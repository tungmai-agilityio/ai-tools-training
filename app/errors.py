class DomainError(Exception):
    """A business-rule violation. `status` is the HTTP status to return."""

    def __init__(self, message: str, status: int = 409):
        super().__init__(message)
        self.message = message
        self.status = status
