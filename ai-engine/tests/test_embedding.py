from unittest.mock import patch
import requests
import pytest
from  services.embedding_service import embed_error, get_embedding, OllamaUnavailableError, OllamaTimeoutError, EmbeddingDimensionError

def test_connection_error():
    with patch('services.embedding_service.requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError
        with pytest.raises(OllamaUnavailableError) as exc:
            embed_error(1, "govind")

    assert str(exc.value) == "Ollama daemon is unreachable!"

def test_timeout_error():
    with patch('services.embedding_service.requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout
        with pytest.raises(OllamaTimeoutError) as exc:
            embed_error(1, "test message")

    assert str(exc.value) == "Embedding request timed out after multiple attempts!"
    assert mock_post.call_count == 3

def test_different_embedding_length_error():
    with patch('services.embedding_service.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "embeddings": [[0.1] * 788]
        }
        with pytest.raises(EmbeddingDimensionError) as exc:
            vector = get_embedding("test message")
    assert str(exc.value) == "Expected 768 dimensions, got 788 dimensions!"

def test_successful_embedding():
    with patch('services.embedding_service.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "embeddings": [[0.1] * 768]
        }
        vector = get_embedding("test message")
        assert len(vector) == 768

def test_invalid_status_code():
    with patch('services.embedding_service.requests.post') as mock_post:
        mock_post.return_value.status_code = 500
        
        with pytest.raises(OllamaUnavailableError) as exc:
            embed_error(1, "hello")
    assert "Ollama returned unexpected status code 500" in str(exc.value)
        

