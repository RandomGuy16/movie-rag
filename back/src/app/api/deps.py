from fastapi import Request

from app.domain.services import RAGService, StaticFileService


def get_rag_service(request: Request) -> RAGService:
    return request.app.state.rag_service


def get_static_service(request: Request) -> StaticFileService:
    return request.app.state.static_service