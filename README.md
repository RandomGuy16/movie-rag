# movie-rag

RAG playground over the TMDB 5000 movies dataset. Asks Gemini, retrieves similar titles
from PostgreSQL + pgvector, and answers. Vanilla-JS frontend included.

## Stack

- FastAPI + Uvicorn
- PostgreSQL 16 with the [pgvector](https://github.com/pgvector/pgvector) extension
- Google GenAI SDK (Gemini for generation)
- Hugging Face Inference API (sentence embeddings, `all-MiniLM-L6-v2`, 384 dims)
- SQLAlchemy 2.0 async + pgvector column type

## Layout

```
back/
├── pyproject.toml
├── Dockerfile
├── raw/                    # gitignored; populated by `make fetch`
├── web/                    # static frontend (served by FastAPI)
└── src/app/
    ├── main.py             # FastAPI app + CORS
    ├── core/               # config, logger, lifespan
    ├── api/                # routes, deps, schemas
    ├── domain/             # models, repositories, uow, services
    ├── infra/              # db, embeddings, web (static file service)
    └── scripts/            # fetch_dataset, seed
```

## Setup

```bash
# 1. Install deps
make sync

# 2. Get the TMDB 5000 dataset, if you have a kaggle api/token:
#    - ~/.kaggle/access_token file (new single-token API)
#    - KAGGLE_API_TOKEN env var
#    - ~/.kaggle/kaggle.json (legacy username + key)
#    → https://www.kaggle.com/settings/account
make fetch
# or simply download it yourself, place the file at
# back/raw/tmdb_5000_movies.csv

# 3. Put your keys in back/.env:
#    GEMINI_API_KEY=...
#    HUGGING_FACE_API_KEY=hf_...
#    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gemma_rag
```

## Running

```bash
make run        # start pgvector and run uvicorn with reload on :8000
# or:
make docker-dev # full stack (db + api) in docker
```

The lifespan hook auto-seeds the DB on first run (idempotent: skips if `movies` is populated).
To force a re-seed from scratch: `make db-prune && make seed`.

Open `http://localhost:8000` for the chat UI, or `/docs` for the OpenAPI spec.

## Frontend

The web UI lives at `back/web/` and is served by FastAPI itself (no separate static server).
You can pick the model from a dropdown (populated from `/info`), use a custom model name, set
temperature, system prompt, and stream. The "Request payload" expander shows the JSON body
that gets sent to `POST /chat`.

## Endpoints

| Method | Path        | Notes                                                   |
|--------|-------------|---------------------------------------------------------|
| GET    | `/info`     | runtime config + available Gemini models                |
| POST   | `/chat`     | RAG query; supports `stream: true` for NDJSON responses |
| GET    | `/`         | static frontend (`index.html`)                          |
| GET    | `/docs`     | Swagger UI                                              |

## Deploy notes

- `docker-compose.yml` ships with `postgres:postgres` defaults for local dev. Override
  `POSTGRES_USER` / `POSTGRES_PASSWORD` (and the matching `DATABASE_URL`) before deploying
  anywhere reachable.
- The API service uses `host.docker.internal` to reach a local Ollama (`OLLAMA_HOST` env var).
  Change this accordingly.
- pgvector assumes the `vector` extension is available; the lifespan hook creates it if not.
