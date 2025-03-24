from app.db.database import VectorDatabase

vector_db = VectorDatabase()

def get_db():
    """
    Dependency to get the database instance
    """
    return vector_db 