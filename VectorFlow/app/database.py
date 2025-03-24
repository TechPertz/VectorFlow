import asyncio
from uuid import UUID
from typing import Dict, Optional
from .models import Library, Document, Chunk

class VectorDatabase:
    def __init__(self):
        self.libraries: Dict[UUID, Library] = {}
        self.locks: Dict[UUID, asyncio.Lock] = {}
    
    async def _get_lock(self, library_id: UUID):
        if library_id not in self.locks:
            self.locks[library_id] = asyncio.Lock()
        return self.locks[library_id]

    # LIBRARY OPERATIONS
    async def create_library(self, library: Library) -> Library:
        async with await self._get_lock(library.id):
            self.libraries[library.id] = library
            return library

    async def get_library(self, library_id: UUID) -> Optional[Library]:
        return self.libraries.get(library_id)

    async def delete_library(self, library_id: UUID):
        async with await self._get_lock(library_id):
            return self.libraries.pop(library_id, None)

    # DOCUMENT OPERATIONS
    async def add_document(self, library_id: UUID, document: Document) -> Document:
        async with await self._get_lock(library_id):
            lib = self.libraries[library_id]
            lib.documents.append(document)
            return document

    async def delete_document(self, library_id: UUID, document_id: UUID):
        async with await self._get_lock(library_id):
            lib = self.libraries[library_id]
            lib.documents = [d for d in lib.documents if d.id != document_id]

    # CHUNK OPERATIONS
    async def add_chunk(self, library_id: UUID, document_id: UUID, chunk: Chunk) -> Chunk:
        async with await self._get_lock(library_id):
            lib = self.libraries[library_id]
            doc = next((d for d in lib.documents if d.id == document_id), None)
            if not doc:
                raise ValueError("Document not found")
            doc.chunks.append(chunk)
            return chunk

    async def delete_chunk(self, library_id: UUID, document_id: UUID, chunk_id: UUID):
        async with await self._get_lock(library_id):
            lib = self.libraries[library_id]
            doc = next((d for d in lib.documents if d.id == document_id), None)
            if doc:
                doc.chunks = [c for c in doc.chunks if c.id != chunk_id]