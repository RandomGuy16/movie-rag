from contextlib import asynccontextmanager
from app.core.config import *
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from google import genai
import json
import os
import psycopg
from pgvector.psycopg import register_vector_async

from app.domain.models import ChatRequest
from app.seed import seed_dataset, get_similar_embeddings, DATABASE_URL


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
        async with conn.cursor() as cur:
            await cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await conn.commit()
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
WEB_DIR = os.path.abspath(os.path.join(BASE_DIR, "web"))

