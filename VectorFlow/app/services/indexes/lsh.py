"""LSH (Locality-Sensitive Hashing) index implementation for vector search"""

import random
from collections import defaultdict
from typing import List, Set, Dict, Optional, Callable
from uuid import UUID
from app.models import Chunk
from app.services.indexes.base import BaseIndex, normalize_vector
from app.services.indexes.linear import LinearIndex

class LSHIndex(BaseIndex):
    """LSH implementation for efficient vector search in high dimensions"""
    
    __slots__ = ['tables', 'hyperplanes', 'num_tables', 'hash_size', 'normalize', 'max_candidates', 
                'chunk_id_map', 'pending_changes', 'dim']
    
    def __init__(self, chunks: List[Chunk], num_tables=6, hash_size=12, normalize=True, max_candidates=50):
        self.num_tables = num_tables
        self.hash_size = hash_size
        self.normalize = normalize
        self.max_candidates = max_candidates
        self.tables = [defaultdict(list) for _ in range(num_tables)]
        self.hyperplanes = []
        self.chunk_id_map = {}
        self.pending_changes = False
        self.dim = 0
        
        if not chunks:
            return
        
        self.dim = len(chunks[0].embedding)
        
        self._generate_hyperplanes(self.dim)
        
        for chunk in chunks:
            self._add_to_tables(chunk)
            self.chunk_id_map[str(chunk.id)] = chunk
    
    def _generate_hyperplanes(self, dim: int) -> None:
        """Generate random hyperplanes for LSH hashing"""
        self.hyperplanes = []
        for _ in range(self.num_tables * self.hash_size):
            hyperplane = [random.gauss(0, 1) for _ in range(dim)]
            self.hyperplanes.append(normalize_vector(hyperplane))
    
    def _normalize_vector(self, embedding: List[float]) -> List[float]:
        """Normalize a vector to unit length"""
        if not self.normalize:
            return embedding
        return normalize_vector(embedding)
    
    def _add_to_tables(self, chunk: Chunk) -> None:
        """Add a chunk to all LSH tables"""
        embedding = self._normalize_vector(chunk.embedding)
        
        for ti in range(self.num_tables):
            hash_val = self._compute_hash(embedding, ti)
            self.tables[ti][hash_val].append(chunk)
    
    def _compute_hash(self, vec: List[float], table_idx: int) -> int:
        """Compute LSH hash value for a vector in a specific table"""
        hash_val = 0
        offset = table_idx * self.hash_size
        
        for h in range(self.hash_size):
            hp = self.hyperplanes[offset + h]
            dot_product = sum(v*h for v, h in zip(vec, hp))
            if dot_product >= 0:
                hash_val |= (1 << h)
                
        return hash_val
    
    def add_chunk(self, chunk: Chunk) -> bool:
        """Add a new chunk to the LSH index incrementally"""
        if not self.hyperplanes:
            if not self.dim:
                self.dim = len(chunk.embedding)
                self._generate_hyperplanes(self.dim)
            else:
                return False
            
        chunk_id_str = str(chunk.id)
        if chunk_id_str in self.chunk_id_map:
            return False
            
        self._add_to_tables(chunk)
        self.chunk_id_map[chunk_id_str] = chunk
        self.pending_changes = True
        return True
    
    def remove_chunk(self, chunk_id: UUID) -> bool:
        """Remove a chunk from all LSH tables"""
        chunk_id_str = str(chunk_id)
        
        if chunk_id_str not in self.chunk_id_map:
            return False
            
        del self.chunk_id_map[chunk_id_str]
        
        for table in self.tables:
            for hash_val, chunks in list(table.items()):
                for i, chunk in enumerate(chunks):
                    if str(chunk.id) == chunk_id_str:
                        chunks.pop(i)
                        self.pending_changes = True
                        if not chunks:
                            del table[hash_val]
                        break
        
        return True
    
    def _get_neighboring_hashes(self, original_hash: int, max_distance: int = 2) -> Set[int]:
        """Get hash values within Hamming distance of the original hash"""
        if max_distance <= 0:
            return {original_hash}
            
        neighbors = {original_hash}
        
        dist1_neighbors = set()
        for bit in range(self.hash_size):
            neighbor = original_hash ^ (1 << bit)
            dist1_neighbors.add(neighbor)
        
        neighbors.update(dist1_neighbors)
        
        if max_distance >= 2:
            for n1 in dist1_neighbors:
                for bit in range(self.hash_size):
                    if n1 & (1 << bit) != original_hash & (1 << bit):
                        continue
                    neighbor = n1 ^ (1 << bit)
                    neighbors.add(neighbor)
                    
        return neighbors
    
    def query(self, query: List[float], k: int, metadata_filter: Optional[Callable[[Chunk], bool]] = None) -> List[Chunk]:
        """Query for k most similar chunks with optional metadata filtering"""
        if not self.hyperplanes or k <= 0:
            return []

        query = self._normalize_vector(query)
        
        query_hashes = [self._compute_hash(query, ti) for ti in range(self.num_tables)]
        
        candidates, seen_ids = self._search_candidates(query_hashes, k, metadata_filter)
        
        if len(candidates) <= k:
            return candidates
            
        return self._rank_candidates(candidates, query, k)
    
    def _search_candidates(self, query_hashes, target_k, metadata_filter=None, max_distance=2):
        """
        Efficient candidate search that avoids redundant code and optimizes performance
        Returns: (candidates, seen_ids)
        """
        candidates = []
        seen_ids = set()
        
        for ti, hash_val in enumerate(query_hashes):
            self._collect_from_bucket(self.tables[ti][hash_val], candidates, seen_ids, metadata_filter)
            if len(candidates) >= target_k * 3:
                return candidates, seen_ids
        
        if len(candidates) < target_k:
            for ti, hash_val in enumerate(query_hashes):
                neighbors = self._get_neighboring_hashes(hash_val, max_distance)
                for neighbor in neighbors:
                    if neighbor == hash_val:
                        continue
                    self._collect_from_bucket(self.tables[ti][neighbor], candidates, seen_ids, metadata_filter)
                    if len(candidates) >= target_k * 3:
                        return candidates, seen_ids
        
        if len(candidates) < target_k:
            self._fallback_broader_search(candidates, seen_ids, query_hashes, target_k, metadata_filter)
            
        return candidates, seen_ids
    
    def _collect_from_bucket(self, bucket, candidates, seen_ids, metadata_filter=None):
        """Helper method to collect chunks from a bucket, applying metadata filter"""
        for chunk in bucket:
            chunk_id = str(chunk.id)
            if chunk_id in seen_ids:
                continue
                
            if metadata_filter and not metadata_filter(chunk):
                continue
                
            seen_ids.add(chunk_id)
            candidates.append(chunk)
    
    def _fallback_broader_search(self, candidates, seen_ids, query_hashes, k, metadata_filter=None):
        """Fallback search strategy using bucket size heuristic"""
        all_buckets = []
        query_hash_set = set(query_hashes)
        
        for ti, table in enumerate(self.tables):
            for hash_val, chunks in table.items():
                if hash_val not in query_hash_set and chunks:
                    all_buckets.append((len(chunks), ti, hash_val))
        
        if not all_buckets:
            return
            
        all_buckets.sort()
        
        chunks_needed = max(k - len(candidates), k // 2)
        for _, ti, hash_val in all_buckets:
            self._collect_from_bucket(self.tables[ti][hash_val], candidates, seen_ids, metadata_filter)
            if len(candidates) >= chunks_needed + len(candidates):
                break
    
    def _rank_candidates(self, candidates, query, k):
        """Rank candidates by exact distance and return top k"""
        if len(candidates) > self.max_candidates:
            random.shuffle(candidates)
            candidates = candidates[:self.max_candidates]
        
        results = LinearIndex(candidates, normalize=self.normalize).query(query, k)
        return results 