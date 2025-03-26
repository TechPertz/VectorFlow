# VectorFlow API Documentation

This directory contains the API endpoints for the VectorFlow application, which provides vector search capabilities for document libraries.

## API Structure

The API is organized into three main categories:

- **Libraries**: Management of vector libraries
- **Documents**: Management of documents within libraries
- **Chunks**: Management of text chunks (with embeddings) within documents

## Endpoints

### Libraries

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/libraries/` | GET | Retrieve all libraries with summary information |
| `/libraries/` | POST | Create a new library |
| `/libraries/{library_id}` | GET | Retrieve a library by its ID |
| `/libraries/{library_id}` | DELETE | Delete a library and all its documents and chunks |
| `/libraries/{library_id}/index` | POST | Build or update a vector index for a library |
| `/libraries/{library_id}/index` | GET | Get the status of a library's index |
| `/libraries/{library_id}/search` | POST | Search for similar documents using a vector query |
| `/libraries/{library_id}/text-search` | POST | Search for documents using a text query |

### Documents

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/libraries/{library_id}/documents` | GET | Retrieve all documents in a library |
| `/libraries/{library_id}/documents` | POST | Add a new document to a library |
| `/libraries/{library_id}/documents/{document_id}` | DELETE | Delete a document from a library |

### Chunks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/libraries/{library_id}/documents/{document_id}/chunks` | GET | Retrieve all chunks belonging to a document |
| `/libraries/{library_id}/documents/{document_id}/chunks` | POST | Add a new chunk to a document |
| `/libraries/{library_id}/documents/{document_id}/chunks/{chunk_id}` | DELETE | Delete a chunk from a document |
| `/libraries/{library_id}/batch-chunks` | POST | Process a batch of texts, generate embeddings, and add them as chunks |

## Key Features

- **Vector Search**: Search for similar documents/chunks using vector embeddings
- **Text-to-Vector Search**: Convert text queries to vectors automatically
- **Multiple Index Types**: Support for linear, KD-tree, and LSH indexing algorithms
- **Incremental Updates**: Some indexes support incremental updates without full rebuilds
- **Batch Processing**: Efficient batch processing of text with automatic embedding generation
- **Metadata Filtering**: Filter search results using document/chunk metadata

## Usage Example

To search for similar documents:

```
POST /libraries/{library_id}/search

{
  "query": [0.1, 0.2, ...],  // Vector embedding
  "metadata_filter": {       // Optional filters
    "category": "finance",
    "date_after": "2023-01-01"
  }
}
``` 