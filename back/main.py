from src.config import *
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
import httpx

app = FastAPI(
    title="Gemma RAG",
    description="A proxy server to interface with local Gemma 2 2B models via Ollama with configurable generation parameters."
)

# Enable CORS for external/cross-origin frontends if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    prompt: str = Field(..., description="The main text prompt for the model.")
    system: Optional[str] = Field(None, description="System message to define the model's behavior/role.")
    temperature: Optional[float] = Field(None, description="Controls response creativity. Higher means more random.")
    top_p: Optional[float] = Field(None, description="Nucleus sampling limit. 1.0 means consider all tokens.")
    top_k: Optional[int] = Field(None, description="Top-k sampling. Limits choices to top K tokens.")
    num_predict: Optional[int] = Field(None, description="Max tokens to generate in the response.")
    repeat_penalty: Optional[float] = Field(None, description="Applies penalty to repeated tokens.")
    stream: bool = Field(False, description="Whether to stream response tokens back dynamically.")
    context: Optional[List[int]] = Field(None, description="Conversation context tokens from previous turns for memory.")


@app.get("/info")
async def get_info():
    """Returns runtime configuration and verifies connectivity to the local Ollama instance."""
    ollama_status = "unknown"
    available_models = []
    
    # contact the model
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            if resp.status_code == 200:
                ollama_status = "connected"
                data = resp.json()
                # list available models
                available_models = [m["name"] for m in data.get("models", [])]
            else:
                ollama_status = f"error: status code {resp.status_code}"
    except Exception as e:
        ollama_status = f"unreachable: {str(e)}"
        
    return {
        "status": "ok",
        "ollama_host": OLLAMA_HOST,
        "ollama_status": ollama_status,
        "configured_model": MODEL,
        "available_models": available_models,
        "api_docs": "/docs"
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Proxies requests to local Ollama.
    Supports generation parameters configuration and streaming responses.
    """
    # Build options dictionary for Ollama API
    options = {}
    if req.temperature is not None:
        options["temperature"] = req.temperature
    if req.top_p is not None:
        options["top_p"] = req.top_p
    if req.top_k is not None:
        options["top_k"] = req.top_k
    if req.num_predict is not None:
        options["num_predict"] = req.num_predict
    if req.repeat_penalty is not None:
        options["repeat_penalty"] = req.repeat_penalty

    # Construct the payload
    payload = {
        "model": MODEL,
        "prompt": req.prompt,
        "stream": req.stream,
    }
    
    if req.system:
        payload["system"] = req.system
    if req.context:
        payload["context"] = req.context
    if options:
        payload["options"] = options

    if req.stream:
        # Define streaming generator to yield Ollama output chunks
        async def event_generator():
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line:
                                yield f"{line}\n"
            except Exception as e:
                yield f"{{\"error\": \"Streaming failed: {str(e)}\"}}\n"

        return StreamingResponse(event_generator(), media_type="application/x-ndjson")
    
    else:
        # Standard synchronous API request
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(OLLAMA_URL, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Ollama API request failed: {str(e)}")


