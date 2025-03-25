from pydantic import BaseModel
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
    id: UUID = uuid4()

class DocumentMetadata(BaseModel):
    title: str
    author: str

class DocumentBase(BaseModel):
    metadata: DocumentMetadata

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: UUID = uuid4()
    chunks: List[Chunk] = []

class LibraryMetadata(BaseModel):
    description: str

class LibraryBase(BaseModel):
    name: str
    metadata: LibraryMetadata

class LibraryCreate(LibraryBase):
    pass

class Library(LibraryBase):
    id: UUID = uuid4()
    documents: List[Document] = []
    index: Optional[Any] = None

class BatchTextInput(BaseModel):
    texts: List[str]
    metadata: List[ChunkMetadata]
    document_id: UUID 