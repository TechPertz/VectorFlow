import heapq
from typing import List
from .models import Chunk

class LinearIndex:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks

    def query(self, query: List[float], k: int) -> List[Chunk]:
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
        if algorithm == "linear":
            return LinearIndex(chunks)
        # TODO: Add other algorithms
        raise ValueError(f"Unknown algorithm: {algorithm}")