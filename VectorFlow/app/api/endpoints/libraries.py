from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from uuid import UUID

from app.core.deps import get_db
from app.db.database import VectorDatabase
from app.models import Library, LibraryCreate
from app.services import Indexer
from app.services.indexes import LinearIndex, KDTreeIndex, LSHIndex
from app.services.embeddings import generate_cohere_embeddings

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Library)
async def create_library(library_create: LibraryCreate, db: VectorDatabase = Depends(get_db)):
    """
    Create a new library.
    """
    try:
        library = Library(**library_create.model_dump())
        return await db.create_library(library)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{library_id}", response_model=Library)
async def get_library(library_id: UUID, db: VectorDatabase = Depends(get_db)):
    """
    Retrieve a library by its ID.
    """
    lib = await db.get_library(library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="Library not found")
    return lib

@router.delete("/{library_id}", status_code=status.HTTP_200_OK)
async def delete_library(library_id: UUID, db: VectorDatabase = Depends(get_db)):
    """
    Delete a library by its ID.
    """
    deleted = await db.delete_library(library_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Library not found")
    return {"status": "deleted"}

@router.post("/{library_id}/index", status_code=status.HTTP_200_OK)
async def build_index(library_id: UUID, algorithm: str = "linear", db: VectorDatabase = Depends(get_db)):
    """
    Build an index for the library's documents.
    """
    lib = await db.get_library(library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="Library not found")
    
    try:
        chunks = [c for doc in lib.documents for c in doc.chunks]
        index = Indexer.create_index(chunks, algorithm)
        lib.index = index
        return {"message": f"{algorithm} index built successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{library_id}/search", status_code=status.HTTP_200_OK)
async def vector_search(
    library_id: UUID, 
    query: List[float], 
    k: int = 5, 
    db: VectorDatabase = Depends(get_db)
):
    """
    Search for similar documents in the library using a vector query.
    """
    lib = await db.get_library(library_id)
    if not lib or not lib.index:
        raise HTTPException(status_code=400, detail="Library not indexed")
    
    # Get the first chunk's embedding dimension based on index type
    if isinstance(lib.index, LinearIndex):
        # For LinearIndex, chunks are directly accessible
        embedding_dim = len(lib.index.chunks[0].embedding)
    elif isinstance(lib.index, KDTreeIndex):
        # For KDTreeIndex, get embedding from the root node
        embedding_dim = len(lib.index.root.chunk.embedding)
    elif isinstance(lib.index, LSHIndex):
        # For LSHIndex, get dimension from hyperplanes
        if not lib.index.hyperplanes:
            raise HTTPException(
                status_code=400,
                detail="LSH index has no hyperplanes"
            )
        embedding_dim = len(lib.index.hyperplanes[0])
    else:
        # Handle any other index types that might be added in the future
        raise HTTPException(
            status_code=400,
            detail="Unsupported index type"
        )
        
    if len(query) != embedding_dim:
        raise HTTPException(
            status_code=400, 
            detail=f"Query dimension mismatch. Expected {embedding_dim}"
        )
    
    return lib.index.query(query, k)

@router.post("/{library_id}/text-search", status_code=status.HTTP_200_OK)
async def text_search(
    library_id: UUID,
    text_query: Dict[str, str],
    k: int = 5,
    db: VectorDatabase = Depends(get_db)
):
    """
    Search for similar documents in the library using a text query.
    The text is converted to an embedding using Cohere API.
    
    Example request body:
    {"text": "What are transformer models?"}
    """
    # Validate input
    if "text" not in text_query:
        raise HTTPException(status_code=400, detail="Request body must contain a 'text' field")
    
    query_text = text_query["text"]
    if not query_text or not isinstance(query_text, str):
        raise HTTPException(status_code=400, detail="Text query must be a non-empty string")
    
    # Get the library
    lib = await db.get_library(library_id)
    if not lib or not lib.index:
        raise HTTPException(status_code=400, detail="Library not indexed")
    
    try:
        # Generate embedding for the query text using Cohere
        embeddings = await generate_cohere_embeddings([query_text])
        
        # Use the generated embedding to perform the search
        query_embedding = embeddings[0]
        
        # Return the search results
        results = lib.index.query(query_embedding, k)
        
        # Extract relevant fields for the response to ensure proper serialization
        serialized_results = []
        for chunk in results:
            serialized_results.append({
                "id": str(chunk.id),
                "text": chunk.text,
                "metadata": chunk.metadata.dict()
            })
        
        # Add the original query text to the response for reference
        return {
            "query_text": query_text,
            "results_count": len(results),
            "results": serialized_results
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing text search: {str(e)}"
        ) 