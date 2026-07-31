from fastapi import APIRouter, Depends, HTTPException
from google import genai
from starlette.responses import StreamingResponse
from fastapi.responses import FileResponse

from app.api.deps import get_rag_service, get_static_service
from app.core.config import GEMINI_API_KEY
from app.domain.models import ChatRequest
from app.domain.services import RAGService, StaticFileService

router = APIRouter(prefix="", tags=["info"])


@router.get("/info")
async def get_info():
    """Returns runtime configuration and verifies connectivity to the Google GenAI API."""
    genai_status = "unknown"
    available_models = []

    try:
        with genai.Client(api_key=GEMINI_API_KEY) as client:
            # Query models available in Google GenAI API
            models_page = client.models.list()
            available_models = [m.name for m in models_page]
            genai_status = "connected"
    except Exception as e:
        genai_status = f"unreachable or authentication error: {str(e)}"

    return {
        "status": "ok",
        "backend_sdk": "google-genai",
        "genai_status": genai_status,
        "default_model": "gemini-3.5-flash",
        "available_models": available_models[:10],  # top 10 models sample
        "api_docs": "/docs"
    }


@router.post("/chat")
async def chat(req: ChatRequest, rag_service: RAGService = Depends(get_rag_service)):
    """RAG-enabled chat using pgvector similarity search & google.genai SDK.

    Delegates retrieval and model interaction to RAGService. Streaming requests return an NDJSON
    streaming response; non-streaming return the full interaction payload.
    """
    try:
        if req.stream:
            gen = await rag_service.query_model_stream(req)
            return StreamingResponse(gen, media_type="application/x-ndjson")
        else:
            result = await rag_service.query_model(req)
            return result
    except RuntimeError as e:
        # Errors raised by the service are translated to 500 responses here
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


# Serve Frontend Static Assets
@router.get("/")
async def serve_index(static_service: StaticFileService = Depends(get_static_service)):
    try:
        index_path = static_service.serve_index()
        return FileResponse(index_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/style.css")
async def serve_css(static_service: StaticFileService = Depends(get_static_service)):
    try:
        css_path = static_service.serve_css()
        return FileResponse(css_path)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/app.js")
async def serve_js(static_service: StaticFileService = Depends(get_static_service)):
    try:
        js_path = static_service.serve_js()
        return FileResponse(js_path)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
