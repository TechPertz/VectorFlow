"""KD-Tree index implementation for vector search"""

import heapq
import random
from typing import List, Set, Optional, Callable
from uuid import UUID
from app.models import Chunk
from app.services.indexes.base import BaseIndex
from app.services.indexes.linear import LinearIndex

class KDTreeIndex(BaseIndex):
    """KD-Tree implementation for efficient vector search in lower dimensions"""
    
    class Node:
        __slots__ = ['chunk', 'axis', 'left', 'right', 'deleted']
        def __init__(self, chunk: Chunk, axis: int):
            self.chunk = chunk
            self.axis = axis
            self.left = None
            self.right = None
            self.deleted = False

    def __init__(self, chunks: List[Chunk], dim_threshold: int = 20):
        self.dim_threshold = dim_threshold
        self.deleted_chunks: Set[str] = set()
        self.added_chunks: List[Chunk] = []
        self.pending_changes = False
        self.rebuild_threshold = 0.1
        
        if not chunks:
            self.root = None
            self.total_chunks = 0
            return
            
        self.dim = len(chunks[0].embedding)
        
        if self.dim > dim_threshold:
            import warnings
            warnings.warn(
                f"KD-Tree performance degrades in high dimensions. "
                f"Current dimensionality ({self.dim}) exceeds recommended threshold ({dim_threshold}). "
                f"Consider using LSH for better performance with high-dimensional data.",
                RuntimeWarning
            )
        
        self.root = self._build(chunks, 0)
        self.total_chunks = len(chunks)
    
    def _find_split_axis(self, chunks: List[Chunk], depth: int) -> int:
        if not chunks or len(chunks) <= 1:
            return depth % self.dim if hasattr(self, 'dim') else 0
            
        variances = [0] * self.dim
        means = [0] * self.dim
        
        n = len(chunks)
        for chunk in chunks:
            for i, val in enumerate(chunk.embedding):
                means[i] += val
                
        for i in range(self.dim):
            means[i] /= n
        
        for chunk in chunks:
            for i, val in enumerate(chunk.embedding):
                variances[i] += (val - means[i]) ** 2
        
        max_axis = 0
        max_var = variances[0]
        for i in range(1, self.dim):
            if variances[i] > max_var:
                max_var = variances[i]
                max_axis = i
            
        return max_axis
    
    def _build(self, chunks: List[Chunk], depth: int):
        if not chunks:
            return None
            
        axis = self._find_split_axis(chunks, depth)
        
        mid = len(chunks) // 2
        self._quickselect(chunks, mid, axis)
        
        node = self.Node(chunks[mid], axis)
        node.left = self._build(chunks[:mid], depth + 1)
        node.right = self._build(chunks[mid+1:], depth + 1)
        return node
    
    def _quickselect(self, arr, k, axis):
        """Optimization: Use Python's built-in list.sort() for small arrays"""
        if len(arr) <= 20:
            arr.sort(key=lambda chunk: chunk.embedding[axis])
            return
            
        def partition(arr, left, right):
            pivot_idx = random.randint(left, right)
            pivot_val = arr[pivot_idx].embedding[axis]
            
            arr[pivot_idx], arr[right] = arr[right], arr[pivot_idx]
            
            store_idx = left
            for i in range(left, right):
                if arr[i].embedding[axis] < pivot_val:
                    arr[i], arr[store_idx] = arr[store_idx], arr[i]
                    store_idx += 1
            
            arr[store_idx], arr[right] = arr[right], arr[store_idx]
            return store_idx
        
        left, right = 0, len(arr) - 1
        while left < right:
            pivot_idx = partition(arr, left, right)
            if k == pivot_idx:
                return
            elif k < pivot_idx:
                right = pivot_idx - 1
            else:
                left = pivot_idx + 1
    
    def add_chunk(self, chunk: Chunk) -> bool:
        """Buffer the chunk for later inclusion - true incremental updates are hard for KD-Trees"""
        self.added_chunks.append(chunk)
        self.pending_changes = True
        self.total_chunks += 1
        return True
        
    def remove_chunk(self, chunk_id: UUID) -> bool:
        """Mark chunk as deleted without modifying the tree structure"""
        chunk_id_str = str(chunk_id)
        self.deleted_chunks.add(chunk_id_str)
        self.pending_changes = True
        
        for i, chunk in enumerate(self.added_chunks):
            if str(chunk.id) == chunk_id_str:
                self.added_chunks.pop(i)
                return True
        
        def _mark_deleted(node):
            if not node:
                return False
                
            if str(node.chunk.id) == chunk_id_str:
                node.deleted = True
                return True
                
            return _mark_deleted(node.left) or _mark_deleted(node.right)
        
        found = _mark_deleted(self.root)
        if found:
            self.total_chunks -= 1
        return found
    
    def check_rebuild_needed(self) -> bool:
        """Check if we should rebuild the tree based on the number of changes"""
        if not self.pending_changes:
            return False
            
        change_ratio = (len(self.added_chunks) + len(self.deleted_chunks)) / max(1, self.total_chunks)
        return change_ratio >= self.rebuild_threshold
    
    def rebuild_if_needed(self, all_chunks: List[Chunk] = None) -> bool:
        """Rebuild the tree if the number of changes exceeds the threshold"""
        if not self.check_rebuild_needed():
            return False
            
        if all_chunks is None:
            valid_chunks = []
            
            def _collect_valid(node):
                if not node:
                    return
                if not node.deleted and str(node.chunk.id) not in self.deleted_chunks:
                    valid_chunks.append(node.chunk)
                _collect_valid(node.left)
                _collect_valid(node.right)
            
            _collect_valid(self.root)
            
            valid_chunks.extend(self.added_chunks)
            all_chunks = valid_chunks
        
        self.root = self._build(all_chunks, 0)
        self.total_chunks = len(all_chunks)
        self.deleted_chunks.clear()
        self.added_chunks.clear()
        self.pending_changes = False
        
        return True
    
    def query(self, query: List[float], k: int, metadata_filter: Optional[Callable[[Chunk], bool]] = None) -> List[Chunk]:
        if self.check_rebuild_needed():
            self.rebuild_if_needed()
            
        buffered_results = []
        if self.added_chunks:
            linear = LinearIndex(self.added_chunks)
            buffered_results = linear.query(query, k, metadata_filter)

        if not self.root:
            return buffered_results
            
        heap = []
        deleted_set = self.deleted_chunks
        
        def _search(node, best_dist):
            if not node:
                return best_dist
                
            if not node.deleted and str(node.chunk.id) not in deleted_set:
                if metadata_filter and not metadata_filter(node.chunk):
                    pass
                else:
                    dist = sum((x - y)**2 for x, y in zip(query, node.chunk.embedding))
                    
                    if len(heap) < k:
                        heapq.heappush(heap, (-dist, node.chunk))
                        best_dist = -heap[0][0] if heap else float('inf')
                    elif dist < -heap[0][0]:
                        heapq.heappushpop(heap, (-dist, node.chunk))
                        best_dist = -heap[0][0]  

            axis_val = query[node.axis]
            node_val = node.chunk.embedding[node.axis]
            
            first, second = (node.left, node.right) if axis_val < node_val else (node.right, node.left)
            
            best_dist = _search(first, best_dist)
            
            if (axis_val - node_val)**2 < best_dist:
                best_dist = _search(second, best_dist)
                
            return best_dist
        
        _search(self.root, float('inf'))
        
        tree_results = [c for _, c in sorted(heap, reverse=True)]
        
        if buffered_results:
            combined = tree_results + buffered_results
            combined.sort(key=lambda c: -sum(q*v for q, v in zip(query, c.embedding)))
            return combined[:k]
            
        return tree_results 