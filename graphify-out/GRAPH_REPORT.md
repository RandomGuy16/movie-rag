# Graph Report - .  (2026-08-06)

## Corpus Check
- Corpus is ~4,210 words - fits in a single context window. You may not need a graph.

## Summary
- 171 nodes · 211 edges · 22 communities (19 shown, 3 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 28 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Frontend Web App (JS)
- Domain Models & Repositories
- API Routes & Dependencies
- RAG Service & Chat Route
- DB Seeding & Embeddings
- Frontend HTML & Docker Stack
- Embedding Clients (HuggingFace)
- Graphify Workflow Docs
- Logging Infrastructure
- Config & DB URL
- Dataset Fetching Script
- DB Connection Layer
- Package Init (gemma_rag)
- Package Init (root)

## God Nodes (most connected - your core abstractions)
1. `RAGService` - 14 edges
2. `StaticFileService` - 11 edges
3. `UnitOfWork` - 9 edges
4. `SqlMoviesRepository` - 8 edges
5. `HuggingFaceEmbeddingClient` - 8 edges
6. `ChatRequest` - 7 edges
7. `lifespan()` - 7 edges
8. `EmbeddingClient` - 7 edges
9. `Graphify Knowledge Graph Workflow` - 7 edges
10. `MoviesRepository` - 6 edges

## Surprising Connections (you probably didn't know these)
- `connection status indicator` --semantically_similar_to--> `db service (pgvector/pgvector:pg16)`  [INFERRED] [semantically similar]
  back/web/index.html → docker-compose.yml
- `Request payload preview` --semantically_similar_to--> `graphify explain command`  [INFERRED] [semantically similar]
  back/web/index.html → AGENTS.md
- `TMDB retrieval-augmented answering` --conceptually_related_to--> `db service (pgvector/pgvector:pg16)`  [INFERRED]
  back/web/index.html → docker-compose.yml
- `api service (FastAPI backend + static web frontend)` --shares_data_with--> `app.js frontend controller`  [INFERRED]
  docker-compose.yml → back/web/index.html
- `lifespan()` --calls--> `RAGService`  [INFERRED]
  back/src/app/core/lifespan.py → back/src/app/domain/services.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Movie RAG runtime stack (vector DB, API, LLM providers, frontend)** — docker_compose_db_service, docker_compose_api_service, docker_compose_ollama_host, docker_compose_gemini_api_key, back_web_index_app_js [INFERRED 0.85]
- **Graphify scoped-context command family** — agents_graphify_query, agents_graphify_path, agents_graphify_explain, agents_graphify_update, agents_graph_report [EXTRACTED 1.00]
- **Chat turn flow: prompt to payload to transcript with memory** — back_web_index_chat_form, back_web_index_settings_panel, back_web_index_payload_preview, back_web_index_messages, back_web_index_memory_indicator [INFERRED 0.85]

## Communities (22 total, 3 thin omitted)

### Community 0 - "Frontend Web App (JS)"
Cohesion: 0.10
Nodes (26): addMessage(), addSystemMessage(), availableModels, btnClearMem, btnSend, chatForm, checkBackendInfo(), getPayload() (+18 more)

### Community 1 - "Domain Models & Repositories"
Cohesion: 0.09
Nodes (17): async_sessionmaker, Base, ORMMovie, CREATE TABLE IF NOT EXISTS movies ( id INT PRIMARY KEY, title TEXT NOT NULL,…, Declarative base for ORM models., MoviesRepository, AsyncSession, Protocol (+9 more)

### Community 2 - "API Routes & Dependencies"
Cohesion: 0.13
Nodes (14): get_rag_service(), get_static_service(), get_info(), Returns runtime configuration and verifies connectivity to the Google GenAI API., serve_css(), serve_index(), serve_js(), lifespan() (+6 more)

### Community 3 - "RAG Service & Chat Route"
Cohesion: 0.21
Nodes (10): chat(), RAG-enabled chat using pgvector similarity search & google.genai SDK. Delegates…, ChatRequest, _build_rag_system_prompt(), RAGService, Service responsible for performing retrieval-augmented generation calls.…, Synchronous (non-streaming) GenAI interaction returning full response., Returns a synchronous generator that yields NDJSON chunks for… (+2 more)

### Community 4 - "DB Seeding & Embeddings"
Cohesion: 0.24
Nodes (11): AsyncConnection, generate_embeddings_batch(), get_existing_count(), get_similar_embeddings(), init_db(), Read dataset, idempotency-check, embed, and load into PostgreSQL asynchronously., Ensure vector extension and target schema table exist., Retrieves top N movies closest in vector similarity to query_text using… (+3 more)

### Community 5 - "Frontend HTML & Docker Stack"
Cohesion: 0.23
Nodes (12): app.js frontend controller, chat-form / user-prompt input, memory indicator and Clear memory button, messages transcript region, TMDB retrieval-augmented answering, connection status indicator, api service (FastAPI backend + static web frontend), DATABASE_URL configuration (+4 more)

### Community 6 - "Embedding Clients (HuggingFace)"
Cohesion: 0.22
Nodes (6): EmbeddingClient, HuggingFaceEmbeddingClient, Protocol, Interface (Protocol) for embedding providers. Python's ``typing.Protocol`` is…, Return a normalized embedding vector for a single text input., Hugging Face Inference API implementation of :class:`EmbeddingClient`.

### Community 7 - "Graphify Workflow Docs"
Cohesion: 0.27
Nodes (10): Dirty Graph Files Policy, GRAPH_REPORT.md, graphify explain command, graphify path command, graphify query command, graphify update command, graphify-out/wiki/index.md, Graphify Knowledge Graph Workflow (+2 more)

### Community 8 - "Logging Infrastructure"
Cohesion: 0.28
Nodes (6): configure_logging(), ContextFormatter, get_logger(), Append structured context from ``extra`` fields to log messages. When…, Logger, LogRecord

### Community 9 - "Config & DB URL"
Cohesion: 0.29
Nodes (6): find_project_root(), _normalize_db_url(), Walk up until we find pyproject.toml, Build an async-friendly SQLAlchemy URL from an arbitrary .env value. Accepts…, Path, URL

### Community 10 - "Dataset Fetching Script"
Cohesion: 0.50
Nodes (4): detect_credentials(), fetch_dataset(), Return a description of the auth source, or None if no credentials are found.…, Download the TMDB 5000 movies CSV from Kaggle into back/raw/.

## Knowledge Gaps
- **23 isolated node(s):** `gemma-rag`, `availableModels`, `statusDot`, `statusText`, `memoryIndicator` (+18 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RAGService` connect `RAG Service & Chat Route` to `Domain Models & Repositories`, `API Routes & Dependencies`, `Embedding Clients (HuggingFace)`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `UnitOfWork` connect `Domain Models & Repositories` to `API Routes & Dependencies`, `RAG Service & Chat Route`, `Embedding Clients (HuggingFace)`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Why does `lifespan()` connect `API Routes & Dependencies` to `RAG Service & Chat Route`, `DB Seeding & Embeddings`, `Embedding Clients (HuggingFace)`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `RAGService` (e.g. with `lifespan()` and `ChatRequest`) actually correct?**
  _`RAGService` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `UnitOfWork` (e.g. with `RAGService` and `SqlMoviesRepository`) actually correct?**
  _`UnitOfWork` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `SqlMoviesRepository` (e.g. with `ORMMovie` and `UnitOfWork`) actually correct?**
  _`SqlMoviesRepository` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `HuggingFaceEmbeddingClient` (e.g. with `lifespan()` and `RAGService`) actually correct?**
  _`HuggingFaceEmbeddingClient` has 3 INFERRED edges - model-reasoned connections that need verification._