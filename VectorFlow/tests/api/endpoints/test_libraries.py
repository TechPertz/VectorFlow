import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import asyncio

from app.main import app
from app.models import Library, LibraryMetadata, Document, DocumentMetadata, Chunk, ChunkMetadata
from app.services.indexes import LinearIndex

pytestmark = pytest.mark.asyncio

@pytest.fixture
def test_client():
    """Return a TestClient for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def mock_library():
    """Create a mock library with sample data and index."""

    chunks = []
    for i in range(5):
        chunk = Chunk(
            id=uuid4(),
            text=f"Sample text {i}",
            embedding=[0.1 * i, 0.2 * i, 0.3 * i, 0.4 * i],
            metadata=ChunkMetadata(name=f"chunk_{i}")
        )
        chunks.append(chunk)
    
    doc = Document(
        id=uuid4(),
        metadata=DocumentMetadata(title="Test Document", author="Test Author"),
        chunks=chunks
    )
    
    lib = Library(
        id=uuid4(),
        name="Test Library",
        metadata=LibraryMetadata(description="Test Description"),
        documents=[doc],
        index=LinearIndex(chunks)
    )
    
    return lib

class AsyncMock(MagicMock):
    """A MagicMock that works with async functions."""
    
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)
    
    def __await__(self):
        return self().__await__()

@pytest.mark.unit
@pytest.mark.mock
class TestLibrariesEndpointUnit:
    """Unit tests for the libraries endpoint using mocks"""
    
    async def test_text_search_endpoint(self, test_client, mock_library):
        """Test the text-search endpoint with mocked database and embeddings."""

        mock_db = MagicMock()
        mock_db.get_library = AsyncMock(return_value=mock_library)
        
        with patch("app.core.deps.vector_db", mock_db), \
             patch("app.api.endpoints.libraries.generate_cohere_embeddings", return_value=[
                 [0.1, 0.2, 0.3, 0.4]
             ]):

            for k in [1, 2, 3, 5]:
                response = test_client.post(
                    f"/libraries/{mock_library.id}/text-search?k={k}",
                    json={"text": "Sample query"}
                )
                
                assert response.status_code == 200, f"Response: {response.json()}"
                data = response.json()
                
                assert "query_text" in data
                assert "results_count" in data
                assert "results" in data
                
                expected_count = min(k, len(mock_library.documents[0].chunks))
                assert data["results_count"] == expected_count
                assert len(data["results"]) == expected_count
                
                for result in data["results"]:
                    assert "id" in result
                    assert "text" in result
                    assert "metadata" in result

    async def test_text_search_validation(self, test_client):
        """Test validation in the text-search endpoint."""
        
        library_id = uuid4()
        
        response = test_client.post(
            f"/libraries/{library_id}/text-search",
            json={"not_text": "This should fail"}
        )
        assert response.status_code == 400
        assert "text" in response.json()["detail"]
        
        response = test_client.post(
            f"/libraries/{library_id}/text-search",
            json={"text": ""}
        )
        assert response.status_code in [400, 422]
        if response.status_code == 400:
            assert "non-empty string" in response.json()["detail"]
        else:
            assert "text" in str(response.json())
        
        response = test_client.post(
            f"/libraries/{library_id}/text-search",
            json={"text": 123}
        )
        assert response.status_code == 422
        assert "text" in str(response.json())
    
    async def test_library_not_found(self, test_client):
        """Test the case when the library is not found."""
        mock_db = MagicMock()
        mock_db.get_library = AsyncMock(return_value=None)
        
        with patch("app.core.deps.vector_db", mock_db):
            response = test_client.post(
                f"/libraries/{uuid4()}/text-search",
                json={"text": "Sample query"}
            )
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    async def test_library_not_indexed(self, test_client, mock_library):
        """Test the case when the library is not indexed."""

        from app.models import Library, LibraryMetadata
        lib = Library(
            id=uuid4(),
            name="Test Library No Index",
            metadata=LibraryMetadata(description="Test Description"),
            documents=mock_library.documents,
            index=None
        )

        mock_db = MagicMock()
        mock_db.get_library = AsyncMock(return_value=lib)
        
        with patch("app.core.deps.vector_db", mock_db):
            response = test_client.post(
                f"/libraries/{lib.id}/text-search",
                json={"text": "Sample query"}
            )
            
            assert response.status_code == 400
            assert "not indexed" in response.json()["detail"].lower() 