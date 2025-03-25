import pytest
import random
from uuid import uuid4
from datetime import datetime

from app.models import Chunk, ChunkMetadata
from app.services.indexes import LinearIndex, KDTreeIndex, LSHIndex

pytestmark = pytest.mark.unit

@pytest.fixture
def sample_chunks():
    """Generate a set of sample chunks for testing indexes."""
    chunks = []
    for i in range(10):
        chunk = Chunk(
            id=uuid4(),
            text=f"Test chunk {i}",
            embedding=[random.random() for _ in range(4)],
            metadata=ChunkMetadata(name=f"test_{i}", created_at=datetime.now())
        )
        chunks.append(chunk)
    return chunks

@pytest.fixture
def random_query():
    """Generate a random query vector for testing."""
    return [random.random() for _ in range(4)]

@pytest.mark.unit
class TestIndexes:
    """Unit tests for the vector index implementations"""
    
    def test_linear_index(self, sample_chunks, random_query):
        """Test that LinearIndex returns the correct number of results."""

        index = LinearIndex(sample_chunks)
        
        for k in [1, 3, 5, 10]:
            results = index.query(random_query, k)

            expected_count = min(k, len(sample_chunks))
            assert len(results) == expected_count, f"LinearIndex should return {expected_count} results for k={k}"
            
            for result in results:
                assert isinstance(result, Chunk), "Result should be a Chunk object"

    def test_kd_tree_index(self, sample_chunks, random_query):
        """Test that KDTreeIndex returns the correct number of results."""
        
        index = KDTreeIndex(sample_chunks)
        
        for k in [1, 3, 5, 10]:
            results = index.query(random_query, k)
            
            expected_count = min(k, len(sample_chunks))
            assert len(results) == expected_count, f"KDTreeIndex should return {expected_count} results for k={k}"
            
            for result in results:
                assert isinstance(result, Chunk), "Result should be a Chunk object"

    def test_lsh_index(self, sample_chunks, random_query):
        """Test that LSHIndex returns results (may be less than k due to LSH approximation)."""
        
        index = LSHIndex(sample_chunks)
        
        for k in [1, 3, 5, 10]:
            results = index.query(random_query, k)

            assert len(results) <= k, f"LSHIndex should return at most {k} results for k={k}"
            
            if len(sample_chunks) >= k:
                assert len(results) > 0, "LSHIndex should return at least some results"
            
            for result in results:
                assert isinstance(result, Chunk), "Result should be a Chunk object"

    def test_index_results_are_ordered_by_similarity(self, sample_chunks):
        """Test that index results are ordered by decreasing similarity to query."""

        reference_chunk = sample_chunks[0]
        query = reference_chunk.embedding.copy()
        
        query = [x * 0.95 for x in query]
        
        for index_class in [LinearIndex, KDTreeIndex, LSHIndex]:
            index = index_class(sample_chunks)
            results = index.query(query, len(sample_chunks))
        
            if index_class is LSHIndex and len(results) > 0:
                first_few_ids = [str(chunk.id) for chunk in results[:3]]
                assert str(reference_chunk.id) in first_few_ids, f"Reference chunk not in top 3 results for {index_class.__name__}"
            elif len(results) > 0:
                assert str(results[0].id) == str(reference_chunk.id), f"First result is not the reference chunk for {index_class.__name__}"

    def test_empty_index(self):
        """Test that indexes handle empty input gracefully."""
        empty_chunks = []
        query = [0.1, 0.2, 0.3, 0.4]
        
        for index_class in [LinearIndex, KDTreeIndex, LSHIndex]:
            index = index_class(empty_chunks)
            results = index.query(query, 5)
            assert len(results) == 0, f"{index_class.__name__} should return empty results for empty index"

@pytest.mark.integration
@pytest.mark.parametrize("index_class", [LinearIndex, KDTreeIndex, LSHIndex])
def test_index_with_large_dataset(index_class):
    """Integration test with a larger dataset to test performance and correctness."""

    chunks = []
    for i in range(100):
        chunk = Chunk(
            id=uuid4(),
            text=f"Large dataset chunk {i}",
            embedding=[random.random() for _ in range(10)],  
            metadata=ChunkMetadata(name=f"large_test_{i}", created_at=datetime.now())
        )
        chunks.append(chunk)
    
    index = index_class(chunks)
    
    query = [random.random() for _ in range(10)]
    
    k = 20
    results = index.query(query, k)
    
    assert len(results) <= k, f"Should return at most {k} results"
    if index_class != LSHIndex:  
        assert len(results) == k, f"Should return exactly {k} results for non-LSH indexes"
    
    result_ids = [id(result) for result in results]
    assert len(result_ids) == len(set(result_ids)), "Results should be unique" 