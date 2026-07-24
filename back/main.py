from contextlib import asynccontextmanager
from src.config import *
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from google import genai
import json
import os
import psycopg
from pgvector.psycopg import register_vector_async
from seed import seed_dataset
from src.seed import get_similar_embeddings, DATABASE_URL


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Runs idempotent database population check on server startup
    try:
        await seed_dataset()
    except Exception as e:
        print(f"⚠️ Seeding check notice: {e}")

    # 2. Establish persistent DB connection for RAG vector queries
    conn = None
    try:
        conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
        await register_vector_async(conn)
        app.state.db_conn = conn
        print("Connected to PostgreSQL pgvector database.")
        yield
    finally:
        if conn:
            await conn.close()
            print("Database connection closed.")


app = FastAPI(
    title="Gemma RAG",
    description="RAG service for TMDB 5000 Movies with Google GenAI & PostgreSQL Vector",
    lifespan=lifespan
)


# Enable CORS for external/cross-origin frontends if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Determine web assets directory path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.abspath(os.path.join(BASE_DIR, "../web"))


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
    previous_interaction_id: Optional[str] = Field(None, description="Interaction context ID from previous turns")


@app.get("/info")
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
        "available_models": available_models[:10], # top 10 models sample
        "api_docs": "/docs"
    }


@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    """RAG-enabled chat using pgvector similarity search & google.genai SDK."""
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
                        model="gemini-3.5-flash",
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
                    model="gemini-3.5-flash",
                    input=rag_prompt,
                    previous_interaction_id=req.previous_interaction_id
                )
                # Returns interaction.output_text along with interaction.id and retrieved context
                return {
                    "interaction_id": interaction.id,
                    "response": interaction.output_text,
                    "retrieved_movies": [m["title"] for m in similar_movies]
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemma API request failed: {str(e)}")


# Serve Frontend Static Assets
@app.get("/")
async def serve_index():
    index_path = os.path.join(WEB_DIR, "index.html")
    if not os.path.exists(index_path):
        return {"error": "index.html not found. Make sure the web folder is populated."}
    return FileResponse(index_path)


@app.get("/style.css")
async def serve_css():
    css_path = os.path.join(WEB_DIR, "style.css")
    if not os.path.exists(css_path):
        raise HTTPException(status_code=404, detail="style.css not found")
    return FileResponse(css_path)


@app.get("/app.js")
async def serve_js():
    js_path = os.path.join(WEB_DIR, "app.js")
    if not os.path.exists(js_path):
        raise HTTPException(status_code=404, detail="app.js not found")
    return FileResponse(js_path)
