from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import GEMINI_API_KEY, WEB_DIR
from app.core.logger import logger
from app.domain.db import SessionLocal, engine
from app.domain.embeddings import HuggingFaceEmbeddingClient
from app.domain.services import RAGService, StaticFileService
from app.domain.uow import UnitOfWork
from app.api.routes import router
from app.seed import seed_dataset


# pgvector's SQLAlchemy ``Vector`` type serializes/deserializes at the
# SQLAlchemy layer (bind_processor / result_processor), so no DBAPI-level
# type registration is required - the async engine hands pgvector strings
# to psycopg and back automatically.


def uow_factory() -> UnitOfWork:
    return UnitOfWork(SessionLocal)


@asynccontextmanager
async def lifespan(app_: FastAPI):
    # 1. Idempotent dataset population check on server startup.
    try:
        await seed_dataset()
    except Exception as e:
        logger.warning("Seeding check notice: %s", e)

    # 2. Ensure the pgvector extension exists. ``engine.begin()`` opens a
    #    transaction that commits on successful exit, so the DDL is
    #    durable before the app starts serving requests.
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("pgvector extension verified.")
    except Exception as exc:
        logger.error("Failed to initialize pgvector extension: %s", exc)
        raise

    # 3. Wire up request-scoped services. Both services are stateless
    #    apart from their construction parameters and are safe to share
    #    across concurrent requests.
    app_.state.static_service = StaticFileService(WEB_DIR)
    app_.state.rag_service = RAGService(
        uow_factory=uow_factory,
        embedding_client=HuggingFaceEmbeddingClient(),
        gemini_api_key=GEMINI_API_KEY,
    )
    logger.info("RAGService + StaticFileService initialized.")

    try:
        yield
    finally:
        await engine.dispose()
        logger.info("Database engine disposed.")


app = FastAPI(
    title="Gemma RAG",
    description="RAG service for TMDB 5000 Movies with Google GenAI & PostgreSQL Vector",
    lifespan=lifespan,
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