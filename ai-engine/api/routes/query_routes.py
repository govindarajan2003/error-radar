from fastapi import APIRouter, HTTPException

from schemas.error_schemas import QueryRequest
from services.rag_service import (
    find_similar_errors,
    generate_suggestion,
)

router = APIRouter(
    prefix="/query",
    tags=["Query"]
)


@router.post("")
def analyze_error(query: QueryRequest):
    """
    Analyze a newly submitted error log.

    The endpoint performs retrieval-augmented generation (RAG) by first
    locating historically similar incidents and then using those results
    as context for the LLM to generate a root-cause analysis and
    recommended remediation steps.

    Args:
        query (QueryRequest):
            Request payload containing the incoming error log.

    Returns:
        dict:
            A response containing:

            - similar_cases: Historical errors retrieved from the vector database.
            - response: LLM-generated diagnosis including root cause,
              suggested fix, and confidence score.

            Example:
            {
                "similar_cases": [...],
                "response": {
                    "root_cause": "...",
                    "suggested_fix": "...",
                    "confidence": 0.72
                }
            }

    Raises:
        HTTPException:
            Returned with status code 500 if an unexpected error occurs
            during retrieval or diagnosis generation.
    """
    try:
        # Extract the raw error log submitted by the client.
        err_log = query.error_log

        # Retrieve historically similar incidents from the vector store.
        similar_cases = find_similar_errors(err_log)

        # Generate a diagnosis using the incoming error and retrieved context.
        response = generate_suggestion(
            err_log,
            similar_cases
        )

        return {
            "similar_cases": similar_cases,
            "response": response
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )