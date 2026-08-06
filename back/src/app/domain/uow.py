from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.domain.repositories import SqlMoviesRepository


class UnitOfWork():
    """Class in responsibility of holding the repositories"""
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        # init repos

    async def __aenter__(self):
        self._session = self._session_factory()
        # init repos
        self.movies = SqlMoviesRepository(self._session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            await self._session.rollback()
        else:
            await self._session.commit()
        await self._session.close()
