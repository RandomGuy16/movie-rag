import os
import sys
import csv
import asyncio
from pathlib import Path
import psycopg
from pgvector.psycopg import register_vector_async
import httpx
import dotenv
from app.core.config import DOTENV_PATH, PROJECT_ROOT

# Load environment variables
if os.path.exists(DOTENV_PATH):
    dotenv.load_dotenv(DOTENV_PATH)
else:
    dotenv.load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/gemma_rag")
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{EMBEDDING_MODEL}/pipeline/feature-extraction"

# Find dataset file
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = PROJECT_ROOT / "raw/tmdb_5000_movies.csv"


async def init_db(conn):
    """Ensure vector extension and target schema table exist."""
    async with conn.cursor() as cur:
        await cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await cur.execute(f"""
            CREATE TABLE IF NOT EXISTS movies (
                id INT PRIMARY KEY,
                title TEXT NOT NULL,
                overview TEXT,
                genres TEXT,
                keywords TEXT,
                tagline TEXT,
                vote_average FLOAT,
                release_date TEXT,
                embedding VECTOR({EMBEDDING_DIM})
            );
        """)
    await conn.commit()


async def get_similar_embeddings(conn: psycopg.AsyncConnection, query_text: str, limit: int = 3) -> list[dict]:
    """Retrieves top N movies closest in vector similarity to query_text using pgvector cosine distance."""
    headers = {"Authorization": f"Bearer {HUGGING_FACE_API_KEY}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(HF_API_URL, headers=headers, json={"inputs": query_text})
        resp.raise_for_status()
        query_embedding = resp.json()

    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT id, title, overview, tagline, genres, vote_average, release_date,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM movies
            ORDER BY embedding <=> %s::vector ASC
            LIMIT %s;
        """, (query_embedding, query_embedding, limit))
        rows = await cur.fetchall()

    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "title": r[1],
            "overview": r[2],
            "tagline": r[3],
            "genres": r[4],
            "vote_average": r[5],
            "release_date": r[6],
            "similarity": float(r[7])
        })
    return results


async def get_existing_count(conn) -> int:
    """Return current number of indexed movies in table."""
    async with conn.cursor() as cur:
        await cur.execute("SELECT COUNT(*) FROM movies;")
        row = await cur.fetchone()
        return row[0] if row else 0


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generates embedding vectors for a batch of text strings via Hugging Face Inference API."""
    headers = {"Authorization": f"Bearer {HUGGING_FACE_API_KEY}"}
    resp = httpx.post(HF_API_URL, headers=headers, json={"inputs": texts}, timeout=60.0)
    resp.raise_for_status()
    return resp.json()



async def seed_dataset():
    """Reads dataset, checks for existing data, embeds, and loads into PostgreSQL asynchronously."""
    print("Connecting to database...")
    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        await register_vector_async(conn)
        await init_db(conn)
        
        # Idempotency Check
        count = await get_existing_count(conn)
        if count > 0:
            print(f"✅ Database is already populated with {count} movies. Skipping seeding.")
            return

        resolved_dataset_path = DATASET_PATH.resolve()
        if not resolved_dataset_path.exists():
            print(f"❌ Error: Dataset file not found at {resolved_dataset_path}")
            sys.exit(1)

        print(f"Reading movies dataset from {resolved_dataset_path}...")
        movies_to_insert = []
        
        with open(resolved_dataset_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                movie_id = int(row["id"])
                title = row.get("title", "").strip()
                overview = row.get("overview", "").strip()
                genres = row.get("genres", "").strip()
                keywords = row.get("keywords", "").strip()
                tagline = row.get("tagline", "").strip()
                
                try:
                    vote_avg = float(row["vote_average"]) if row.get("vote_average") else 0.0
                except ValueError:
                    vote_avg = 0.0
                    
                release_date = row.get("release_date", "").strip()
                
                # Combine fields into rich semantic text snippet for embedding
                text_to_embed = f"The movie '{title}' is a {genres} film. {tagline} Here is the overview: {overview} Some key themes and keywords associated with this movie are: {keywords}."
                
                movies_to_insert.append({
                    "id": movie_id,
                    "title": title,
                    "overview": overview,
                    "genres": genres,
                    "keywords": keywords,
                    "tagline": tagline,
                    "vote_average": vote_avg,
                    "release_date": release_date,
                    "text_to_embed": text_to_embed
                })

        print(f"Total movies parsed: {len(movies_to_insert)}. Generating embeddings via Hugging Face Inference API...")
        batch_size = 32
        inserted_total = 0
        
        for i in range(0, len(movies_to_insert), batch_size):
            batch = movies_to_insert[i : i + batch_size]
            texts = [m["text_to_embed"] for m in batch]
            
            try:
                embeddings = generate_embeddings_batch(texts)
            except Exception as e:
                print(f"⚠️ Error generating embeddings for batch {i}: {e}. Retrying after short pause...")
                await asyncio.sleep(2)
                embeddings = generate_embeddings_batch(texts)

                
            rows = [
                (
                    m["id"],
                    m["title"],
                    m["overview"],
                    m["genres"],
                    m["keywords"],
                    m["tagline"],
                    m["vote_average"],
                    m["release_date"],
                    emb
                )
                for m, emb in zip(batch, embeddings)
            ]
            
            async with conn.cursor() as cur:
                await cur.executemany("""
                    INSERT INTO movies (id, title, overview, genres, keywords, tagline, vote_average, release_date, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, rows)
            await conn.commit()
            
            inserted_total += len(batch)
            print(f"Progress: {inserted_total}/{len(movies_to_insert)} movies indexed...")

        print("Building HNSW vector cosine similarity index...")
        async with conn.cursor() as cur:
            await cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_movies_embedding_hnsw 
                ON movies 
                USING hnsw (embedding vector_cosine_ops);
            """)
        await conn.commit()
        print("🎉 Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_dataset())
