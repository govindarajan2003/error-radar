import json
import requests

API_URL = "http://127.0.0.1:8000/query"

test_error = "sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflowed during inventory transaction"

payload = {
    "error_log": test_error
}

def run_simulation():
    print("Simulation of production API")
    print(f"Error: {test_error}\n")
    print("Sending to Zero-Trust TraceRAG API...")

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()

        data = response.json()
        print("API response received")
        print("Similar historic errors")
        for case in data.get("similar_cases"):
            print(f"[{case['similarity_score']}] {case['message']} (Service: {case['service_name']})")
        print("\n--- AI DIAGNOSIS ---")
        print(json.dumps(data.get("response", {}), indent=2))
    except Exception as e:
        print(f"API Call Failed: {e}")

if __name__ == "__main__":
    run_simulation()