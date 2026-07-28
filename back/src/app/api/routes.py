import json

from fastapi import APIRouter, Depends, status, HTTPException
from google import genai
from starlette.requests import Request
from starlette.responses import StreamingResponse
from fastapi.responses import FileResponse

from app.api.deps import get_rag_service
from app.core.config import GEMINI_API_KEY
from app.domain.models import ChatRequest
from app.domain.services import RAGService
from app.seed import get_similar_embeddings

router = APIRouter(prefix="/", tags=["info"])


@router.get("/info")
async def get_info():
    """Returns runtime configuration and verifies connectivity to the Google GenAI API."""
    genai_status = "unknown"
    available_models = []

    try:
        with genai.Client(api_key=GEMINI_API_KEY) as client:
            # Query models available in Google GenAI API
            models_page = client.models.list()
            available_models = [m.name for m in models_page]
            genai_status = "connected"
    except Exception as e:
        genai_status = f"unreachable or authentication error: {str(e)}"

    return {
        "status": "ok",
        "backend_sdk": "google-genai",
        "genai_status": genai_status,
        "default_model": "gemini-3.5-flash",
        "available_models": available_models[:10],  # top 10 models sample
        "api_docs": "/docs"
    }


@router.post("/chat")
async def chat(req: ChatRequest, rag_service: RAGService = Depends(get_rag_service)):
    """RAG-enabled chat using pgvector similarity search & google.genai SDK."""
    # Selected model (defaults to gemini-3.5-flash if unspecified)
    selected_model = req.model if req.model else "gemini-3.5-flash"

    # 1. Fetch top N relevant movie context from PostgreSQL pgvector
    db_conn = request.app.state.db_conn
    similar_movies = await get_similar_embeddings(db_conn, query_text=req.prompt, limit=3)

    # 2. Build augmented RAG prompt string
    context_text = "\n\n".join([
        f"Title: {m['title']}\nTagline: {m['tagline']}\nGenres: {m['genres']}\nOverview: {m['overview']}"
        for m in similar_movies
    ])

    rag_prompt = f"""You are a movie expert assistant. Use the retrieved TMDB movie information below to answer the user request.

Retrieved Movie Context:
----------------------------------
{context_text}
----------------------------------

User Request: {req.prompt}"""

    if req.stream:
        # Define streaming generator to yield GenAI interaction output chunks as NDJSON
        async def event_generator():
            try:
                with genai.Client(api_key=GEMINI_API_KEY) as client:
                    stream = client.interactions.create(
                        model=selected_model,
                        input=rag_prompt,
                        stream=True,
                        previous_interaction_id=req.previous_interaction_id
                    )
                    for event in stream:
                        interaction_id = None
                        if hasattr(event, 'interaction') and event.interaction:
                            interaction_id = getattr(event.interaction, 'id', None)

                        delta_text = None
                        if hasattr(event, 'delta') and event.delta and hasattr(event.delta, 'text'):
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

        return StreamingResponse(event_generator(), media_type="application/x-ndjson")

    else:
        # Synchronous GenAI Interaction request
        try:
            with genai.Client(api_key=GEMINI_API_KEY) as client:
                interaction = client.interactions.create(
                    model=selected_model,
                    input=rag_prompt,
                    previous_interaction_id=req.previous_interaction_id
                )
                # Returns interaction.output_text along with interaction.id and retrieved context
                return {
                    "interaction_id": interaction.id,
                    "model": selected_model,
                    "response": interaction.output_text,
                    "retrieved_movies": [m["title"] for m in similar_movies]
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemma API request failed: {str(e)}")


# Serve Frontend Static Assets
@router.get("/")
async def serve_index():
    try:
        return FileResponse(index_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"index.html not found.: {str(e)}")


@router.get("/style.css")
async def serve_css():
    css_path = os.path.join(WEB_DIR, "style.css")
    if not os.path.exists(css_path):
        raise HTTPException(status_code=404, detail="style.css not found")
    return FileResponse(css_path)


@router.get("/app.js")
async def serve_js():
    js_path = os.path.join(WEB_DIR, "app.js")
    if not os.path.exists(js_path):
        raise HTTPException(status_code=404, detail="app.js not found")
    return FileResponse(js_path)
