import requests
from sqlalchemy import text
from core.database import engine 

API_URL = "http://127.0.0.1:8000"

def get_error_id_from_db(message):
    """Helper to find the ID of the record we just inserted."""
    with engine.connect() as conn:
        query = text("SELECT id FROM errors WHERE message = :msg ORDER BY created_at DESC LIMIT 1")
        result = conn.execute(query, {"msg": message}).scalar()
        return result

def run_dedup_verification():
    print("Starting deduplication verification script...")
    
    payload = {
        "message": "Duplicate test",
        "stack_trace": "test_trace",
        "service_name": "test_service",
        "sanitized_trace": "test_trace" # Ensure this matches your schema
    }

    try:
        # 1. First call
        print("Calling log-error first time...")
        response_1 = requests.post(f"{API_URL}/errors/log-error", json=payload)
        response_1.raise_for_status()
        
        # Manually fetch the ID from DB
        id_1 = get_error_id_from_db(payload["message"])
        print(f"First call inserted record ID: {id_1}")

        # 2. Second call (Duplicate)
        print("Calling log-error second time (duplicate)...")
        response_2 = requests.post(f"{API_URL}/errors/log-error", json=payload)
        response_2.raise_for_status()
        
        # Fetch the ID again
        id_2 = get_error_id_from_db(payload["message"])
        print(f"Second call matched record ID: {id_2}")

        # 3. Verify ID matches
        assert id_1 == id_2, f"Deduplication failed! Expected ID {id_1}, got {id_2}"
        print("Verification: IDs match (Deduplication worked).")

        # 4. Verify Occurrence Count
        with engine.connect() as conn:
            query = text("SELECT occurrence_count FROM errors WHERE id = :id")
            count = conn.execute(query, {"id": id_1}).scalar()
            
            assert count == 2, f"Verification failed! Expected occurrence_count 2, got {count}"
            print(f"Verification: Occurrence count is {count}.")

        # 5. Cleanup
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM errors WHERE id = :id"), {"id": id_1})
        print("Cleanup: Test record deleted.")
        
        print("\nSUCCESS: Deduplication test passed!")

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        # Ensure cleanup runs
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM errors WHERE id = :id"), {"id": id_1})
        except: pass

if __name__ == "__main__":
    run_dedup_verification()