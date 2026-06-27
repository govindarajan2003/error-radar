import json
import requests

API_URL = "http://127.0.0.1:8000/query"

test_errors = [

    # 1. Null Pointer
    {
        "error_log": 'java.lang.NullPointerException: Cannot invoke "Customer.getEmail()" because "customer" is null at EmailProcessor.java:67'
    },

    # 2. Database Pool Exhaustion
    {
        "error_log": "sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow reached while processing inventory updates"
    },

    # 3. Database Timeout
    {
        "error_log": "org.postgresql.util.PSQLException: Operation timed out while acquiring database connection"
    },

    # 4. Authentication
    {
        "error_log": "io.jsonwebtoken.ExpiredJwtException: JWT token expired during API authentication"
    },

    # 5. Authentication Signature Failure
    {
        "error_log": "io.jsonwebtoken.SignatureException: Token signature validation failed for incoming request"
    },

    # 6. Resource Not Found
    {
        "error_log": "com.app.CustomerNotFoundException: Customer id 5012 does not exist"
    },

    # 7. Out Of Memory
    {
        "error_log": "java.lang.OutOfMemoryError: Java heap space while generating analytics report"
    },

    # 8. Native Thread Exhaustion
    {
        "error_log": "java.lang.OutOfMemoryError: unable to create new native thread in worker executor"
    },

    # 9. Type Conversion
    {
        "error_log": "java.lang.ClassCastException: java.lang.Long cannot be cast to java.lang.String at UserMapper.java:91"
    },

    # 10. Recursive Overflow
    {
        "error_log": "java.lang.StackOverflowError at TreeTraversalService.java:121 caused by recursive node processing"
    }

]


def run_simulation():
    print("Simulation of production API")
    for test_error in test_errors:
        payload = {
            "id": -1,
            "error_log": test_error["error_log"]
        }
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