from fastapi import FastAPI, HTTPException, status
from uuid import UUID
from .database import VectorDatabase
from .indexes import Indexer
from .models import LibraryCreate, DocumentCreate, ChunkCreate, Library, Document, Chunk
from typing import List

app = FastAPI()
db = VectorDatabase()

@app.post("/libraries", status_code=status.HTTP_201_CREATED)
async def create_library(library_create: LibraryCreate):
    try:
        library = Library(**library_create.model_dump())
        return await db.create_library(library)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/libraries/{library_id}")
async def get_library(library_id: UUID):
    lib = await db.get_library(library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="Library not found")
    return lib

@app.delete("/libraries/{library_id}")
async def delete_library(library_id: UUID):
    deleted = await db.delete_library(library_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Library not found")
    return {"status": "deleted"}

@app.post("/libraries/{library_id}/documents", status_code=201)
async def create_document(library_id: UUID, document: DocumentCreate):
    try:
        new_doc = Document(**document.dict())
        return await db.add_document(library_id, new_doc)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/libraries/{library_id}/documents/{document_id}")
async def delete_document(library_id: UUID, document_id: UUID):
    await db.delete_document(library_id, document_id)
    return {"status": "deleted"}

@app.post("/libraries/{library_id}/documents/{document_id}/chunks", status_code=201)
async def create_chunk(
    library_id: UUID, 
    document_id: UUID, 
    chunk: ChunkCreate
):
    try:
        new_chunk = Chunk(**chunk.model_dump())
        return await db.add_chunk(library_id, document_id, new_chunk)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/libraries/{library_id}/documents/{document_id}/chunks/{chunk_id}")
async def delete_chunk(library_id: UUID, document_id: UUID, chunk_id: UUID):
    await db.delete_chunk(library_id, document_id, chunk_id)
    return {"status": "deleted"}

@app.post("/libraries/{library_id}/index")
async def build_index(library_id: UUID, algorithm: str = "linear"):
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

@app.post("/libraries/{library_id}/search")
async def vector_search(library_id: UUID, query: List[float], k: int = 5):
    lib = await db.get_library(library_id)
    if not lib or not lib.index:
        raise HTTPException(status_code=400, detail="Library not indexed")
    
    if len(query) != len(lib.index.chunks[0].embedding):
        raise HTTPException(
            status_code=400, 
            detail=f"Query dimension mismatch. Expected {len(lib.index.chunks[0].embedding)}"
        )
    
    return lib.index.query(query, k)