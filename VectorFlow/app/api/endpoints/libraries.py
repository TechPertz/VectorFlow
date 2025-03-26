from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.core.deps import get_db
from app.db.database import VectorDatabase
from app.models import Library, LibraryCreate, LibraryResponse, LibrarySummary
from app.services import Indexer
from app.services.indexes import LinearIndex, KDTreeIndex, LSHIndex
from app.services.embeddings import generate_cohere_embeddings

router = APIRouter()

@router.get("/", response_model=List[LibrarySummary])
async def get_all_libraries(db: VectorDatabase = Depends(get_db)):
    """
    Retrieve all libraries with summary information.
    """
    libraries = await db.get_all_libraries()
    return [
        LibrarySummary(
            id=lib.id,
            name=lib.name,
            metadata=lib.metadata,
            document_count=len(lib.documents)
        )
        for lib in libraries
    ]

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

@router.get("/{library_id}", response_model=LibrarySummary)
async def get_library(library_id: UUID, db: VectorDatabase = Depends(get_db)):
    """
    Retrieve a library by its ID with summary information.
    """
    lib = await db.get_library(library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="Library not found")
    return LibrarySummary(
        id=lib.id,
        name=lib.name,
        metadata=lib.metadata,
        document_count=len(lib.documents)
    )

@router.delete("/{library_id}", status_code=status.HTTP_200_OK)
async def delete_library(library_id: UUID, db: VectorDatabase = Depends(get_db)):
    """
    Delete a library by its ID.
    """
    deleted = await db.delete_library(library_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Library not found")
    return {"status": "deleted", "message": f"Library {library_id} and all its documents and chunks have been deleted"}

@router.post("/{library_id}/index", status_code=status.HTTP_200_OK)
async def build_index(
    library_id: UUID, 
    algorithm: str = "linear", 
    force: bool = Query(False, description="Force rebuild even if incremental updates are available"),
    db: VectorDatabase = Depends(get_db)
):
    """
    Build an index for the library's documents.
    
    - algorithm: Type of index to build (linear, kd_tree, lsh)
    - force: If true, always rebuilds the entire index, ignoring incremental options
    """
    lib = await db.get_library(library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="Library not found")
    
    try:

        current_algorithm = None
        if lib.index:
            if isinstance(lib.index, LinearIndex):
                current_algorithm = "linear"
            elif isinstance(lib.index, KDTreeIndex):
                current_algorithm = "kd_tree"
            elif isinstance(lib.index, LSHIndex):
                current_algorithm = "lsh"
        
        is_updateable = lib.index and Indexer.is_index_updateable(lib.index)
        algorithm_changed = current_algorithm and current_algorithm != algorithm
        
        if is_updateable and not algorithm_changed and not force:

            if hasattr(lib.index, 'check_rebuild_needed') and lib.index.check_rebuild_needed():
                print(f"Performing full rebuild of {current_algorithm} index due to high change ratio")
                chunks = [c for doc in lib.documents for c in doc.chunks]
                if hasattr(lib.index, 'rebuild_if_needed'):
                    lib.index.rebuild_if_needed(chunks)
                else:

                    lib.index = Indexer.create_index(chunks, algorithm)
                    
                return {"message": f"{algorithm} index rebuilt successfully"}
            

            if hasattr(lib.index, 'pending_changes'):
                lib.index.pending_changes = False
                
            return {"message": f"{current_algorithm} index updated incrementally"}
        

        chunks = [c for doc in lib.documents for c in doc.chunks]
        index = Indexer.create_index(chunks, algorithm)
        lib.index = index
        return {"message": f"{algorithm} index built successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{library_id}/index", status_code=status.HTTP_200_OK)
async def get_index_status(library_id: UUID, db: VectorDatabase = Depends(get_db)):
    """
    Get the status of a library's index.
    """
    try:
        status = await db.get_index_status(library_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{library_id}/search", status_code=status.HTTP_200_OK)
async def vector_search(
    library_id: UUID, 
    query: List[float], 
    k: int = 5, 
    rebuild_if_needed: bool = Query(False, description="Rebuild the index if it needs rebuilding"),
    db: VectorDatabase = Depends(get_db)
):
    """
    Search for similar documents in the library using a vector query.
    """
    lib = await db.get_library(library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="Library not found")
        
    if not lib.index:
        raise HTTPException(
            status_code=400, 
            detail="Library not indexed. Please build an index first."
        )
    

    needs_rebuild = False
    if hasattr(lib.index, 'check_rebuild_needed'):
        needs_rebuild = lib.index.check_rebuild_needed()
    

    if needs_rebuild and rebuild_if_needed:
        try:
            algorithm = "linear"
            if isinstance(lib.index, LinearIndex):
                algorithm = "linear"
            elif isinstance(lib.index, KDTreeIndex):
                algorithm = "kd_tree"
            elif isinstance(lib.index, LSHIndex):
                algorithm = "lsh"
                
            chunks = [c for doc in lib.documents for c in doc.chunks]
            index = Indexer.create_index(chunks, algorithm)
            lib.index = index
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error rebuilding index: {str(e)}"
            )
    elif needs_rebuild:
        raise HTTPException(
            status_code=400,
            detail="Index needs rebuilding. Set rebuild_if_needed=true or rebuild manually."
        )
    

    try:
        if isinstance(lib.index, LinearIndex):
            if not lib.index.chunks:
                raise HTTPException(status_code=400, detail="Index has no chunks")
            embedding_dim = len(lib.index.chunks[0].embedding)
        elif isinstance(lib.index, KDTreeIndex):
            if not lib.index.root:
                raise HTTPException(status_code=400, detail="KDTree index has no root")
            embedding_dim = len(lib.index.root.chunk.embedding)
        elif isinstance(lib.index, LSHIndex):
            if not lib.index.hyperplanes:
                raise HTTPException(status_code=400, detail="LSH index has no hyperplanes")
            embedding_dim = len(lib.index.hyperplanes[0])
        else:
            raise HTTPException(status_code=400, detail="Unsupported index type")
            
        if len(query) != embedding_dim:
            raise HTTPException(
                status_code=400, 
                detail=f"Query dimension mismatch. Expected {embedding_dim}"
            )
        
        return lib.index.query(query, k)
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(
                status_code=500, 
                detail=f"Error during vector search: {str(e)}"
            )
        raise e

@router.post("/{library_id}/text-search", status_code=status.HTTP_200_OK)
async def text_search(
    library_id: UUID,
    text_query: Dict[str, str],
    k: int = 5,
    rebuild_if_needed: bool = Query(False, description="Rebuild the index if it needs rebuilding"),
    db: VectorDatabase = Depends(get_db)
):
    """
    Search for similar documents in the library using a text query.
    The text is converted to an embedding using Cohere API.
    """
    if "text" not in text_query:
        raise HTTPException(status_code=400, detail="Request body must contain a 'text' field")
    
    query_text = text_query["text"]
    if not query_text or not isinstance(query_text, str):
        raise HTTPException(status_code=400, detail="Text query must be a non-empty string")
    
    lib = await db.get_library(library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="Library not found")
        
    if not lib.index:
        raise HTTPException(
            status_code=400, 
            detail="Library not indexed. Please build an index first."
        )
    
    needs_rebuild = False
    if hasattr(lib.index, 'check_rebuild_needed'):
        needs_rebuild = lib.index.check_rebuild_needed()
    
    if needs_rebuild and rebuild_if_needed:
        try:
            algorithm = "linear"
            if isinstance(lib.index, LinearIndex):
                algorithm = "linear"
            elif isinstance(lib.index, KDTreeIndex):
                algorithm = "kd_tree"
            elif isinstance(lib.index, LSHIndex):
                algorithm = "lsh"
                
            chunks = [c for doc in lib.documents for c in doc.chunks]
            index = Indexer.create_index(chunks, algorithm)
            lib.index = index
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error rebuilding index: {str(e)}"
            )
    elif needs_rebuild:
        raise HTTPException(
            status_code=400,
            detail="Index needs rebuilding. Set rebuild_if_needed=true or rebuild manually."
        )
    
    try:
        embeddings = await generate_cohere_embeddings([query_text])
        
        query_embedding = embeddings[0]
        
        results = lib.index.query(query_embedding, k)
        
        serialized_results = []
        for chunk in results:
            serialized_results.append({
                "id": str(chunk.id),
                "text": chunk.text,
                "metadata": chunk.metadata.dict()
            })
        
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