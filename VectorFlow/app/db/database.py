import asyncio
from uuid import UUID
from typing import Dict, Optional, List, Any

from app.models import Library, Document, Chunk
from app.services.indexes import Indexer

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
            if library_id not in self.libraries:
                return None
            deleted_library = self.libraries.pop(library_id, None)
            self.locks.pop(library_id, None)
            return deleted_library

    async def add_document(self, library_id: UUID, document: Document) -> Document:
        """Add a document to a library."""
        async with await self._get_lock(library_id):
            lib = self.libraries.get(library_id)
            if not lib:
                raise ValueError(f"Library with ID {library_id} not found")
            lib.documents.append(document)
            return document

    async def delete_document(self, library_id: UUID, document_id: UUID):
        """Delete a document from a library."""
        async with await self._get_lock(library_id):
            lib = self.libraries.get(library_id)
            if not lib:
                raise ValueError(f"Library with ID {library_id} not found")
            
            doc_to_delete = next((d for d in lib.documents if d.id == document_id), None)
            if not doc_to_delete:
                raise ValueError(f"Document with ID {document_id} not found")
            
            if lib.index and Indexer.is_index_updateable(lib.index):
                chunks_removed = False
                for chunk in doc_to_delete.chunks:
                    try:
                        if lib.index.remove_chunk(chunk.id):
                            chunks_removed = True
                    except Exception as e:
                        print(f"Error removing chunk {chunk.id} from index: {e}")
                        lib.index = None
                        break
                
                if chunks_removed and hasattr(lib.index, 'pending_changes'):
                    lib.index.pending_changes = True
            else:
                lib.index = None
            
            lib.documents = [d for d in lib.documents if d.id != document_id]
            
            return doc_to_delete

    async def add_chunk(self, library_id: UUID, document_id: UUID, chunk: Chunk) -> Chunk:
        """Add a chunk to a document in a library."""
        async with await self._get_lock(library_id):
            lib = self.libraries.get(library_id)
            if not lib:
                raise ValueError(f"Library with ID {library_id} not found")
            
            doc = next((d for d in lib.documents if d.id == document_id), None)
            if not doc:
                raise ValueError(f"Document with ID {document_id} not found")
            
            doc.chunks.append(chunk)
            
            if lib.index and Indexer.is_index_updateable(lib.index):
                try:
                    lib.index.add_chunk(chunk)
                except Exception as e:
                    print(f"Error adding chunk to index: {e}")
                    lib.index = None
            
            return chunk

    async def delete_chunk(self, library_id: UUID, document_id: UUID, chunk_id: UUID):
        """Delete a chunk from a document in a library."""
        async with await self._get_lock(library_id):
            lib = self.libraries.get(library_id)
            if not lib:
                raise ValueError(f"Library with ID {library_id} not found")
            
            doc = next((d for d in lib.documents if d.id == document_id), None)
            if not doc:
                raise ValueError(f"Document with ID {document_id} not found")
            
            chunk_id_str = str(chunk_id)
            before_len = len(doc.chunks)
            
            chunk_to_delete = next((c for c in doc.chunks if str(c.id) == chunk_id_str), None)
            if not chunk_to_delete:
                raise ValueError(f"Chunk with ID {chunk_id_str} not found in document {document_id}")
            
            if lib.index and Indexer.is_index_updateable(lib.index):
                try:
                    chunk_removed = lib.index.remove_chunk(chunk_id)
                    print(f"Chunk {chunk_id} removed from index: {chunk_removed}")
                except Exception as e:
                    print(f"Error removing chunk from index: {e}")

                    lib.index = None
            else:
                lib.index = None
            
            doc.chunks = [c for c in doc.chunks if str(c.id) != chunk_id_str]
            after_len = len(doc.chunks)
            
            if before_len == after_len:
                raise ValueError(f"Failed to delete chunk {chunk_id_str}: chunk count didn't change")
            
            return chunk_to_delete

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

    async def get_all_libraries(self) -> List[Library]:
        """
        Retrieve all libraries in the database.
        """
        return list(self.libraries.values())

    async def get_all_documents(self, library_id: UUID) -> List[Document]:
        """
        Retrieve all documents in a specific library.
        """
        lib = self.libraries.get(library_id)
        if not lib:
            raise ValueError(f"Library with ID {library_id} not found")
        
        return lib.documents

    async def get_index_status(self, library_id: UUID) -> Dict[str, Any]:
        """
        Get the current status of a library's index
        
        Returns a dictionary with:
        - status: "none", "current", or "needs_rebuild"
        - algorithm: The current indexing algorithm or None
        - stats: Additional statistics about the index
        """
        lib = self.libraries.get(library_id)
        if not lib:
            raise ValueError(f"Library with ID {library_id} not found")
            
        if not lib.index:
            return {
                "status": "none",
                "algorithm": None,
                "stats": {
                    "chunk_count": sum(len(doc.chunks) for doc in lib.documents)
                }
            }
            
        algorithm = None
        if hasattr(lib.index, '__class__'):
            algorithm = lib.index.__class__.__name__.replace('Index', '').lower()
            
        needs_rebuild = False
        pending_changes = False
        
        if hasattr(lib.index, 'pending_changes'):
            pending_changes = lib.index.pending_changes
            
        if hasattr(lib.index, 'check_rebuild_needed'):
            needs_rebuild = lib.index.check_rebuild_needed()
            
        stats = {
            "chunk_count": sum(len(doc.chunks) for doc in lib.documents)
        }
        
        if hasattr(lib.index, 'added_chunks'):
            stats["buffered_chunks"] = len(lib.index.added_chunks)
            
        if hasattr(lib.index, 'deleted_chunks'):
            stats["deleted_chunks"] = len(lib.index.deleted_chunks)
            
        return {
            "status": "needs_rebuild" if needs_rebuild else "modified" if pending_changes else "current",
            "algorithm": algorithm,
            "stats": stats
        } 