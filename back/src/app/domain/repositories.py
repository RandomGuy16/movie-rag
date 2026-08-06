from typing import Protocol
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import ORMMovie


class MoviesRepository(Protocol):
    """Protocol for movies repository."""
    async def get_by_similarity_embedding(self, embedding: list, limit: int = 3) -> list[dict]:
        """Retrieves top N movies closest in vector similarity to the given embedding using pgvector cosine distance."""
        ...


class SqlMoviesRepository(MoviesRepository):
    """Repository for retrieving movies by vector similarity using SQLAlchemy."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_similarity_embedding(self, embedding: list, limit: int = 3) -> list[dict]:
        """Retrieves top N movies closest in vector similarity to the given embedding using pgvector cosine distance."""
        similarity = 1 - (ORMMovie.embedding.cosine_distance(embedding))
        
        query = (
            select(
                ORMMovie.id,
                ORMMovie.title,
                ORMMovie.overview,
                ORMMovie.tagline,
                ORMMovie.genres,
                ORMMovie.keywords,
                ORMMovie.vote_average,
                ORMMovie.release_date,
                similarity.label("similarity")
            )
            .order_by(ORMMovie.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "title": r[1],
                "overview": r[2],
                "tagline": r[3],
                "genres": r[4],
                "keywords": r[5],
                "vote_average": float(r[6]) if r[6] else None,
                "release_date": r[7],
                "similarity": float(r[8])
            })
        return results
