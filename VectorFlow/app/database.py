import asyncio
from uuid import UUID, uuid4
from typing import Dict, Optional
from .models import Library, Document, Chunk, LibraryCreate, DocumentCreate, ChunkCreate

class Database:
    def __init__(self):
        self.libraries: Dict[UUID, Library] = {}
        self.locks: Dict[UUID, asyncio.Lock] = {}

    async def create_library(self, library_create: LibraryCreate) -> Library:
        library = Library(
            id=uuid4(),
            **library_create.dict()
        )
        self.libraries[library.id] = library
        self.locks[library.id] = asyncio.Lock()
        return library

    async def get_library(self, library_id: UUID) -> Optional[Library]:
        return self.libraries.get(library_id)

    async def add_document(self, library_id: UUID, document_create: DocumentCreate) -> Document:
        async with self.locks[library_id]:
            library = self.libraries[library_id]
            document = Document(
                id=uuid4(),
                **document_create.dict()
            )
            library.documents.append(document)
            return document

    async def add_chunk(self, library_id: UUID, document_id: UUID, chunk_create: ChunkCreate) -> Chunk:
        async with self.locks[library_id]:
            library = self.libraries[library_id]
            document = next((doc for doc in library.documents if doc.id == document_id), None)
            if not document:
                raise ValueError("Document not found")
            chunk = Chunk(id=uuid4(), **chunk_create.dict())
            document.chunks.append(chunk)
            return chunk