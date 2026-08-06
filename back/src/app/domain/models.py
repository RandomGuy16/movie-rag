from sqlalchemy import Integer, Text, DECIMAL
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.testing.schema import mapped_column
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    """Declarative base for ORM models."""


class ORMMovie(Base):
    """
    CREATE TABLE IF NOT EXISTS movies (
                id INT PRIMARY KEY,
                title TEXT NOT NULL,
                overview TEXT,
                genres TEXT,
                keywords TEXT,
                tagline TEXT,
                vote_average FLOAT,
                release_date TEXT,
                embedding VECTOR(384)
    """
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    overview: Mapped[str] = mapped_column(Text)
    genres: Mapped[str] = mapped_column(Text)
    keywords: Mapped[str] = mapped_column(Text)
    tagline: Mapped[str] = mapped_column(Text)
    vote_average: Mapped[float] = mapped_column(DECIMAL)
    release_date: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(Vector(384))
