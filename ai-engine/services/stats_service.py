from repositories.error_repo import total_error_count, unresolved_error_count,most_occurred_error, occurrence_count_in_interval
from sqlalchemy.exc import SQLAlchemyError

def stats_service():
    """
    Retrieves aggregate statistics about stored error records.

    Returns:
        dict: Summary statistics containing:
            - total: Total number of recorded errors.
            - unresolved: Total number of unresolved errors.
            - top_error: Error with the highest occurrence count.

    Raises:
        SQLAlchemyError: If a database operation fails.
    """
    try:
        total_count = total_error_count()
        unresolved_count = unresolved_error_count()
        top_error = most_occurred_error()
        return {
            "total":total_count,
            "unresolved":unresolved_count,
            "top_error": top_error
        }
    except SQLAlchemyError as e:
        print(f"Database error {e}")
        raise e

def daily_stats_service(
        interval: int 
):
    """
    Retrieves daily error occurrence statistics for a specified
    time interval.

    Args:
        interval (int): Number of days to include in the analysis.

    Returns:
        list: Collection of dictionaries containing:
            - date: Calendar date.
            - count: Number of errors created on that date.

    Raises:
        SQLAlchemyError: If a database operation fails.
    """
    try:
        rows = occurrence_count_in_interval(interval)
        result = []
        for row in rows:
            result.append(
                {
                    "date": row.date,
                    "count": row.error_count
                }
            )
        return result
    except SQLAlchemyError as e:
        raise e
    
        
    