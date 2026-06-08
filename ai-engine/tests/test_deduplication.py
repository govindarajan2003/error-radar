from unittest.mock import patch
import pytest
from services.rag_service import insert_new_error

@patch("services.rag_service.get_embedding")
@patch("services.rag_service.update_occurrence_count")
@patch("services.rag_service.insert_error")
@patch("services.rag_service.find_duplicate_id")
def test_deduplication_logic_when_match_found(
    mock_find, 
    mock_insert,
    mock_update,
    mock_get_embedding
    ):
    mock_get_embedding.return_value = [0.1, 0.2, 0.3]
    mock_find.return_value = 999
    mock_update.return_value = True

    result = insert_new_error("test_msg", "test_trace", "test_trace", "test_service")

    mock_update.assert_called_once_with(999)
    mock_insert.assert_not_called()
    assert result == {"response": "Success"}

@patch("services.rag_service.get_embedding")
@patch("services.rag_service.insert_error")
@patch("services.rag_service.update_occurrence_count")
@patch("services.rag_service.find_duplicate_id")
def test_deduplication_inserts_new_record(
    mock_find, 
    mock_update, 
    mock_insert,
    mock_get_embedding
    ):
    mock_get_embedding.return_value = [0.1, 0.2, 0.3]
    mock_find.return_value = None
    mock_insert.return_value = 100

    result = insert_new_error("test_msg", "test_trace", "test_trace", "test_service")

    mock_update.assert_not_called()

    mock_insert.assert_called_once()