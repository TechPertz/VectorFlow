# VectorFlow Indexing Algorithms

This document provides detailed information about the vector indexing algorithms implemented in VectorFlow for similarity search.

## Overview

VectorFlow implements three primary indexing algorithms, each with different characteristics, trade-offs, and optimal use cases:

1. **Linear Index** - Simple brute force approach
2. **KD-Tree Index** - Space-partitioning data structure for efficient search in lower dimensions
3. **LSH (Locality-Sensitive Hashing) Index** - Probabilistic technique for approximate nearest neighbor search in high dimensions

## Linear Index

### How It Works
The Linear Index is the simplest approach, implementing a brute force search:
- Stores all vectors (embeddings) in a flat array
- For each query, computes the similarity between the query vector and every vector in the index
- Returns the k vectors with the highest similarity scores

### Implementation Details
- Supports normalization of vectors to unit length for faster dot product comparisons
- Computes similarity using dot product (for normalized vectors) or negative Euclidean distance
- Processes chunks in batches to improve performance

### Time Complexity
- **Index Construction**: O(n) - simply stores all vectors
- **Query**: O(n × d) - where n is the number of vectors and d is the vector dimension
- **Memory Usage**: O(n × d) - stores all vectors directly

### Incremental Updates
- **Add**: O(1) - simply append to the list
- **Remove**: O(n) - requires rebuilding the vector-to-index mapping

### Optimal Use Cases
- Small datasets (up to a few thousand vectors)
- Situations where index construction speed is prioritized over query speed
- When exact results are required, not approximations
- Development and testing environments

## KD-Tree Index

### How It Works
The KD-Tree (K-Dimensional Tree) is a space-partitioning data structure:
- Recursively partitions the vector space along different dimensions
- Creates a binary tree where each node represents a split along one dimension
- During queries, efficiently traverses only relevant partitions of the space

### Implementation Details
- Uses variance-based selection of split dimensions for better balance
- Implements optimized quickselect for median finding during construction
- Handles high-dimensional warnings (performance degrades in high dimensions)

### Time Complexity
- **Index Construction**: O(n log n) average case - building a balanced tree
- **Query**: 
  - Best case: O(log n) for well-distributed data in low dimensions
  - Average case: O(n^(1-1/d)) for higher dimensions
  - Worst case: O(n) when tree becomes unbalanced or in very high dimensions
- **Memory Usage**: O(n) - only stores references in tree nodes

### Incremental Updates
- True incremental updates are difficult for KD-Tree as they can unbalance the tree
- Instead, tracks added and deleted chunks separately
- Triggers a full rebuild when changes exceed a threshold (configurable)

### Optimal Use Cases
- Low to medium-dimensional data (typically d ≤ 20)
- Data with natural clusters or structure
- When exact or very close approximations are required
- Applications where fast queries are needed but LSH approximation is unacceptable

## LSH (Locality-Sensitive Hashing) Index

### How It Works
LSH is a probabilistic technique for approximate nearest neighbor search:
- Creates multiple hash tables, each with a different hash function set
- Similar vectors are likely to be hashed to the same bucket in at least one table
- Queries inspect only a small subset of all vectors (those in matching buckets)

### Implementation Details
- Uses random hyperplanes for hashing (cosine similarity)
- Supports multiple hash tables to increase probability of finding similar vectors
- Implements neighbor exploration for improved recall

### Time Complexity
- **Index Construction**: O(n × d × L × K) - where L is the number of tables and K is the hash size
- **Query**: 
  - Average case: O(L + n/2^K) - often sublinear in practice
  - Worst case: O(n) when excessive candidates are found
- **Memory Usage**: O(n × L) - stores each vector reference L times (once per table)

### Incremental Updates
- **Add**: O(L × K) - add to all hash tables
- **Remove**: O(L) - remove from all buckets where present

### Optimal Use Cases
- High-dimensional data (d > 20)
- Very large datasets (millions of vectors)
- Applications where approximate nearest neighbors are acceptable
- When query speed is prioritized over exact results
- Real-time applications requiring sub-linear search time

## Performance Comparison

| Algorithm | Construction Time | Query Time | Memory Usage | Exact Results | Update Support | Dimensionality |
|-----------|-------------------|------------|--------------|---------------|----------------|----------------|
| Linear    | Very Fast         | Slow       | Medium       | Yes           | Excellent      | Any            |
| KD-Tree   | Medium            | Fast (low-d)| Low          | Yes           | Limited        | Low/Medium     |
| LSH       | Medium            | Very Fast  | High         | Approximate   | Good           | High           |

## Choosing the Right Index

Consider these factors when selecting an index:

1. **Dataset Size:**
   - Small (<10K vectors): Linear or KD-Tree
   - Medium (10K-1M vectors): KD-Tree or LSH
   - Large (>1M vectors): LSH

2. **Vector Dimensionality:**
   - Low (<10 dimensions): KD-Tree
   - Medium (10-100 dimensions): KD-Tree or LSH
   - High (>100 dimensions): LSH

3. **Result Quality Requirements:**
   - Exact results needed: Linear or KD-Tree
   - Approximate results acceptable: LSH

4. **Update Frequency:**
   - Frequent updates: Linear
   - Occasional updates: LSH
   - Rare updates: Any

5. **Query Speed Requirements:**
   - Fastest possible: LSH
   - Balanced speed/accuracy: KD-Tree
   - Accuracy over speed: Linear

## Implementation Notes

All indexes in VectorFlow implement a common interface:
- `add_chunk(chunk)` - Add a new chunk to the index
- `remove_chunk(chunk_id)` - Remove a chunk from the index
- `query(query, k, metadata_filter)` - Find k most similar chunks with optional filtering

Indexes can be created using the `Indexer.create_index()` factory method with the appropriate algorithm name.

## Advanced Features

### Metadata Filtering
All indexes support filtering results based on metadata during queries:
```python
results = index.query(query_vector, k=10, metadata_filter=lambda chunk: chunk.metadata.category == "finance")
```

### Automatic Index Management
VectorFlow monitors index quality and can recommend or perform rebuilds when necessary:
- Checks if index rebuilds are needed based on change ratios
- Can rebuild incrementally when supported
- Warns users when index performance might be degraded 