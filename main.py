from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI(title="Gemma API", description="Proxy to local Gemma 2 2b via Ollama")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma2:2b"


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str


class ChatPayload(BaseModel):
    model: str
    prompt: str
    stream: bool


@app.get("/")
def root():
    return {"status": "ok", "model": MODEL}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    async with httpx.AsyncClient(timeout=120) as client:
        # payload = {"model": MODEL, "prompt": req.prompt, "stream": False}
        payload = ChatPayload(model=MODEL, prompt=req.prompt, stream=False)
        resp = await client.post(OLLAMA_URL, json=payload.model_dump())
        resp.raise_for_status()
        data = resp.json()
        return ChatResponse(response=data["response"])
