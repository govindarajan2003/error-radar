from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """
    Request payload for error analysis.
    """
    
    id: int = Field(
        description="Error Id of the querying record, to avoid getting same record when searching for similar errors."
    )
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
    service_name: str = Field(
        description="Service in which error occured."
    )