from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """
    Request payload for error analysis.
    """

    error_log: str = Field(
        description="Raw error message, stack trace, or log entry to analyze."
    )


class FixRequest(BaseModel):
    """
    Request payload for recording an error resolution.
    """

    fix_description: str = Field(
        description="Description of the fix applied to resolve the error."
    )