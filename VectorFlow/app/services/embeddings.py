import os
from dotenv import load_dotenv  
import cohere
from typing import List

load_dotenv()

async def generate_cohere_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts using Cohere's API.
    """
    api_key = os.environ.get("COHERE_API_KEY")
    if not api_key:
        raise ValueError("COHERE_API_KEY environment variable is not set")
    
    co = cohere.Client(api_key)
    
    response = co.embed(
        texts=texts,
        model="embed-english-v3.0",
        input_type="search_query"
    )
    
    return response.embeddings 