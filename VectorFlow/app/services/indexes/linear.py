"""Linear index implementation for vector search"""

import heapq
from typing import List, Dict, Optional, Callable
from uuid import UUID
from app.models import Chunk
from app.services.indexes.base import BaseIndex, normalize_vector

class LinearIndex(BaseIndex):
    """Linear index implementation using brute force search"""
    
    def __init__(self, chunks: List[Chunk], normalize: bool = True, batch_size: int = 1000):
        self.chunks = chunks
        self.normalize = normalize
        self.batch_size = batch_size
        self.normalized_embeddings = None
        self.chunk_id_to_idx: Dict[str, int] = {}
        
        for i, chunk in enumerate(self.chunks):
            self.chunk_id_to_idx[str(chunk.id)] = i
        
        if normalize and chunks:
            self._normalize_embeddings()
    
    def _normalize_embeddings(self) -> None:
        """Normalize all embeddings to unit length for faster dot product comparison"""
        self.normalized_embeddings = []
        for chunk in self.chunks:
            self.normalized_embeddings.append(normalize_vector(chunk.embedding) if self.normalize else chunk.embedding)
    
    def _compute_similarity(self, query: List[float], chunk_idx: int) -> float:
        if self.normalize:
            return sum(q*v for q, v in zip(query, self.normalized_embeddings[chunk_idx]))
        else:
            return -sum((q-v)**2 for q, v in zip(query, self.chunks[chunk_idx].embedding))
    
    def add_chunk(self, chunk: Chunk) -> bool:
        """Add a new chunk to the index incrementally"""
        chunk_id_str = str(chunk.id)
        
        if chunk_id_str in self.chunk_id_to_idx:
            return False
            
        self.chunks.append(chunk)
        self.chunk_id_to_idx[chunk_id_str] = len(self.chunks) - 1
        
        if self.normalize and self.normalized_embeddings is not None:
            self.normalized_embeddings.append(normalize_vector(chunk.embedding))
                
        return True
    
    def remove_chunk(self, chunk_id: UUID) -> bool:
        """Remove a chunk from the index incrementally"""
        chunk_id_str = str(chunk_id)
        
        if chunk_id_str not in self.chunk_id_to_idx:
            return False
            
        idx = self.chunk_id_to_idx[chunk_id_str]
        
        self.chunks.pop(idx)
        if self.normalize and self.normalized_embeddings:
            self.normalized_embeddings.pop(idx)
            
        self.chunk_id_to_idx = {str(chunk.id): i for i, chunk in enumerate(self.chunks)}
            
        return True
    
    def query(self, query: List[float], k: int, metadata_filter: Optional[Callable[[Chunk], bool]] = None) -> List[Chunk]:
        if not self.chunks or k <= 0:
            return []

        if self.normalize:
            query = normalize_vector(query)
        
        heap = []  
        
        for batch_start in range(0, len(self.chunks), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(self.chunks))
            
            for i in range(batch_start, batch_end):
                if metadata_filter and not metadata_filter(self.chunks[i]):
                    continue
                    
                similarity = self._compute_similarity(query, i)
                
                if len(heap) < k:
                    heapq.heappush(heap, (similarity, i))
                elif similarity > heap[0][0]:
                    heapq.heappushpop(heap, (similarity, i))
        
        sorted_results = sorted(heap, reverse=True)
        return [self.chunks[idx] for _, idx in sorted_results] 