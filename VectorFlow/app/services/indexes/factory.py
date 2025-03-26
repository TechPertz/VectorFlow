"""Index factory for creating and managing indexes"""

from typing import List, Callable
from app.models import Chunk
from app.services.indexes.base import BaseIndex
from app.services.indexes.linear import LinearIndex
from app.services.indexes.kdtree import KDTreeIndex
from app.services.indexes.lsh import LSHIndex

class Indexer:
    """Factory class for creating and managing indexes"""
    
    @staticmethod
    def create_index(chunks: List[Chunk], algorithm: str):
        """
        Factory method to create the appropriate index based on the algorithm name
        """
        if algorithm == "linear":
            return LinearIndex(chunks)
        elif algorithm == "kd_tree":
            return KDTreeIndex(chunks)
        elif algorithm == "lsh":
            return LSHIndex(chunks)
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    @staticmethod
    def is_index_updateable(index) -> bool:
        """
        Check if an index supports incremental updates
        """
        return isinstance(index, BaseIndex)
    
    @staticmethod
    def create_metadata_filter(**kwargs):
        """
        Create a metadata filter function based on provided criteria.
        
        Example:
            filter = create_metadata_filter(date_after="2023-01-01", name_contains="report")
            results = index.query(query_vector, k=10, metadata_filter=filter)
        """
        def filter_func(chunk):
            if not hasattr(chunk, 'metadata') or not chunk.metadata:
                return False
                
            for key, value in kwargs.items():
                if key.endswith('_after') and key[:-6] in chunk.metadata.__dict__:
                    chunk_value = getattr(chunk.metadata, key[:-6])
                    if chunk_value <= value:
                        return False
                elif key.endswith('_before') and key[:-7] in chunk.metadata.__dict__:
                    chunk_value = getattr(chunk.metadata, key[:-7])
                    if chunk_value >= value:
                        return False
                elif key.endswith('_contains') and key[:-9] in chunk.metadata.__dict__:
                    chunk_value = getattr(chunk.metadata, key[:-9])
                    if value not in chunk_value:
                        return False
                elif key in chunk.metadata.__dict__:
                    chunk_value = getattr(chunk.metadata, key)
                    if chunk_value != value:
                        return False
                        
            return True
            
        return filter_func 