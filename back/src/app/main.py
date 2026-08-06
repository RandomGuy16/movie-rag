from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.lifespan import lifespan


# pgvector's SQLAlchemy ``Vector`` type serializes/deserializes at the
# SQLAlchemy layer (bind_processor / result_processor), so no DBAPI-level
# type registration is required - the async engine hands pgvector strings
# to psycopg and back automatically.


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
