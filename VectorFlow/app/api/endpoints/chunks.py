from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List

from app.core.deps import get_db
from app.db.database import VectorDatabase
from app.models import Chunk, ChunkCreate, BatchTextInput, ChunkMetadata
from app.services.embeddings import generate_cohere_embeddings

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

@router.post("/{library_id}/batch-chunks", status_code=status.HTTP_201_CREATED, response_model=List[Chunk])
async def create_batch_chunks_with_embeddings(
    library_id: UUID,
    batch_input: BatchTextInput,
    db: VectorDatabase = Depends(get_db)
):
    """
    Process a batch of texts, generate embeddings using Cohere API, and add them as chunks.
    """
    try:
        # Generate embeddings with Cohere
        embeddings = await generate_cohere_embeddings(batch_input.texts)
        
        # Create and add chunks
        added_chunks = []
        for i, (text, embedding) in enumerate(zip(batch_input.texts, embeddings)):
            # Create a new chunk
            chunk = Chunk(
                text=text,
                embedding=embedding,
                metadata=batch_input.metadata[i] if i < len(batch_input.metadata) else ChunkMetadata(name=f"chunk_{i}")
            )
            
            # Add the chunk to the database
            added_chunk = await db.add_chunk(library_id, batch_input.document_id, chunk)
            added_chunks.append(added_chunk)
            
        return added_chunks
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}") 