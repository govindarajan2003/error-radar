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

class LogErrorRequest(BaseModel):
    """
    Request payload for adding new error record.
    """
    message: str = Field(
        description="Message explaining error briefly."
    )
    stack_trace: str = Field(
        description="Stack-trace of encountered error."
    )
    sanitized_trace: str = Field(
        description="Sanitized version of stack-trace"
    )
    service_name: str = Field(
        description="Service in which error occured."
    )