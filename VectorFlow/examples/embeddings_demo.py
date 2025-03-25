#!/usr/bin/env python
"""
Demo script for the Cohere embeddings service in VectorFlow.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.embeddings import generate_cohere_embeddings

load_dotenv()

async def main():
    if not os.environ.get("COHERE_API_KEY"):
        print("Error: COHERE_API_KEY environment variable is not set")
        print("Please set it in a .env file or in your environment")
        sys.exit(1)
    
    texts = [
        "This is a simple test of the embeddings service",
        "Vector embeddings are useful for many NLP tasks",
        "Semantic search relies on good quality embeddings"
    ]
    
    print(f"Generating embeddings for {len(texts)} texts...")
    
    try:
        embeddings = await generate_cohere_embeddings(texts)
        
        print("\nEmbeddings generated successfully!")
        print(f"Embedding dimension: {len(embeddings[0])}")
        
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            print(f"\nText {i+1}: '{text}'")
            print(f"Embedding (first 5 dimensions): {embedding[:5]}...")
        
    except Exception as e:
        print(f"Error generating embeddings: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 