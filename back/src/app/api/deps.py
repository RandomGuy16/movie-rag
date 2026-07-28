# app/api/deps.py
from fastapi import Request
from psycopg import AsyncConnection

from app.domain.services import RAGService


def get_rag_service(request: Request) -> RAGService:
    return request.app.state.rag_service

def get_db_conn(request: Request) -> AsyncConnection:
    return request.app.state.db_conn
