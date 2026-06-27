from sqlalchemy import text

from datetime import datetime, timezone

from core.database import engine

from typing import Optional


def find_similar_by_vector(query_vector_str: str, top_n: int, min_similarity: float, id: int | None = None) -> list[dict]:
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
    query = """
        SELECT
            id,
            message,
            sanitized_trace,
            service_name,
            past_fix,
            1 - (embedding <=> :query_vector) AS similarity_score
        FROM errors
        WHERE embedding IS NOT NULL
    """

    params = {
        "query_vector": query_vector_str,
        "top_n": top_n,
    }

    if id is not None:
        query += " AND id != :id"
        params["id"] = id

    query += """
        ORDER BY embedding <=> :query_vector ASC
        LIMIT :top_n
    """

    with engine.connect() as connection:
        result = connection.execute(text(query), params)

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
                occurrence_count,
                resolved,
                past_fix,
                created_at
            FROM errors
        """
        # Dynamically append the WHERE clause only when filtering
        # has been requested by the caller.
        params = {}
        if resolved is not None:
            sql_text += " WHERE resolved = :resolved "
            params['resolved'] = resolved

        sql_text += "ORDER BY last_seen_at DESC;"
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
                    "past_fix": row.past_fix,
                    "occurrence_count": row.occurrence_count,
                    "created_at":row.created_at,
                }
            )
        return errors

def update_past_fix(
        error_id: int,
        fix_description: str
) -> bool:
    """
    Updates an error record with a human-approved fix and 
    marks the error as resolved.

    Args:
        error_id (int): Unique identifier of the error record.
        fix_description (str): Resolution details provided by a user.
    
    Returns:
        bool: True if the record was updated successfully,
            False if no mmatching record exists. 
    """
    with engine.begin() as connection:
        query = text("""
            UPDATE errors 
            SET past_fix = :fix_description,
                resolved = :resolved
            WHERE id = :error_id
        """)
    
        result = connection.execute(query,{
            "fix_description": fix_description,
            "error_id": error_id,
            "resolved": "true"
        })

        return result.rowcount > 0
    
def insert_error(
        message: str,
        stack_trace: str,
        sanitized_trace: str,
        service_name: str,
        embedding: str
) -> int:
    """
    Persists a new error record in the database along with its
    vector embedding for similarity search.

    Args:
        message (str): Error message summary.
        stack_trace (str): Original stack trace.
        sanitized_trace (str): Normalized stack trace used for embedding.
        service_name (str): Source service that generated the error.
        embedding (str): Vector embedding representation of the error.
    Returns:
        int: Database-generated identifier of the newly created record.
    """
    with engine.begin() as connection:
        query = text(""" INSERT INTO errors (message, stack_trace, sanitized_trace, service_name,embedding)
            VALUES (:message, :stack_trace, :sanitized_trace, :service_name, :embedding)
            RETURNING id;
        """)
        id = connection.execute(query,{
            "message": message,
            "stack_trace": stack_trace,
            "sanitized_trace": sanitized_trace,
            "service_name": service_name,
            "embedding": embedding
        }).scalar()
    

def update_occurrence_count(
        error_id: int
) -> bool:
    """
    Increments the occurrence count of an existing error record
    and update its last-seen timestamp.

    Args:
        error_id (int): Unique identifier of the error record.
    
    Returns:
        bool: True if the record was updated successfully,
            False if no matching record exists.
    """
    with engine.begin() as connection:
        query = text("""
            UPDATE errors 
            SET occurrence_count = occurrence_count + 1,
                last_seen_at = :now
            WHERE id = :error_id 
        """)
        now = datetime.now(timezone.utc)
        result = connection.execute(query,{
            "error_id": error_id,
            "now": now
        })
        return result.rowcount > 0

def find_duplicate_id(
        query_vector_str:str,
        min_similarity: float
) -> int | None:
    """
    Finds the most similar error record based on vector similarity
    and returns its identifier if the similarity exceeds the 
    configured threshold.

    Args:
        query_vector_str (str): Vector embedding of the incoming error.
        min_similarity (float): Minimum similarity score required to 
            consider a record a duplicate.
    
    Returns:
        int | None:
            - Error Id when a matching record exceeds the threshold.
            - None when no suitable match is found.
    """
    with engine.connect() as connection:
        query = text("""
            SELECT id, 1 - (embedding <=> :query_vector) AS similarity FROM errors
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_vector ASC
            LIMIT 1
        """)
        result = connection.execute(query,{
            "query_vector": query_vector_str
        })
        similar_row = result.fetchone()
        if result and similar_row.similarity > min_similarity:
            return similar_row.id
        else:
            return None    

def total_error_count() -> int:
    """
    Retrieves the total number of error records stored in the database.
    
    Returns:
        int: Total number of records in the errors table.  
    """
    with engine.connect() as connection:
        query = text("""
            SELECT COUNT(*) FROM errors;
        """)
        result = connection.execute(query).scalar()
        return result
    
def unresolved_error_count():
    """
    Retrieves the total number of unresolved errors.
    
    Returns:
        int: Count of all unresolved errors in the table errors.    
    """
    with engine.connect() as connection:
        query = text("""
            SELECT COUNT(*) FROM errors 
            WHERE errors.resolved = false;
        """)
        result = connection.execute(query).scalar()
        return result
    
def most_occurred_error() -> dict:
    """
    Retrieves the error with most occurrence count.
    
    Returns:
        dict: Dictionary containing the error message and
    occurrence count of the most frequently occurring error.
    """
    with engine.connect() as connection:
        query = text("""
            SELECT message, occurrence_count FROM errors
            ORDER BY occurrence_count DESC 
            LIMIT 1;
        """)
        result = connection.execute(query).fetchone()
        if not result:
            return {
                "message": "no error found",
                "occurrence_count":  0
            }
        return {
            "message": result.message,
            "occurrence_count": result.occurrence_count
        }

def occurrence_count_in_interval(
        interval: int
) -> list:
    """
    Retrieves the number of errors created per day within the
    specified time interval.

    Args:
        interval (int): Number of days to include in the analysis.

    Returns:
        list: Collection of rows containing the date and the
        corresponding error count for that day.
    """
    with engine.connect() as connection:
        query = text("""
            SELECT DATE(created_at) AS date, COUNT(*) as error_count FROM errors
            WHERE created_at >= NOW() - (:interval * INTERVAL '1 day')
            GROUP BY date
            ORDER BY date ASC;
        """)
        rows = connection.execute(query,{
            "interval": interval
        }).fetchall()

        return rows
        