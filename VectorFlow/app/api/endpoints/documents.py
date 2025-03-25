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
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) 