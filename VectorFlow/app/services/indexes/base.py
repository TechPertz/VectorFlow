"""Base index implementation and utility functions"""

import math
from typing import List, Optional, Callable
from uuid import UUID
from app.models import Chunk

class BaseIndex:
    """Base class for all index implementations with incremental update support"""
    
    def add_chunk(self, chunk: Chunk) -> bool:
        """
        Add a new chunk to the index incrementally
        Returns True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement add_chunk")
    
    def remove_chunk(self, chunk_id: UUID) -> bool:
        """
        Remove a chunk from the index incrementally
        Returns True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement remove_chunk")
    
    def query(self, query: List[float], k: int, metadata_filter: Optional[Callable[[Chunk], bool]] = None) -> List[Chunk]:
        """
        Query the index for the k most similar chunks
        
        Args:
            query: The query vector
            k: Number of results to return
            metadata_filter: Optional function that takes a Chunk and returns True if it should be included
        """
        raise NotImplementedError("Subclasses must implement query")

def normalize_vector(vec: List[float]) -> List[float]:
    """Normalize a vector to unit length - utility function shared by indexes"""
    norm = math.sqrt(sum(x*x for x in vec))
    if norm > 0:
        return [x/norm for x in vec]
    return vec.copy() 