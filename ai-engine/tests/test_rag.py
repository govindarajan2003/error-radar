import pytest
from unittest.mock import patch, MagicMock
from services.rag_service import find_similar_errors
from services.embedding_service import OllamaUnavailableError

class FakeRow:
    def __init__(self, id, message, sanitized_trace, service_name, similarity_score):
        self.id = id
        self.message = message
        self.sanitized_trace = sanitized_trace
        self.service_name = service_name
        self.similarity_score = similarity_score

@patch('services.rag_service.engine.connect')
@patch('services.rag_service.get_embedding')
def test_happy_path(mock_embedding, mock_connect):
    mock_embedding.return_value = [0.1] * 768
    mock_db_result = MagicMock()
    mock_db_result.fetchall.return_value = [
        FakeRow(1, "Error 1", "Trace 1", "Service A", 0.95432),
        FakeRow(2, "Error 2", "Trace 2", "Service A", 0.85111),
        FakeRow(3, "Error 3", "Trace 3", "Service A", 0.76222)
    ]
    mock_connect.return_value.__enter__.return_value.execute.return_value = mock_db_result

    results = find_similar_errors("Test error")

    assert len(results) == 3
    assert results[0]["id"] == 1
    assert results[0]["similarity_score"] == 0.9543

@patch('services.rag_service.engine.connect')
@patch('services.rag_service.get_embedding')
def test_empty_result(mock_embedding, mock_connect):
    mock_embedding.return_value = [0.1] * 768
    mock_db_result = MagicMock()
    mock_db_result.fetchall.return_value = []
    mock_connect.return_value.__enter__.return_value.execute.return_value = mock_db_result

    results = find_similar_errors("Test error")

    assert results == []

@patch('services.rag_service.engine.connect')
@patch('services.rag_service.get_embedding')
def test_similarity_threshold_filtering(mock_embedding, mock_connect):
    mock_embedding.return_value = [0.1] * 768
    mock_db_result = MagicMock()
    mock_db_result.fetchall.return_value = [
        FakeRow(1, "Error 1", "Trace 1", "Service A", 0.95432),
        FakeRow(2, "Error 2", "Trace 2", "Service A", 0.85111),
        FakeRow(3, "Error 3", "Trace 3", "Service A", 0.43222)
    ]
    mock_connect.return_value.__enter__.return_value.execute.return_value = mock_db_result

    results = find_similar_errors("Test error", min_similarity = 0.7)

    assert len(results) == 2

@patch('services.rag_service.get_embedding')
def test_embedding_failure_propagates(mock_get_embedding):
    mock_get_embedding.side_effect = OllamaUnavailableError("Ollama is down")
    with pytest.raises(OllamaUnavailableError):
        find_similar_errors("test error query")