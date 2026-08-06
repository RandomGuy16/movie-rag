from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from pgvector.psycopg import register_vector_async

from app.domain.db import SessionLocal, engine
from app.domain.uow import UnitOfWork
from app.domain.embeddings import HuggingFaceEmbeddingClient
from app.seed import seed_dataset, DATABASE_URL
from app.domain.services import RAGService, StaticFileService
from app.core.config import GEMINI_API_KEY, WEB_DIR
from app.core.logger import logger
from app.api.routes import router


def uow_factory() -> UnitOfWork:
    return UnitOfWork(SessionLocal)


@asynccontextmanager
async def lifespan(app_: FastAPI):
    # 1. Runs idempotent database population check on server startup
    try:
        await seed_dataset()
    except Exception as e:
        print(f"⚠️ Seeding check notice: {e}")

    # 2. Establish persistent DB connection for RAG vector queries
    conn = None

    # idk why this line, maybe just a test
    async with engine.begin() as conn:
        await conn.run_sync(lambda _: None)

    try:
        conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
        async with conn.cursor() as cur:
            await cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await conn.commit()
        await register_vector_async(conn)
        app_.state.db_conn = conn

        # Attach static file service to app state so routes can depend on it
        app_.state.static_service = StaticFileService(WEB_DIR)
        app_.state.rag_service = RAGService(
            uow_factory=uow_factory,
            embedding_client=HuggingFaceEmbeddingClient(),
            gemini_api_key=GEMINI_API_KEY,
        )
        print("Connected to PostgreSQL pgvector database and RAGService + StaticFileService initialized.")
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
app.include_router(router)

# Enable CORS for external/cross-origin frontends if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
