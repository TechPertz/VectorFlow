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
        print(f"LinearIndex.query called with k={k}, chunks count={len(self.chunks)}")

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
        results = [self.chunks[idx] for _, idx in sorted_results]
        print(f"LinearIndex.query returning {len(results)} results")
        return results

class KDTreeIndex:
    class Node:
        __slots__ = ['chunk', 'axis', 'left', 'right']
        def __init__(self, chunk: Chunk, axis: int):
            self.chunk = chunk
            self.axis = axis
            self.left = None
            self.right = None

    def __init__(self, chunks: List[Chunk], dim_threshold: int = 20):
        
        if not chunks:
            self.root = None
            return
            
        dim = len(chunks[0].embedding)
        if dim > dim_threshold:
            import warnings
            warnings.warn(
                f"KD-Tree performance degrades in high dimensions. "
                f"Current dimensionality ({dim}) exceeds recommended threshold ({dim_threshold}). "
                f"Consider using LSH for better performance with high-dimensional data.",
                RuntimeWarning
            )
        
        self.root = self._build(chunks, 0)
    
    def _find_split_axis(self, chunks: List[Chunk], depth: int) -> int:
        
        if not chunks:
            return 0
            
        dim = len(chunks[0].embedding)
        if len(chunks) <= 1:
            return depth % dim
            
        variances = []
        for axis in range(dim):
            values = [chunk.embedding[axis] for chunk in chunks]
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            variances.append((variance, axis))
            
        return max(variances)[1]
    
    def _build(self, chunks: List[Chunk], depth: int):
        """
        Build the KD-Tree recursively.
        
        Args:
            chunks: List of chunks to organize in the tree
            depth: Current depth in the tree
        
        Returns:
            Root node of the subtree
        """
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
        """In-place partial sorting for O(n) avg case"""
        while True:
            if len(arr) <= 1:
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
        print(f"KDTreeIndex.query called with k={k}")

        if not self.root:
            return []
            
        heap = []
        
        def _search(node, best_dist):
            if not node:
                return best_dist
                
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
        
        results = [c for _, c in sorted(heap, reverse=True)]
        print(f"KDTreeIndex.query returning {len(results)} results")
        return results

class LSHIndex:
    __slots__ = ['tables', 'hyperplanes', 'num_tables', 'hash_size', 'normalize', 'max_candidates']
    
    def __init__(self, chunks: List[Chunk], num_tables=6, hash_size=12, normalize=True, max_candidates=50):
        
        self.num_tables = num_tables
        self.hash_size = hash_size
        self.normalize = normalize
        self.max_candidates = max_candidates
        self.tables: List[DefaultDict[int, List[Chunk]]] = [defaultdict(list) for _ in range(num_tables)]
        
        if not chunks:
            self.hyperplanes = []
            return
        
        dim = len(chunks[0].embedding)
        self.hyperplanes = []
        
        for _ in range(num_tables * hash_size):

            hyperplane = [random.gauss(0, 1) for _ in range(dim)]
            
            norm = math.sqrt(sum(x*x for x in hyperplane))
            if norm > 0:
                hyperplane = [x/norm for x in hyperplane]
                
            self.hyperplanes.append(hyperplane)
        
        for chunk in chunks:
            embedding = chunk.embedding
            
            if normalize:
                norm = math.sqrt(sum(x*x for x in embedding))
                if norm > 0:
                    embedding = [x/norm for x in embedding]
            
            for ti in range(num_tables):
                hash_val = self._compute_hash(embedding, ti)
                self.tables[ti][hash_val].append(chunk)
    
    def _compute_hash(self, vec: List[float], table_idx: int) -> int:
        hash_val = 0
        for h in range(self.hash_size):
            hp = self.hyperplanes[table_idx * self.hash_size + h]
            hash_val |= (1 << h) if sum(x*y for x, y in zip(vec, hp)) >= 0 else 0
        return hash_val
    
    def query(self, query: List[float], k: int) -> List[Chunk]:
        print(f"LSHIndex.query called with k={k}")

        if self.normalize:
            norm = math.sqrt(sum(x*x for x in query))
            if norm > 0:
                query = [x/norm for x in query]
        
        # First try the exact bucket matches
        candidates = []
        hash_vals = []
        
        for ti in range(self.num_tables):
            hash_val = self._compute_hash(query, ti)
            hash_vals.append(hash_val)
            candidates.extend(self.tables[ti][hash_val])
        
        print(f"LSHIndex found {len(candidates)} initial candidates")
        
        # If we don't have enough candidates, try neighboring buckets
        if len(candidates) < k:
            print(f"Not enough candidates, exploring neighboring buckets")
            # For each hash table
            for ti in range(self.num_tables):
                original_hash = hash_vals[ti]
                
                # First try flipping each bit of the hash to find neighboring buckets
                for bit in range(self.hash_size):
                    # Create a neighbor hash by flipping a bit
                    neighbor_hash = original_hash ^ (1 << bit)
                    # Only look at this bucket if we haven't seen it already
                    if neighbor_hash != original_hash:
                        candidates.extend(self.tables[ti][neighbor_hash])
                
                # If still not enough candidates, try flipping two bits (more distant neighbors)
                if len(candidates) < k * 2:
                    print(f"Still not enough candidates, exploring more distant buckets")
                    for bit1 in range(self.hash_size):
                        for bit2 in range(bit1 + 1, self.hash_size):
                            # Create a neighbor hash by flipping two bits
                            neighbor_hash = original_hash ^ (1 << bit1) ^ (1 << bit2)
                            # Add candidates from this bucket
                            candidates.extend(self.tables[ti][neighbor_hash])
                            
                            # Stop if we have enough candidates
                            if len(candidates) >= k * 3:  # Get more than k to account for duplicates
                                break
                        if len(candidates) >= k * 3:
                            break
                
                if len(candidates) >= k * 3:
                    break
        
        # Deduplicate candidates
        unique_candidates = []
        seen_chunk_ids = set()
        
        for chunk in candidates:
            chunk_id = id(chunk)
            if chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(chunk_id)
                unique_candidates.append(chunk)
        
        print(f"LSHIndex found {len(unique_candidates)} unique candidates")
        
        # If we still don't have enough candidates, but we have some data in the index
        # Fall back to a more exhaustive search only if we have less than k candidates
        if len(unique_candidates) < k and len(self.tables) > 0 and any(len(table) > 0 for table in self.tables):
            # We'll gather a sample of chunks from all tables, biased toward less common buckets
            # which are more likely to contain meaningful results
            print(f"LSHIndex: Falling back to broader search strategy")
            
            extra_candidates = []
            extra_chunk_ids = set(id(chunk) for chunk in unique_candidates)
            
            # Collect chunks from smaller buckets first (they're more specific/meaningful)
            all_buckets = []
            for ti in range(self.num_tables):
                for hash_val, chunks in self.tables[ti].items():
                    if hash_val not in hash_vals:  # Don't include already searched buckets
                        all_buckets.append((len(chunks), ti, hash_val))
            
            # Sort buckets by size (smallest first)
            all_buckets.sort()
            
            # Take chunks from smaller buckets until we have enough
            chunks_needed = max(k - len(unique_candidates), k)  # At least k more
            for _, ti, hash_val in all_buckets:
                for chunk in self.tables[ti][hash_val]:
                    chunk_id = id(chunk)
                    if chunk_id not in extra_chunk_ids:
                        extra_chunk_ids.add(chunk_id)
                        extra_candidates.append(chunk)
                        chunks_needed -= 1
                        if chunks_needed <= 0:
                            break
                if chunks_needed <= 0:
                    break
            
            print(f"LSHIndex: Added {len(extra_candidates)} extra candidates from smaller buckets")
            unique_candidates.extend(extra_candidates)
        
        # If we still don't have enough candidates, we'll return what we have
        if len(unique_candidates) < k:
            print(f"LSHIndex: Only found {len(unique_candidates)} candidates for requested k={k}")
            # Just sort the candidates we have by similarity and return them
            if self.normalize:
                dist_candidates = [
                    (-sum(q*v for q, v in zip(query, chunk.embedding)), chunk) 
                    for chunk in unique_candidates
                ]
            else:
                dist_candidates = [
                    (sum((q-v)**2 for q, v in zip(query, chunk.embedding)), chunk) 
                    for chunk in unique_candidates
                ]
            dist_candidates.sort()
            return [c for _, c in dist_candidates]
        
        if len(unique_candidates) > self.max_candidates:
            dist_candidates = []
            
            for chunk in unique_candidates:
                if self.normalize:
                    dist = -sum(q*v for q, v in zip(query, chunk.embedding))
                else:
                    dist = sum((q-v)**2 for q, v in zip(query, chunk.embedding))
                    
                dist_candidates.append((dist, chunk))
            
            dist_candidates.sort()
            unique_candidates = [c for _, c in dist_candidates[:self.max_candidates]]
            print(f"LSHIndex pruned to {len(unique_candidates)} candidates")
        
        results = LinearIndex(unique_candidates, normalize=self.normalize).query(query, k)
        print(f"LSHIndex returning {len(results)} results via LinearIndex")
        return results


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