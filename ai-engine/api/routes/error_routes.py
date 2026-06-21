from typing import Optional
from fastapi import APIRouter, HTTPException
from services.stats_service import stats_service, daily_stats_service
from services.rag_service import get_all_errors, update_human_fix_service, insert_new_error
from schemas.error_schemas import FixRequest, LogErrorRequest
from exceptions.database_exceptions import ErrorLogNotFoundError
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(
    prefix="/errors",
    tags=["Errors"]
)


@router.get("")
def list_errors(resolved: Optional[bool] = None):
    """
    Retrieve stored error records.

    Returns all errors ordered from newest to oldest. Optionally filters
    results by their resolution status.

    Args:
        resolved (Optional[bool]):
            Filter criteria for the error status:
            - True: return only resolved errors
            - False: return only unresolved errors
            - None: return all errors

    Returns:
        dict:
            Standardized API response containing the requested error records.

            Example:
            {
                "status": "success",
                "data": [...]
            }

    Raises:
        HTTPException:
            Returned with status code 500 if an unexpected server-side
            error occurs while retrieving records.
    """
    try:
        errors = get_all_errors(resolved)

        return {
            "status": "success",
            "data": errors
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
@router.post("/{error_id}/fix")
def mark_resolved(
    error_id: int,
    error_fix: FixRequest
    ):
    """
    Marks an existing error log as resolved by storing the provided
    human-approved fix description.

    Args:
        error_id (int): unique identifier of the error record.
        error_fix (FixRequest): Request payload containing the fix description.

    Returns:
        dict: Success response when the fix is stored successfully.

    Raises:
        HTTPException:
            - 404 if the error record does not exist.
            - 400 if the provided fix data is invalid.
            - 500 for unexpected server errors.
    """
    try:
        update_human_fix_service(error_id, error_fix.fix_description)
        return {
            "status": "success"
        }
    except ErrorLogNotFoundError:
        raise HTTPException(
            status_code=404, 
            detail="The Id was not found in the Database."
            )
    except ValueError as val_err:
        raise HTTPException(
            status_code=400,
            detail=str(val_err)
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error.")

@router.post("/log-error")
def log_new_error(
        new_error: LogErrorRequest
):
    """
    Creates a new error log entry and stored its associated metadata,
    including stack trace information and service details.

    Args:
        new_error (LogErrorRequest): Error payload received from the client.
    
    Returns:
        dict: success response indicating that the error was
    processed successfully.
    
    Raises:
        HTTPException:
            - 500 for unexpected sertver errors.
    """
    try:
        insert_new_error(
            new_error.message,
            new_error.stack_trace,
            new_error.service_name
        )
        return {
            "response": "success"
        }
    except Exception as e:
        raise 

@router.get("/stats")
def check_stats():
    """
    Retrieves aggregate error statistics for the application.
    Returns:
        dict: Returns a standardized JSON structured with
            - total_count: Total number of errors.
            - unresolved_count: Total number of unresolved errors.
            - top_error: Error with the highest occurrence count.

    """
    try:
        return stats_service()
    except HTTPException as e:
        raise HTTPException(status_code=400)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500)

@router.get("/stats/daily")
def daily_stats(
    interval: int  = 14
):
    """
    Endpoint to view statistics about the application for a particular interval.
    
    Returns:
        list: Collection of daily error counts grouped by date.
    """
    try:
        return daily_stats_service(interval)
    except HTTPException as e:
        raise HTTPException(status_code=400)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500)
