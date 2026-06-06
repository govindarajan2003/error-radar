from typing import Optional

from fastapi import APIRouter, HTTPException

from services.rag_service import get_all_errors

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