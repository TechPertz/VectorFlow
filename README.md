# VectorFlow

VectorFlow is a powerful vector database and similarity search API built with FastAPI. It provides efficient vector indexing, storage, and retrieval capabilities for developing AI applications that require semantic search.

## Overview

VectorFlow enables you to:
- Store and organize text data in a hierarchical structure (libraries → documents → chunks)
- Generate vector embeddings for text using the Cohere API
- Index vectors using different algorithms optimized for various use cases
- Perform fast similarity searches with optional metadata filtering
- Update your vector database incrementally without full rebuilds

## Installation and Setup

### Prerequisites

- Python 3.11 (recommended, also works with Python 3.9+)
- Docker (for containerization)
- Kubernetes & Minikube (for deployment)
- Cohere API key

### API Key Setup

VectorFlow uses the Cohere API for generating embeddings. You need to set up an API key:

1. Create a `.env` file in the project root:
   ```
   COHERE_API_KEY=your_api_key_here
   ```

2. The application will automatically read this file when running.

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/VectorFlow.git
   cd VectorFlow
   ```

2. Set up a Python virtual environment with Python 3.11 (recommended):
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Make the run script executable (if not already):
   ```bash
   chmod +x run.sh
   chmod +x run/*.sh
   ```

5. Run the application using the provided script:
   ```bash
   ./run.sh
   ```
   
   Or manually with uvicorn:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Access the API documentation at http://localhost:8000/docs

### Kubernetes Deployment with Minikube

1. Start Minikube:
   ```bash
   minikube start
   ```

2. Make the deployment script executable (if not already):
   ```bash
   chmod +x deploy-minikube.sh
   chmod +x run.sh
   chmod +x run/*.sh
   ```

3. Deploy VectorFlow:
   ```bash
   ./deploy-minikube.sh
   ```

4. Access the API:
   ```bash
   minikube service vectorflow --url
   ```

## Interactive CLI Demo

VectorFlow includes a comprehensive interactive CLI demo to help you explore its capabilities. The demo is implemented through a modular collection of shell scripts.

### Running the Demo

```bash
./run.sh
```

The interactive CLI provides two main modes:
- **Guided Demo**: Walks you through a complete example workflow
- **Custom Steps**: Allows you to execute specific operations in any order

### Demo Structure

```
run/
├── main.sh              # Main script coordinating all demo functionality
├── functions/           # Shared utility functions
│   ├── dependencies.sh  # Dependency checks and environment setup
│   └── utils.sh         # Helper functions and formatting utilities
└── steps/               # Individual operation implementations
    ├── create_library.sh    # Create vector libraries
    ├── create_document.sh   # Add documents to libraries
    ├── add_chunks.sh        # Add text chunks with embeddings
    ├── build_index.sh       # Build vector search indexes
    ├── search.sh            # Perform vector similarity searches
    ├── list_operations.sh   # List libraries, documents, and chunks
    ├── set_ids.sh           # Manually set library and document IDs
    └── delete_operations.sh # Delete libraries, documents, and chunks
```

### Available Operations

The demo provides access to all core VectorFlow functionality:

1. **Library Management**
   - Create libraries with metadata
   - List available libraries
   - Delete libraries and their contents

2. **Document Management**
   - Add documents to libraries with metadata
   - List documents in a library
   - Delete documents

3. **Chunk Operations**
   - Add text chunks with automatic embedding generation
   - Delete specific chunks
   - List chunks in a document

4. **Vector Search Capabilities**
   - Build different types of vector indexes (Linear, KD-Tree, LSH)
   - Perform vector similarity searches
   - Text-to-vector searches with automatic embedding generation
   - Apply metadata filters to search results

5. **Administration**
   - View index status and statistics
   - Set library and document IDs manually

### Demo Flow

When you run `./run.sh`, the script first checks dependencies and ensures the API server is running. Then it presents a menu with the following options:

1. **Run Example Demo**: Follows a recommended sequence of operations:
   - Create a library
   - Add a document
   - Add text chunks with embeddings
   - Build a vector index
   - Perform searches

2. **Run Custom Steps**: Opens a menu where you can choose specific operations:
   - Library operations
   - Document operations
   - Chunk operations
   - Index building and searches
   - Listing and deleting operations

The demo provides helpful prompts and colorized output to guide you through the process.

## Architecture

VectorFlow follows a modular architecture with these key components:

### Database (In-Memory)
- Hierarchical data structure with libraries, documents, and chunks
- Thread-safe concurrent access with async/await patterns
- Atomic operations with library-level locking

### Vector Indexing Algorithms
- **Linear Index**: Simple brute force approach (O(n×d) query time)
- **KD-Tree Index**: Space-partitioning for lower dimensions (O(log n) to O(n) query time)
- **LSH Index**: Locality-sensitive hashing for high dimensions (sublinear query time)

### Data Models
- Pydantic schemas for type validation and serialization
- Support for metadata at all levels of the hierarchy
- Summary models optimized for API responses

### API Endpoints
- REST API with FastAPI
- Endpoints for managing libraries, documents, and chunks
- Vector and text search capabilities

## Project Structure

```
VectorFlow/
├── app/                     # Main application package
│   ├── api/                 # API endpoints
│   │   ├── endpoints/       # Individual endpoint modules 
│   │   └── api.py           # API router
│   ├── core/                # Core application components
│   ├── db/                  # Database components
│   ├── models/              # Data models
│   ├── services/            # Business logic services
│   └── main.py              # Application entry point
├── helm/                    # Helm chart for Kubernetes deployment
├── tests/                   # Test directory
└── Dockerfile               # Docker image definition
```

## Technical Deep Dive

### Well-Defined Schemas

VectorFlow uses Pydantic to define a robust schema hierarchy:

#### Core Data Models

```python
# Core entity models with hierarchical relationships
class Chunk(ChunkBase):
    id: UUID = Field(default_factory=uuid4)
    text: str
    embedding: List[float]
    metadata: ChunkMetadata

class Document(DocumentBase):
    id: UUID = Field(default_factory=uuid4)
    metadata: DocumentMetadata  # title, author, etc.
    chunks: List[Chunk] = []

class Library(LibraryBase):
    id: UUID = Field(default_factory=uuid4)
    name: str
    metadata: LibraryMetadata  # description, etc.
    documents: List[Document] = []
    index: Optional[Any] = None  # Vector index
```

#### API Request/Response Models

VectorFlow implements specialized models for API interactions:

- **Create Models** (`LibraryCreate`, `DocumentCreate`, `ChunkCreate`): For validating creation requests
- **Summary Models** (`LibrarySummary`, `DocumentSummary`, `ChunkSummary`): Lightweight representations excluding heavy data like embeddings
- **Response Models** (`LibraryResponse`): Special models for API responses that exclude non-serializable fields

This schema design ensures:
- Type safety throughout the application
- Clear validation rules for API inputs
- Efficient API responses without unnecessary data
- Proper serialization/deserialization

### Indexing Algorithms: Complexity Analysis

VectorFlow implements three indexing strategies, each with different performance characteristics:

#### 1. Linear Index (Brute Force)

```python
class LinearIndex(BaseIndex):
    """Linear index implementation using brute force search"""
```

**Complexities:**
- **Build Time**: O(n) - simply stores vectors in an array
- **Query Time**: O(n × d) - compares query against every vector
- **Space Complexity**: O(n × d) - stores all n vectors with d dimensions
- **Memory Access Pattern**: Sequential, cache-friendly

**Optimizations:**
- Batch processing to leverage CPU cache efficiency
- Normalization of vectors for faster dot product comparisons
- Early termination of dissimilar vectors

**Best For:**
- Small datasets (<10K vectors)
- Situations requiring exact results
- Development/testing environments

#### 2. KD-Tree Index

```python
class KDTreeIndex(BaseIndex):
    """KD-Tree implementation for efficient vector search in lower dimensions"""
```

**Complexities:**
- **Build Time**: O(n log n) - recursive partitioning to build balanced tree
- **Query Time**: 
  - Best case: O(log n) in low dimensions
  - Average case: O(n^(1-1/d)) - degrades with increasing dimensions
  - Worst case: O(n) in high dimensions
- **Space Complexity**: O(n) - only stores references in tree nodes
- **Memory Access Pattern**: Non-sequential, less cache-friendly

**Optimizations:**
- Variance-based split axis selection for better balance
- Optimized quickselect for median finding
- Buffered updates to avoid tree rebalancing

**Best For:**
- Low to medium dimensions (d ≤ 20)
- Data with natural clusters or structure
- Applications needing balance between speed and accuracy

#### 3. Enhanced LSH Index (Locality-Sensitive Hashing)

```python
class LSHIndex(BaseIndex):
    """LSH implementation for efficient vector search in high dimensions"""
```

**Complexities:**
- **Build Time**: O(n × d × L × K) - where L is number of tables, K is hash size
- **Query Time**: O(L + nL/2^K) - often sublinear in practice
- **Space Complexity**: O(n × L) - stores vector references in L tables
- **Memory Access Pattern**: Random access, less cache-friendly

**Optimizations:**
- **Hybrid Approach**: Combines traditional LSH with neighbor exploration
- Adaptive neighbor exploration based on result quality
- Dynamic bucket size monitoring
- Fallback mechanisms for low-recall scenarios

**Best For:**
- High dimensional data (d > 20)
- Very large datasets (>100K vectors)
- Applications where query speed is critical
- Approximate nearest neighbor search

### Concurrency Model & Data Race Prevention

VectorFlow implements a sophisticated concurrency model to ensure thread safety:

```python
class VectorDatabase:
    def __init__(self):
        self.libraries: Dict[UUID, Library] = {}
        self.locks: Dict[UUID, asyncio.Lock] = {}
    
    async def _get_lock(self, library_id: UUID):
        if library_id not in self.locks:
            self.locks[library_id] = asyncio.Lock()
        return self.locks[library_id]
```

#### Design Choices:

1. **Library-Level Granularity**
   - Each library has its own lock
   - Operations on different libraries can proceed concurrently
   - Prevents system-wide blocking during operations

2. **Async/Await Pattern**
   - All database methods are implemented as async functions
   - Context managers ensure locks are properly released
   - Compatible with FastAPI's async architecture

3. **Lock Acquisition Strategy**
   ```python
   async def add_chunk(self, library_id: UUID, document_id: UUID, chunk: Chunk):
       async with await self._get_lock(library_id):
           # Safe operations within the lock context
   ```
   - Atomic operations within lock contexts
   - Prevents data races during critical operations

4. **Read/Write Consistency**
   - Reads also acquire locks to ensure consistent views
   - Prevents reading partially updated data structures

### Data Consistency & Integrity

VectorFlow maintains data consistency and integrity through several mechanisms:

1. **Atomic Operations**
   - All CRUD operations are performed atomically within lock contexts
   - Ensures all-or-nothing updates

2. **Index-Data Synchronization**
   ```python
   # First update data structure
   doc.chunks.append(chunk)
   
   # Then try to update index incrementally
   if lib.index and Indexer.is_index_updateable(lib.index):
       try:
           lib.index.add_chunk(chunk)
       except Exception:
           # Graceful failure handling
           lib.index = None
   ```
   - Data structure updated first, then indexes
   - Indexes marked invalid if update fails
   - Ensures data and indexes stay in sync

3. **Cascading Deletes**
   - Deleting a library removes all its documents and chunks
   - Deleting a document removes all its chunks
   - Ensures referential integrity

4. **Validation Checks**
   - Verifies entity existence before operations
   - Raises clear, specific exceptions for invalid operations
   - Ensures data integrity throughout operations

### Metadata Filtering System

VectorFlow implements a powerful metadata filtering system:

```python
@staticmethod
def create_metadata_filter(**kwargs):
    def filter_func(chunk):
        for key, value in kwargs.items():
            if key.endswith('_after') and key[:-6] in chunk.metadata.__dict__:
                chunk_value = getattr(chunk.metadata, key[:-6])
                if chunk_value <= value:
                    return False
            # ... more filter implementations
        return True
    return filter_func
```

#### Features:

1. **Dynamic Filter Generation**
   - Creates filter functions on the fly
   - Combines multiple criteria with AND logic

2. **Rich Comparison Operators**
   - `field`: Exact match (equality)
   - `field_after`: Greater than comparison
   - `field_before`: Less than comparison
   - `field_contains`: Substring matching

3. **Integration with Queries**
   ```python
   # In API endpoint
   results = index.query(
       query_vector, 
       k=10, 
       metadata_filter=Indexer.create_metadata_filter(**filter_criteria)
   )
   ```

4. **Application Examples**
   ```python
   # Filter by date and category
   metadata_filter={
       "date_after": "2023-01-01",
       "category": "finance",
       "title_contains": "quarterly report"
   }
   ```

## API Endpoints

### Libraries

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/libraries/` | GET | Retrieve all libraries with summary information |
| `/libraries/` | POST | Create a new library |
| `/libraries/{library_id}` | GET | Retrieve a library by its ID |
| `/libraries/{library_id}` | DELETE | Delete a library and all its contents |
| `/libraries/{library_id}/index` | POST | Build or update a vector index |
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
| `/libraries/{library_id}/documents/{document_id}/chunks` | GET | Retrieve all chunks in a document |
| `/libraries/{library_id}/documents/{document_id}/chunks` | POST | Add a new chunk to a document |
| `/libraries/{library_id}/documents/{document_id}/chunks/{chunk_id}` | DELETE | Delete a chunk |
| `/libraries/{library_id}/batch-chunks` | POST | Process a batch of texts with automatic embedding generation |

## Performance Optimizations

VectorFlow includes several optimizations for high-performance vector search:

1. **Batched Processing**
   - Linear search processes vectors in batches to optimize CPU cache usage
   - Significant speedup for large datasets

2. **Vector Normalization**
   - Pre-normalizes vectors to unit length
   - Enables faster dot product calculations for cosine similarity

3. **Adaptive Index Selection**
   - Automatic warnings for suboptimal index choices
   - KD-Tree warns when dimensions exceed recommended threshold

4. **Incremental Index Updates**
   - Tracks changes to determine when full rebuilds are necessary
   - Applies incremental updates when possible to avoid rebuilding

5. **LSH Enhancements**
   - Neighboring hash exploration for improved recall
   - Intelligent candidate collection strategies
   - Fallback to broader search when results are insufficient

6. **Memory Optimizations**
   - Uses `__slots__` in performance-critical classes to reduce memory overhead
   - Avoids duplicate storage of embeddings

7. **Query Optimizations**
   - Early termination for dissimilar vectors
   - Heap-based top-k selection instead of sorting all distances
   - Optimized distance calculations

## Example Usage

### Creating a Library and Building an Index

```bash
# Create a new library
curl -X POST "http://localhost:8000/libraries/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Research Papers", "metadata": {"description": "AI research papers"}}'

# Build an LSH index for high-dimensional vectors
curl -X POST "http://localhost:8000/libraries/{library_id}/index" \
  -H "Content-Type: application/json" \
  -d '{"algorithm": "lsh"}'
```

### Searching by Vector

```bash
curl -X POST "http://localhost:8000/libraries/{library_id}/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": [0.1, 0.2, ...],
    "k": 5,
    "metadata_filter": {"category": "finance"}
  }'
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 