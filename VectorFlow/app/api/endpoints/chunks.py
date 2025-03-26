from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List

from app.core.deps import get_db
from app.db.database import VectorDatabase
from app.models import Chunk, ChunkCreate, BatchTextInput, ChunkMetadata
from app.services.embeddings import generate_cohere_embeddings
from app.services.indexes import Indexer

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
        
        # Check the library to determine if we need to show index warnings
        lib = await db.get_library(library_id)
        
        response = {
            "status": "deleted", 
            "message": f"Chunk {chunk_id} has been deleted"
        }
        
        if not lib.index:
            response["warning"] = "The library index has been reset. You must rebuild the index before performing searches."
        elif hasattr(lib.index, 'pending_changes') and lib.index.pending_changes:
            if hasattr(lib.index, 'check_rebuild_needed') and lib.index.check_rebuild_needed():
                response["warning"] = "The index may need rebuilding due to significant changes. Searches will automatically rebuild if needed."
            else:
                response["info"] = "The index has been updated incrementally. You can perform searches without rebuilding."
                
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

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
        embeddings = await generate_cohere_embeddings(batch_input.texts)
        
        added_chunks = []
        for i, (text, embedding) in enumerate(zip(batch_input.texts, embeddings)):
            chunk = Chunk(
                text=text,
                embedding=embedding,
                metadata=batch_input.metadata[i] if i < len(batch_input.metadata) else ChunkMetadata(name=f"chunk_{i}")
            )
            
            added_chunk = await db.add_chunk(library_id, batch_input.document_id, chunk)
            added_chunks.append(added_chunk)
            
        return added_chunks
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

@router.get("/{library_id}/documents/{document_id}/chunks", status_code=status.HTTP_200_OK, response_model=List[Chunk])
async def get_document_chunks(
    library_id: UUID, 
    document_id: UUID, 
    db: VectorDatabase = Depends(get_db)
):
    """
    Retrieve all chunks belonging to a specific document.
    """
    try:
        chunks = await db.get_document_chunks(library_id, document_id)
        return chunks
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chunks: {str(e)}") 