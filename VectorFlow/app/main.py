from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router

app = FastAPI(
    title="VectorFlow",
    description="A vector database and similarity search API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

app.include_router(api_router)

@app.get("/")
async def root():
    """
    Root endpoint - health check
    """
    return {"status": "healthy", "message": "VectorFlow API is running"}