from fastapi import APIRouter

from app.api.endpoints import libraries, documents, chunks

api_router = APIRouter()

api_router.include_router(libraries.router, prefix="/libraries", tags=["libraries"])
api_router.include_router(documents.router, prefix="/libraries", tags=["documents"])
api_router.include_router(chunks.router, prefix="/libraries", tags=["chunks"]) 