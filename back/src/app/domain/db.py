from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import DATABASE_URL

# define the engine
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True
)

# session
SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_db():
    """
    Yield one async db session for request-scoped dependency injections
    :return: Session
    """
    async with SessionLocal() as session:
        yield session
