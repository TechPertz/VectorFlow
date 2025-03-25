import heapq
import random
import math
# import numpy as np
from typing import List, DefaultDict, Optional, Tuple
from collections import defaultdict
from app.models import Chunk

class LinearIndex:
    def __init__(self, chunks: List[Chunk], normalize: bool = True, batch_size: int = 1000):
        
        self.chunks = chunks
        self.normalize = normalize
        self.batch_size = batch_size
        self.normalized_embeddings = None
        
        if normalize and chunks:
            self._normalize_embeddings()
    
    def _normalize_embeddings(self) -> None:
        """Normalize all embeddings to unit length for faster dot product comparison"""
        self.normalized_embeddings = []
        for chunk in self.chunks:
            vec = chunk.embedding
            norm = math.sqrt(sum(x*x for x in vec))
            if norm > 0:
                self.normalized_embeddings.append([x/norm for x in vec])
            else:
                self.normalized_embeddings.append(vec)  # Keep zero vectors as is
    
    def _compute_similarity(self, query: List[float], chunk_idx: int) -> float:
        
        if self.normalize:
            return sum(q*v for q, v in zip(query, self.normalized_embeddings[chunk_idx]))
        else:
            return -sum((q-v)**2 for q, v in zip(query, self.chunks[chunk_idx].embedding))
    
    def query(self, query: List[float], k: int) -> List[Chunk]:

        if self.normalize:
            norm = math.sqrt(sum(x*x for x in query))
            if norm > 0:
                query = [x/norm for x in query]
        
        heap = []  
        
        for batch_start in range(0, len(self.chunks), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(self.chunks))
            
            for i in range(batch_start, batch_end):
                similarity = self._compute_similarity(query, i)
                
                if len(heap) < k:
                    heapq.heappush(heap, (similarity, i))
                elif similarity > heap[0][0]:
                    heapq.heappushpop(heap, (similarity, i))
        
        sorted_results = sorted(heap, reverse=True)
        return [self.chunks[idx] for _, idx in sorted_results]

class KDTreeIndex:
    class Node:
        __slots__ = ['chunk', 'axis', 'left', 'right']
        def __init__(self, chunk: Chunk, axis: int):
            self.chunk = chunk
            self.axis = axis
            self.left = None
            self.right = None

    def __init__(self, chunks: List[Chunk]):
        self.root = self._build(chunks, 0)
    
    def _build(self, chunks: List[Chunk], depth: int):
        if not chunks:
            return None
        axis = depth % len(chunks[0].embedding)
        
        mid = len(chunks) // 2
        self._quickselect(chunks, mid, axis)
        
        node = self.Node(chunks[mid], axis)
        node.left = self._build(chunks[:mid], depth + 1)
        node.right = self._build(chunks[mid+1:], depth + 1)
        return node
    
    def _quickselect(self, arr, k, axis):
        """In-place partial sorting for O(n) avg case"""
        while True:
            if len(arr) == 1:
                return
            pivot_idx = random.randint(0, len(arr)-1)
            pivot_val = arr[pivot_idx].embedding[axis]
            left, right = [], []
            for item in arr:
                if item.embedding[axis] < pivot_val:
                    left.append(item)
                elif item.embedding[axis] >= pivot_val:
                    right.append(item)
            if k < len(left):
                arr = left
            else:
                k -= len(left)
                arr = right
                if k == 0:
                    return
    
    def query(self, query: List[float], k: int) -> List[Chunk]:
        heap = []
        
        def _search(node):
            if not node:
                return
            dist = sum((x - y)**2 for x, y in zip(query, node.chunk.embedding))
            if len(heap) < k or -dist > heap[0][0]:
                if len(heap) == k:
                    heapq.heappop(heap)
                heapq.heappush(heap, (-dist, node.chunk))
            
            axis_val = query[node.axis]
            node_val = node.chunk.embedding[node.axis]
            
            if axis_val < node_val:
                _search(node.left)
                if (node_val - axis_val)**2 < -heap[0][0]:
                    _search(node.right)
            else:
                _search(node.right)
                if (axis_val - node_val)**2 < -heap[0][0]:
                    _search(node.left)
        
        _search(self.root)
        return [c for _, c in sorted(heap, reverse=True)]

class LSHIndex:
    __slots__ = ['tables', 'hyperplanes', 'num_tables', 'hash_size']
    
    def __init__(self, chunks: List[Chunk], num_tables=4, hash_size=8):
        self.num_tables = num_tables
        self.hash_size = hash_size
        self.tables: List[DefaultDict[int, List[Chunk]]] = [defaultdict(list) for _ in range(num_tables)]
        
        if not chunks:
            self.hyperplanes = []
            return
            
        dim = len(chunks[0].embedding)
        self.hyperplanes = [
            [random.gauss(0, 1) for _ in range(dim)]
            for _ in range(num_tables * hash_size)
        ]
        
        for chunk in chunks:
            for ti in range(num_tables):
                hash_val = self._compute_hash(chunk.embedding, ti)
                self.tables[ti][hash_val].append(chunk)
    
    def _compute_hash(self, vec: List[float], table_idx: int) -> int:
        hash_val = 0
        for h in range(self.hash_size):
            hp = self.hyperplanes[table_idx * self.hash_size + h]
            hash_val |= (1 << h) if sum(x*y for x,y in zip(vec, hp)) >= 0 else 0
        return hash_val
    
    def query(self, query: List[float], k: int) -> List[Chunk]:
        candidates = []
        for ti in range(self.num_tables):
            hash_val = self._compute_hash(query, ti)
            candidates.extend(self.tables[ti][hash_val])
        
        # Remove duplicates without using set (since Chunk may not be hashable)
        # We'll use a list to keep track of seen chunks by ID
        unique_candidates = []
        seen_chunk_ids = set()
        
        for chunk in candidates:
            # Use object ID as a unique identifier since Chunk may not have an id attribute
            chunk_id = id(chunk)
            if chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(chunk_id)
                unique_candidates.append(chunk)
                
                # Limit to 3*k candidates for efficiency
                if len(unique_candidates) >= 3*k:
                    break
        
        # Rerank candidates using exact distance
        return LinearIndex(unique_candidates).query(query, k)


class Indexer:
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