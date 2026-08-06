from typing import Protocol

import httpx

from app.core.config import HUGGING_FACE_API_KEY, HUGGING_FACE_API_URL


class EmbeddingClient(Protocol):
    async def embed_text(self, text: str) -> list[float]:
        """Return a normalized embedding vector for a single text input."""


class HuggingFaceEmbeddingClient:
    def __init__(
        self,
        api_key: str = HUGGING_FACE_API_KEY,
        api_url: str = HUGGING_FACE_API_URL,
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout

    async def embed_text(self, text: str) -> list[float]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.api_url, headers=headers, json={"inputs": text})
            resp.raise_for_status()
            embedding = resp.json()

        if embedding and isinstance(embedding[0], list):
            embedding = embedding[0]

        return [float(value) for value in embedding]
