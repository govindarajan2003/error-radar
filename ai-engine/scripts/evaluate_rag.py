from services.rag_service import find_similar_errors 


def run_evaluation():
    test_set = [
        {"id": 1, "expected": "NullPointerException", "query": 'java.lang.NullPointerException: Cannot invoke "Customer.getEmail()" because "customer" is null at NotificationService.java:54'},
        {"id": 2, "expected": "NullPointerException", "query": 'Application crashed while processing checkout request. Attempted to access payment details from an uninitialized request object.'},
        {"id": 3, "expected": "Database Connection / Timeout", "query": 'TimeoutError: Failed to acquire database connection from pool after waiting 30000ms during order retrieval.'},
        {"id": 4, "expected": "Database Connection / Timeout", "query": 'org.postgresql.util.PSQLException: Database server did not respond before connection timeout expired.'},
        {"id": 5, "expected": "JWT / Authentication", "query": 'AuthenticationException: Bearer token signature validation failed. Access denied for protected endpoint.'},
        {"id": 6, "expected": "JWT / Authentication", "query": 'Unauthorized request received. JWT token expired and user session could not be verified.'},
        {"id": 7, "expected": "Resource Not Found", "query": 'UserProfileNotFoundException: No profile exists for userId=78291 while fetching account details.'},
        {"id": 8, "expected": "OutOfMemoryError", "query": 'java.lang.OutOfMemoryError: Java heap space exhausted while generating monthly analytics report.'},
        {"id": 9, "expected": "Ambiguous (Auth/DB/NotFound)", "query": 'Failed to load authenticated user information because account record could not be retrieved from database.'},
        {"id": 10, "expected": "Unrelated (Should be Empty)", "query": 'Redis cache eviction policy triggered after memory threshold exceeded for session store.'}
    ]   
    print("--- STARTING P@1 EVALUATION ---\n")
    
    correct_count = 0
    
    for test in test_set:
        print(f"Test ID: {test['id']}")
        print(f"Query: {test['query']}")
        print(f"Expected: {test['expected']}")

        results = find_similar_errors(test['query'])
        if results:
                top_result = results[0]
                print(f"Top Match: {top_result['message']} (Score: {top_result['similarity_score']:.4f})")
        else:
            print("Top Match: NONE (or below threshold)")
            
        print("-" * 20)
        judgment = input("Is this a PASS? (y/n): ").strip().lower()
        
        if judgment == 'y':
            correct_count += 1
            print("Status: PASS\n" + "="*40 + "\n")
        else:
            print("Status: FAIL\n" + "="*40 + "\n")

    # Final Calculation
    p_at_1 = correct_count / len(test_set)
    print("\n--- FINAL RESULTS ---")
    print(f"Correct: {correct_count}/{len(test_set)}")
    print(f"P@1 Score: {p_at_1:.2f}")

if __name__ == "__main__":
    run_evaluation()