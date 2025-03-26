# VectorFlow Database

This directory contains VectorFlow's in-memory database implementation. The database manages libraries, documents, and vector chunks while maintaining the structured hierarchy and providing concurrent access.

## Database Architecture

VectorFlow uses an in-memory database that:

1. Maintains the hierarchical data structure (Library → Document → Chunk)
2. Provides thread-safe concurrent access with async/await patterns
3. Manages vector indexes alongside the data structure
4. Handles CRUD operations at all levels of the hierarchy

## Core Components

### VectorDatabase

The primary database class that stores and manages all data in memory.

#### Storage Structure

```
VectorDatabase
  └── libraries: Dict[UUID, Library]
       └── documents: List[Document]
            └── chunks: List[Chunk]
  └── locks: Dict[UUID, asyncio.Lock]
```

#### Concurrency Model

- Uses asyncio locks for thread-safe operations
- Library-level locking granularity (one lock per library)
- All database operations are implemented as async methods
- Prevents race conditions when modifying library contents or indexes

## Key Operations

### Library Operations

| Method | Description | Time Complexity |
|--------|-------------|-----------------|
| `create_library(library)` | Add a new library to the database | O(1) |
| `get_library(library_id)` | Retrieve a library by its ID | O(1) |
| `delete_library(library_id)` | Remove a library and its contents | O(1) |
| `get_all_libraries()` | Retrieve all libraries | O(n) |

### Document Operations

| Method | Description | Time Complexity |
|--------|-------------|-----------------|
| `add_document(library_id, document)` | Add a document to a library | O(1) |
| `delete_document(library_id, document_id)` | Delete a document from a library | O(d), where d is number of documents |
| `get_all_documents(library_id)` | Retrieve all documents in a library | O(1) |

### Chunk Operations

| Method | Description | Time Complexity |
|--------|-------------|-----------------|
| `add_chunk(library_id, document_id, chunk)` | Add a chunk to a document | O(d), where d is document count |
| `delete_chunk(library_id, document_id, chunk_id)` | Delete a chunk from a document | O(d×c), where c is chunk count |
| `get_document_chunks(library_id, document_id)` | Retrieve all chunks in a document | O(d) |

### Index Management

The database also handles index operations:

- Maintaining indexes during add/delete operations
- Gracefully handling index failures
- Marking indexes for rebuild when necessary

## Synchronization with Indexes

When modifying data, the database:

1. Updates the in-memory data structure first
2. Attempts to update associated indexes incrementally
3. If index update fails, marks the index as invalid
4. Provides mechanisms to check if indexes need rebuilding

## Error Handling

The database implements robust error handling:

- Validates existence of libraries, documents, and chunks
- Raises specific ValueError exceptions with clear messages
- Handles index update failures gracefully
- Provides atomic operations with locking

## Usage Example

```python
# Initialize database
db = VectorDatabase()

# Create a library
library = Library(name="Research Data", metadata=LibraryMetadata(description="Science papers"))
lib = await db.create_library(library)

# Add a document
document = Document(metadata=DocumentMetadata(title="AI Research", author="Smith"))
await db.add_document(lib.id, document)

# Add a chunk with vector embedding
chunk = Chunk(
    text="Deep learning has transformed machine learning...",
    embedding=[0.1, 0.2, 0.3, ...],
    metadata=ChunkMetadata(name="intro")
)
await db.add_chunk(lib.id, document.id, chunk)

# Query data
all_libraries = await db.get_all_libraries()
library = await db.get_library(lib.id)
document_chunks = await db.get_document_chunks(lib.id, document.id)
```

## Future Enhancements

The current in-memory database design could be extended to:

1. Support persistence to disk (e.g., via JSON serialization)
2. Implement more sophisticated concurrency models (e.g., finer-grained locking)
3. Add transaction support for multi-operation atomic updates
4. Implement query caching for frequently accessed data 