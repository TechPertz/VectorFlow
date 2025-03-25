from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Optional, Any

class ChunkMetadata(BaseModel):
    name: str
    created_at: datetime = datetime.now()

class ChunkBase(BaseModel):
    text: str
    embedding: List[float]
    metadata: ChunkMetadata

class ChunkCreate(ChunkBase):
    pass

class Chunk(ChunkBase):
    id: UUID = Field(default_factory=uuid4)

class DocumentMetadata(BaseModel):
    title: str
    author: str

class DocumentBase(BaseModel):
    metadata: DocumentMetadata

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: UUID = Field(default_factory=uuid4)
    chunks: List[Chunk] = []

class LibraryMetadata(BaseModel):
    description: str

class LibraryBase(BaseModel):
    name: str
    metadata: LibraryMetadata

class LibraryCreate(LibraryBase):
    pass

class Library(LibraryBase):
    id: UUID = Field(default_factory=uuid4)
    documents: List[Document] = []
    index: Optional[Any] = None

class LibraryResponse(LibraryBase):
    """Model for API responses without the non-serializable index field"""
    id: UUID
    documents: List[Document] = []

class ChunkSummary(BaseModel):
    """Summary info for a chunk without embedding data"""
    id: UUID
    text: str
    metadata: ChunkMetadata

class DocumentSummary(BaseModel):
    """Summary info for a document without full chunk data"""
    id: UUID
    metadata: DocumentMetadata
    chunk_count: int = 0

class LibrarySummary(LibraryBase):
    """Summary info for a library without detailed document/chunk data"""
    id: UUID
    document_count: int = 0

class BatchTextInput(BaseModel):
    texts: List[str]
    metadata: List[ChunkMetadata]
    document_id: UUID 