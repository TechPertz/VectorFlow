from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List

from app.core.deps import get_db
from app.db.database import VectorDatabase
from app.models import Document, DocumentCreate, DocumentSummary

router = APIRouter()

@router.get("/{library_id}/documents", response_model=List[DocumentSummary])
async def get_all_documents(
    library_id: UUID, 
    db: VectorDatabase = Depends(get_db)
):
    """
    Retrieve all documents in a library with summary information.
    """
    try:
        documents = await db.get_all_documents(library_id)
        return [
            DocumentSummary(
                id=doc.id,
                metadata=doc.metadata,
                chunk_count=len(doc.chunks)
            )
            for doc in documents
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{library_id}/documents", status_code=status.HTTP_201_CREATED, response_model=Document)
async def create_document(
    library_id: UUID, 
    document: DocumentCreate, 
    db: VectorDatabase = Depends(get_db)
):
    """
    Add a new document to a library.
    """
    try:
        new_doc = Document(**document.model_dump())
        return await db.add_document(library_id, new_doc)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{library_id}/documents/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    library_id: UUID, 
    document_id: UUID, 
    db: VectorDatabase = Depends(get_db)
):
    """
    Delete a document from a library.
    """
    try:
        await db.delete_document(library_id, document_id)
        
        # Check the library to determine if we need to show index warnings
        lib = await db.get_library(library_id)
        
        response = {
            "status": "deleted", 
            "message": f"Document {document_id} and all its chunks have been deleted"
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