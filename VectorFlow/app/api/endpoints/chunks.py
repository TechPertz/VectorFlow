from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.core.deps import get_db
from app.db.database import VectorDatabase
from app.models import Chunk, ChunkCreate

router = APIRouter()

@router.post("/{library_id}/documents/{document_id}/chunks", status_code=status.HTTP_201_CREATED, response_model=Chunk)
async def create_chunk(
    library_id: UUID, 
    document_id: UUID, 
    chunk: ChunkCreate, 
    db: VectorDatabase = Depends(get_db)
):
    """
    Add a new chunk to a document.
    """
    try:
        new_chunk = Chunk(**chunk.model_dump())
        return await db.add_chunk(library_id, document_id, new_chunk)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{library_id}/documents/{document_id}/chunks/{chunk_id}", status_code=status.HTTP_200_OK)
async def delete_chunk(
    library_id: UUID, 
    document_id: UUID, 
    chunk_id: UUID, 
    db: VectorDatabase = Depends(get_db)
):
    """
    Delete a chunk from a document.
    """
    try:
        await db.delete_chunk(library_id, document_id, chunk_id)
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) 