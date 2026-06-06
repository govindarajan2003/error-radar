from sqlalchemy import text

from core.database import engine

from typing import Optional

def find_similar_by_vector(query_vector_str: str, top_n: int, min_similarity: float) -> list[dict]:
    """
    Retrieve historically similar errors using pgvector similarity search.

    The query compares the supplied embedding against stored error embeddings
    and returns the most relevant matches ordered by vector distance. Results
    below the configured similarity threshold are discarded.

    Args:
        query_vector_str (str):
            Embedding vector formatted for pgvector comparison.

        top_n (int):
            Maximum number of candidate matches to retrieve from the database.

        min_similarity (float):
            Minimum similarity score required for a result to be included
            in the final response.

    Returns:
        list[dict]:
            Collection of similar historical errors containing metadata,
            previous fixes, and similarity scores.
    """
    # Calculate cosine similarity using pgvector distance operators.
    # Higher similarity scores indicate a closer semantic match.
    with engine.connect() as connection:
        query = text("""
            SELECT id, message, sanitized_trace, service_name, past_fix,
                   1 - (embedding <=> :query_vector) AS similarity_score
            FROM errors
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_vector ASC
            LIMIT :top_n
        """)
        result = connection.execute(query, {'top_n': top_n, 'query_vector': query_vector_str})
        
        results_list = []
        for row in result.fetchall():
            if row.similarity_score >= min_similarity:
                results_list.append({
                    "id": row.id,
                    "message": row.message,
                    "sanitized_trace": row.sanitized_trace,
                    "service_name": row.service_name,
                    "past_fix": row.past_fix,
                    "similarity_score": round(row.similarity_score, 4)
                })
        return results_list

def get_all_errors_from_db(resolved: Optional[bool] = None) -> list[dict]:
    """
    Retrieve stored error records from the error ledger.

    Results are returned in reverse chronological order so that the
    most recently ingested incidents appear first. Optionally filters
    records by resolution status.

    Args:
        resolved (Optional[bool]):
            Resolution-state filter.

            - True: return only resolved errors
            - False: return only unresolved errors
            - None: return all errors

    Returns:
        list[dict]:
            Error records matching the requested filter criteria.
    """
    with engine.connect() as connection:
        sql_text = """
            SELECT
                id,
                message,
                sanitized_trace,
                service_name,
                resolved,
                created_at
            FROM errors
        """
        # Dynamically append the WHERE clause only when filtering
        # has been requested by the caller.
        params = {}
        if resolved is not None:
            sql_text += " WHERE resolved = :resolved "
            params['resolved'] = resolved

        sql_text += "ORDER BY created_at DESC;"
        query = text(sql_text)
        
        result = connection.execute(query, params)
        rows = result.fetchall()
            
        # Convert SQLAlchemy Row objects into plain dictionaries to
        # provide a consistent API response format.
        errors = []
        for row in rows:
            errors.append(
                {
                    "id": row.id,
                    "message": row.message,
                    "sanitized_trace": row.sanitized_trace,
                    "service_name":row.service_name,
                    "resolved":row.resolved,
                    "created_at":row.created_at,
                }
            )
        return errors

