import heapq
import random
from typing import List
from app.models import Chunk

class LinearIndex:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks

    def query(self, query: List[float], k: int) -> List[Chunk]:
        heap = []
        for chunk in self.chunks:
            dist = sum((x - y)**2 for x, y in zip(query, chunk.embedding))
            if len(heap) < k:
                heapq.heappush(heap, (-dist, chunk))
            else:
                heapq.heappushpop(heap, (-dist, chunk))
        return [c for _, c in sorted(heap, reverse=True)]

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
        raise ValueError(f"Unknown algorithm: {algorithm}") 