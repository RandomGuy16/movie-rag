import json
from typing import Iterator, Callable

from google import genai

from app.api.schemas import ChatRequest
from app.core.config import GEMINI_API_KEY
from app.domain.uow import UnitOfWork
from app.infra.embeddings import EmbeddingClient, HuggingFaceEmbeddingClient


def _build_rag_system_prompt(similar_movies: list) -> str:
    context_text = "\n\n".join([
        f"The movie '{m['title']}' is a {m['genres']} film. {m['tagline']} "
        f"Here is the overview: {m['overview']} "
        f"Some key themes and keywords associated with this movie are: {m['keywords']}."
        for m in similar_movies
    ])

    return (
        "You are a movie expert assistant. Use the retrieved TMDB movie information "
        "below to answer the user request.\n\n"
        "Retrieved Movie Context:\n"
        "----------------------------------\n"
        f"{context_text}\n"
        "----------------------------------\n\n"
    )


class RAGService:
    """Service responsible for performing retrieval-augmented generation calls.

    Responsibilities:
    - Fetch similar documents from pgvector via an embedding client + repository
    - Build the RAG prompt
    - Execute synchronous or streaming GenAI interactions

    The FastAPI dependency should construct this with a live DB connection (see app.api.deps).
    """

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        embedding_client: EmbeddingClient | None = None,
        gemini_api_key: str = GEMINI_API_KEY,
        default_model: str = "gemini-3.5-flash",
    ):
        self.uow_factory = uow_factory
        self.embedding_client = embedding_client or HuggingFaceEmbeddingClient()
        self.gemini_api_key = gemini_api_key
        self.default_model = default_model

    async def _fetch_similar(self, prompt: str, limit: int = 3):
        query_embedding = await self.embedding_client.embed_text(prompt)

        async with self.uow_factory() as uow:
            return await uow.movies.get_by_similarity_embedding(query_embedding, limit=limit)

    def _selected_model(self, req: ChatRequest) -> str:
        return req.model if req.model else self.default_model

    async def query_model(self, req: ChatRequest) -> dict:
        """Synchronous (non-streaming) GenAI interaction returning full response."""
        selected_model = self._selected_model(req)
        similar_movies = await self._fetch_similar(req.prompt, limit=3)
        system_prompt = _build_rag_system_prompt(similar_movies)

        try:
            with genai.Client(api_key=self.gemini_api_key) as client:
                interaction = client.interactions.create(
                    model=selected_model,
                    input=req.prompt,
                    previous_interaction_id=req.previous_interaction_id,
                    system_instruction=system_prompt,
                )
                return {
                    "interaction_id": getattr(interaction, "id", None),
                    "model": selected_model,
                    "response": getattr(interaction, "output_text", None),
                    "retrieved_movies": [m["title"] for m in similar_movies],
                }

        except Exception as e:
            # Let caller handle HTTP translation; raise for visibility in logs/tests
            raise RuntimeError(f"Gemma API request failed: {e}")

    async def query_model_stream(self, req: ChatRequest) -> Iterator[str]:
        """Returns a synchronous generator that yields NDJSON chunks for StreamingResponse.

        Note: fetching similar docs is async, but the GenAI client stream is synchronous, so
        the async function awaits retrieval then returns a sync generator.
        """
        selected_model = self._selected_model(req)
        similar_movies = await self._fetch_similar(req.prompt, limit=3)
        rag_prompt = _build_rag_system_prompt(similar_movies)

        def _event_generator() -> Iterator[str]:
            try:
                with genai.Client(api_key=self.gemini_api_key) as client:
                    stream = client.interactions.create(
                        model=selected_model,
                        input=rag_prompt,
                        stream=True,
                        previous_interaction_id=req.previous_interaction_id,
                    )

                    for event in stream:
                        interaction_id = None
                        if hasattr(event, "interaction") and event.interaction:
                            interaction_id = getattr(event.interaction, "id", None)

                        delta_text = None
                        if hasattr(event, "delta") and event.delta and hasattr(event.delta, "text"):
                            delta_text = event.delta.text

                        if delta_text or interaction_id:
                            chunk_payload = {}
                            if delta_text:
                                chunk_payload["response"] = delta_text
                            if interaction_id:
                                chunk_payload["interaction_id"] = interaction_id
                            yield f"{json.dumps(chunk_payload)}\n"
            except Exception as e:
                yield f"{{\"error\": \"Streaming failed: {str(e)}\"}}\n"

        return _event_generator()
