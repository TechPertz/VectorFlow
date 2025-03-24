import heapq
from typing import List
from app.models import Chunk

class LinearIndex:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks

    def query(self, query: List[float], k: int) -> List[Chunk]:
        """
        Find the k closest chunks to the query vector using Euclidean distance
        """
        heap = []
        for chunk in self.chunks:
            dist = sum((x - y)**2 for x, y in zip(query, chunk.embedding))
            heapq.heappush(heap, (-dist, chunk))
            if len(heap) > k:
                heapq.heappop(heap)
        return [c for _, c in sorted(heap, reverse=True)]

# TODO: Add other algorithms

class Indexer:
    @staticmethod
    def create_index(chunks: List[Chunk], algorithm: str):
        """
        Factory method to create the appropriate index based on the algorithm name
        """
        if algorithm == "linear":
            return LinearIndex(chunks)
        # TODO: Add other algorithms
        raise ValueError(f"Unknown algorithm: {algorithm}") 