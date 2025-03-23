from typing import List
from .models import Chunk

class LinearIndex:
    def __init__(self):
        self.chunks: List[Chunk] = []

    def build(self, chunks: List[Chunk]):
        self.chunks = chunks

    def query(self, query_embedding: List[float], k: int) -> List[Chunk]:
        distances = []
        for chunk in self.chunks:
            dist = sum((x - y) ** 2 for x, y in zip(query_embedding, chunk.embedding)) ** 0.5
            distances.append((dist, chunk))
        distances.sort(key=lambda x: x[0])
        return [chunk for _, chunk in distances[:k]]