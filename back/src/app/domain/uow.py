


class UnitOfWork():
    """Class in responsibility of holding the repositories"""
    def __init__(self, session_factory):
        self._session_factory = session_factory()
        # init repos

    async def __aenter__(self):
        self._session = self._session_factory()
        # init repo
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            await self._session.rollback()
        else:
            await self._session.commit()
        await self._session.close()
