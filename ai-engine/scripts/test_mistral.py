from services.rag_service import generate_suggestion, find_similar_errors

err_log = "JWT token expired during user authentication request"
similar_cases = find_similar_errors(err_log)
response = generate_suggestion(err_log, similar_cases)