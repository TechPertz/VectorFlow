import asyncio
from uuid import UUID
from typing import Dict, Optional, List

from app.models import Library, Document, Chunk

class VectorDatabase:
    def __init__(self):
        self.libraries: Dict[UUID, Library] = {}
        self.locks: Dict[UUID, asyncio.Lock] = {}
    
    async def _get_lock(self, library_id: UUID):
        if library_id not in self.locks:
            self.locks[library_id] = asyncio.Lock()
        return self.locks[library_id]

    async def create_library(self, library: Library) -> Library:
        """Create a new library."""
        async with await self._get_lock(library.id):
            self.libraries[library.id] = library
            return library

    async def get_library(self, library_id: UUID) -> Optional[Library]:
        """Retrieve a library by its ID."""
        return self.libraries.get(library_id)

    async def delete_library(self, library_id: UUID):
        """Delete a library by its ID."""
        async with await self._get_lock(library_id):
            return self.libraries.pop(library_id, None)

    async def add_document(self, library_id: UUID, document: Document) -> Document:
        """Add a document to a library."""
        async with await self._get_lock(library_id):
            lib = self.libraries.get(library_id)
            if not lib:
                raise ValueError("Library not found")
            lib.documents.append(document)
            return document

    async def delete_document(self, library_id: UUID, document_id: UUID):
        """Delete a document from a library."""
        async with await self._get_lock(library_id):
            lib = self.libraries.get(library_id)
            if not lib:
                raise ValueError("Library not found")
            lib.documents = [d for d in lib.documents if d.id != document_id]

    async def add_chunk(self, library_id: UUID, document_id: UUID, chunk: Chunk) -> Chunk:
        """Add a chunk to a document in a library."""
        async with await self._get_lock(library_id):
            lib = self.libraries.get(library_id)
            if not lib:
                raise ValueError("Library not found")
            doc = next((d for d in lib.documents if d.id == document_id), None)
            if not doc:
                raise ValueError("Document not found")
            doc.chunks.append(chunk)
            return chunk

    async def delete_chunk(self, library_id: UUID, document_id: UUID, chunk_id: UUID):
        """Delete a chunk from a document in a library."""
        async with await self._get_lock(library_id):
            lib = self.libraries.get(library_id)
            if not lib:
                raise ValueError("Library not found")
            doc = next((d for d in lib.documents if d.id == document_id), None)
            if doc:
                doc.chunks = [c for c in doc.chunks if c.id != chunk_id]

    async def get_document_chunks(self, library_id: UUID, document_id: UUID) -> List[Chunk]:
        """
        Retrieve all chunks associated with a specific document.
        
        Args:
            library_id: The ID of the library
            document_id: The ID of the document
            
        Returns:
            A list of Chunk objects
            
        Raises:
            ValueError: If the library or document doesn't exist
        """
        lib = self.libraries.get(library_id)
        if not lib:
            raise ValueError(f"Library with ID {library_id} not found")
        
        doc = next((d for d in lib.documents if d.id == document_id), None)
        if not doc:
            raise ValueError(f"Document with ID {document_id} not found in library {library_id}")
        
        return doc.chunks 