# VectorFlow Data Models

This directory contains the data models (schemas) used throughout VectorFlow. The models define the structure of data for libraries, documents, and vector chunks, as well as their relationships.

## Data Hierarchy

VectorFlow organizes vector data in a hierarchical structure:

```
Library
  └── Document
       └── Chunk (with vector embedding)
```

Each level has associated metadata and relationships:

1. **Library** - A collection of related documents
2. **Document** - A container for chunks (e.g., a file, article, or record)
3. **Chunk** - A text fragment with its vector embedding

## Core Models

### Chunk Models

Chunks are the atomic units in VectorFlow that contain actual vector embeddings.

| Model | Description |
|-------|-------------|
| `ChunkBase` | Base model with text content, vector embedding, and metadata |
| `ChunkCreate` | Request model for creating new chunks |
| `Chunk` | Complete chunk model with ID and all properties |
| `ChunkMetadata` | Metadata associated with a chunk (name, creation time) |
| `ChunkSummary` | Lightweight representation without embedding data |

#### Key Fields
- `text`: The text content of the chunk
- `embedding`: Vector representation (List[float])
- `metadata`: Associated metadata (name, timestamps)
- `id`: Unique identifier (UUID)

### Document Models

Documents act as containers for related chunks.

| Model | Description |
|-------|-------------|
| `DocumentBase` | Base model with document metadata |
| `DocumentCreate` | Request model for creating new documents |
| `Document` | Complete document model with ID and associated chunks |
| `DocumentMetadata` | Metadata for a document (title, author) |
| `DocumentSummary` | Lightweight representation with chunk count |

#### Key Fields
- `metadata`: Document metadata (title, author)
- `id`: Unique identifier (UUID)
- `chunks`: List of associated chunks
- `chunk_count`: Number of chunks (in summary model)

### Library Models

Libraries are the top-level containers that organize documents and maintain indexes.

| Model | Description |
|-------|-------------|
| `LibraryBase` | Base model with name and metadata |
| `LibraryCreate` | Request model for creating new libraries |
| `Library` | Complete library model with documents and search index |
| `LibraryMetadata` | Library metadata (description) |
| `LibraryResponse` | API response model without non-serializable index |
| `LibrarySummary` | Lightweight representation with document count |

#### Key Fields
- `name`: Library name
- `metadata`: Library metadata (description)
- `id`: Unique identifier (UUID)
- `documents`: List of documents in the library
- `index`: Vector search index (not serialized in responses)
- `document_count`: Number of documents (in summary model)

## Utility Models

### BatchTextInput

Used for batch processing of texts into embeddings.

#### Key Fields
- `texts`: List of text strings to process
- `metadata`: List of metadata objects for each text
- `document_id`: ID of the document to associate chunks with

## Usage Examples

### Creating a Library with Documents and Chunks

```python
# Create a library
library = Library(
    name="Research Papers",
    metadata=LibraryMetadata(description="AI research papers collection")
)

# Add a document
document = Document(
    metadata=DocumentMetadata(
        title="Vector Databases in Practice",
        author="Jane Smith"
    )
)
library.documents.append(document)

# Add chunks with embeddings
chunk = Chunk(
    text="Vector databases provide efficient similarity search...",
    embedding=[0.1, 0.2, 0.3, ...],  # Vector embedding
    metadata=ChunkMetadata(name="intro_paragraph")
)
document.chunks.append(chunk)
```

### Using Summary Models for API Responses

Summary models are optimized for API responses by excluding heavy data like embeddings:

```python
# Get lightweight library information
library_summary = LibrarySummary(
    id=library.id,
    name=library.name,
    metadata=library.metadata,
    document_count=len(library.documents)
)

# Return summary in API response
return library_summary
```

## Schema Evolution

When extending these models:

1. Add new fields to base models if they apply to all derived models
2. Make new fields optional or provide defaults for backward compatibility
3. Update API documentation when changing models
4. Consider adding new summary models for large additions 