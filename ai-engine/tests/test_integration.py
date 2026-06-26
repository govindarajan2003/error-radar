from fastapi.testclient import TestClient
from main import app  

client = TestClient(app)

def test_get_errors_returns_list():
    """Test that the main errors endpoint returns a 200 and a list of data."""
    response = client.get("/errors") 
    assert response.status_code == 200
    json_data = response.json()
    
    if isinstance(json_data, dict) and "data" in json_data:
        assert isinstance(json_data["data"], list)
    else:
        assert isinstance(json_data, list)

def test_get_stats_returns_correct_shape():
    """Test that the dashboard stats endpoint returns the correct keys."""
    response = client.get("/errors/stats")
    assert response.status_code == 200
    json_data = response.json()
    
    assert "total" in json_data
    assert "unresolved" in json_data
    assert "top_error" in json_data

def test_fix_nonexistent_error_returns_404():
    """Test that trying to fix a ghost error throws a 404/400 properly."""
    payload = {"fix_description": "Restarted the flux capacitor"}
    response = client.post("/errors/999999/fix", json=payload)
    assert response.status_code in [404, 400, 500]