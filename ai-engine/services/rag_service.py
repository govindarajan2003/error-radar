import os
from dotenv import load_dotenv
from sqlalchemy import text, create_engine
from services.embedding_service import get_embedding

# Loads environment values
load_dotenv()

# Creates engine for the database 
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise EnvironmentError("Database URL not set, check the .env file")
engine = create_engine(database_url)

def find_similar_errors(
        query_text: str,
        top_n: int = int(os.getenv('TOP_N_RESULTS', 5)),
        min_similarity: float = float(os.getenv('SIMILARITY_THRESHOLD', 0.70))
) -> list[dict]:
    """
    Executes a semantic similarity search using pgvector's cosine distance operator.
    
    Args:
        query_text (str): The incoming error stack trace or message.
        top_n (int): Max results to return. Defaults to env config.
        min_similarity (float): The threshold for filtering weak matches. Defaults to env config.
        
    Returns:
        list[dict]: A list of historical errors that semantically match the query, 
                    including their calculated similarity score (1 - distance).
    """
    # Fallback to Environment Variables if explicit parameters aren't passed
    # Wrapping in int() and float() ensures string configs are cast correctly.
    if top_n is None:
        top_n = int(os.getenv('TOP_N_RESULTS', 5))
    if min_similarity is None:
        min_similarity = float(os.getenv('SIMILARITY_THRESHOLD', 0.70))
    
    # Convert the incoming string to a 768-dimensional vector via local LLM
    vector = get_embedding(query_text)

    # Format strictly for pgvector compatibility (e.g., '[0.1, 0.2, ...]')
    query_vector = "[" + "," .join(str(v) for v in vector) + "]"
    
    # Execute Read-Only Transaction
    with engine.connect() as connection:
        query = text("""
            SELECT
                id,
                message,
                sanitized_trace,
                service_name,
                1 - (embedding <=> :query_vector) AS similarity_score
            FROM errors
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_vector ASC
            LIMIT :top_n
        """)
        result = connection.execute(query,{
            'top_n': top_n,
            'query_vector': query_vector
        })
        
        rows = result.fetchall()
        results_list = []
        # Parse, Filter, and Format Results
        for row in rows:
            if row.similarity_score >= min_similarity:
                match = {
                    "id": row.id,
                    "message": row.message,
                    "sanitized_trace": row.sanitized_trace,
                    "service_name": row.service_name,
                    "similarity_score": round(row.similarity_score, 4)
                }
                results_list.append(match)
    return results_list

