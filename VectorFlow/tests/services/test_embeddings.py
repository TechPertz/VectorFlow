import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from app.services.embeddings import generate_cohere_embeddings

pytestmark = pytest.mark.asyncio

@pytest.mark.unit
@pytest.mark.mock
class TestEmbeddingsUnit:
    """Unit tests for the Cohere embeddings service using mocks"""
    
    async def test_missing_api_key(self):
        """Test behavior when the API key is not set"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                await generate_cohere_embeddings(["test text"])
            assert "COHERE_API_KEY environment variable is not set" in str(exc_info.value)
    
    async def test_generate_embeddings_success(self):
        """Test embeddings generation with mocked Cohere response"""
        test_texts = ["This is a test", "Another test text"]
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.embeddings = mock_embeddings
        mock_client.embed.return_value = mock_response
        
        with patch('cohere.Client', return_value=mock_client):
            with patch.dict(os.environ, {"COHERE_API_KEY": "dummy_key"}):
                embeddings = await generate_cohere_embeddings(test_texts)
                
                assert embeddings == mock_embeddings
                mock_client.embed.assert_called_once()
                
                call_args = mock_client.embed.call_args[1]
                assert call_args["texts"] == test_texts
                assert call_args["model"] == "embed-english-v3.0"
                assert call_args["input_type"] == "search_query"
    
    async def test_generate_embeddings_error_handling(self):
        """Test error handling when the Cohere API call fails"""
        mock_client = MagicMock()
        mock_client.embed.side_effect = Exception("API error")
        
        with patch('cohere.Client', return_value=mock_client):
            with patch.dict(os.environ, {"COHERE_API_KEY": "dummy_key"}):
                with pytest.raises(Exception) as exc_info:
                    await generate_cohere_embeddings(["test text"])
                assert "API error" in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.real
class TestEmbeddingsIntegration:
    """Integration tests for the Cohere embeddings service using real API calls"""
    
    @pytest.mark.skipif(not os.environ.get("COHERE_API_KEY"), 
                      reason="COHERE_API_KEY not set")
    async def test_integration_single_text(self):
        """Integration test with actual Cohere API - single text"""
        test_texts = ["This is an integration test"]
        
        embeddings = await generate_cohere_embeddings(test_texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 1
        assert isinstance(embeddings[0], list)
        assert len(embeddings[0]) > 0
        assert all(isinstance(val, float) for val in embeddings[0])
    
    @pytest.mark.skipif(not os.environ.get("COHERE_API_KEY"), 
                      reason="COHERE_API_KEY not set")
    async def test_integration_multiple_texts(self):
        """Integration test with actual Cohere API - multiple texts"""
        test_texts = [
            "First test text for integration testing",
            "Second test text with different content",
            "Third test text to ensure batch processing works"
        ]
        
        embeddings = await generate_cohere_embeddings(test_texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == len(test_texts)
        
        embedding_dim = len(embeddings[0])
        assert all(len(emb) == embedding_dim for emb in embeddings)
        
        assert embeddings[0] != embeddings[1] 