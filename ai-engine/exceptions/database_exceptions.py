class ErrorLogNotFoundError(Exception):
    """
    Raised when an error log ID cannot be found in the database.
    """
    pass

class UpdateOccurrenceFailureError(Exception):
    """
    Raised when occurance_count is not updated
    """
    pass