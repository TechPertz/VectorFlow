from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

class ChunkMetadata(BaseModel):
    name: str
    created_at: datetime

class ChunkCreate(BaseModel):
    text: str
    embedding: List[float]
    metadata: ChunkMetadata

class Chunk(ChunkCreate):
    id: UUID

class DocumentMetadata(BaseModel):
    title: str
    author: str

class DocumentCreate(BaseModel):
    metadata: DocumentMetadata

class Document(DocumentCreate):
    id: UUID
    chunks: List[Chunk] = []

class LibraryMetadata(BaseModel):
    description: str

class LibraryCreate(BaseModel):
    name: str
    metadata: LibraryMetadata

class Library(LibraryCreate):
    id: UUID
    documents: List[Document] = []