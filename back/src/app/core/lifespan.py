from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import GEMINI_API_KEY, WEB_DIR
from app.core.logger import logger
from app.infra.db import SessionLocal, engine
from app.infra.embeddings import HuggingFaceEmbeddingClient
from app.infra.web import StaticFileService
from app.domain.services import RAGService
from app.domain.uow import UnitOfWork
from app.scripts.seed import seed_dataset


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
