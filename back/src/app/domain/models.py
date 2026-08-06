from typing import Optional, List

from pydantic import BaseModel, Field
from sqlalchemy import Integer, Text, DECIMAL
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.testing.schema import mapped_column
from pgvector.sqlalchemy import Vector


class ChatRequest(BaseModel):
    prompt: str = Field(..., description="The main text prompt for the model.")
    model: Optional[str] = Field("gemini-3.5-flash", description="Target GenAI model identifier to use.")
    system: Optional[str] = Field(None, description="System message to define the model's behavior/role.")
    temperature: Optional[float] = Field(None, description="Controls response creativity. Higher means more random.")
    top_p: Optional[float] = Field(None, description="Nucleus sampling limit. 1.0 means consider all tokens.")
    top_k: Optional[int] = Field(None, description="Top-k sampling. Limits choices to top K tokens.")
    num_predict: Optional[int] = Field(None, description="Max tokens to generate in the response.")
    repeat_penalty: Optional[float] = Field(None, description="Applies penalty to repeated tokens.")
    stream: bool = Field(False, description="Whether to stream response tokens back dynamically.")
    context: Optional[List[int]] = Field(None, description="Conversation context tokens from previous turns for memory.")
    previous_interaction_id: Optional[str] = Field(None, description="Interaction context ID from previous turns")


class Base(DeclarativeBase):
    """Base"""


class Movie():
    pass


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
                embedding VECTOR({EMBEDDING_DIM})
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
