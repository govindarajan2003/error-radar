from services.rag_service import find_similar_errors

queries = {
    "NullPointerException in CartService line 55 while processing checkout request",
    "PostgreSQL database connection timeout during payment transaction",
    "JWT token expired during user authentication request",
    "OrderNotFoundException: Order with id 4502 not found",
    "java.lang.OutOfMemoryError: Java heap space exhausted during report generation",
    "The flux capacitor overheated during time travel"
}

for query in queries:
    print(f"Current query - {query}")
    results = find_similar_errors(query, 5, 0.0)
    for result in results:
        print(f"Result: {result['similarity_score']} — {result['message']} ({result['service_name']})")
