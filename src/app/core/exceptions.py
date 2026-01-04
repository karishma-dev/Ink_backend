class AppException(Exception):
    """Base exception for all application errors"""
    def __init__(self, message: str, code: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class AuthException(AppException):
    """Authentication/Authorization errors"""
    def __init__(self, message: str, code: str = "AUTH_ERROR", status_code: int = 401, details: dict = None):
        super().__init__(message, code, status_code=status_code, details=details)

class ValidationException(AppException):
    """Input validation errors"""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR", details: dict = None):
        super().__init__(message, code, status_code=400, details=details)

class NotFound(AppException):
    """Resource not found errors"""
    def __init__(self, message: str, code: str = "NOT_FOUND", details: dict = None):
        super().__init__(message, code, status_code=404, details=details)

class RateLimitException(AppException):
    """Rate limit exceeded errors"""
    def __init__(self, message: str = "Rate limit exceeded. Please try again later.", 
                 code: str = "RATE_LIMIT_EXCEEDED", retry_after: int = 60):
        super().__init__(message, code, status_code=429, details={"retry_after": retry_after})
        self.retry_after = retry_after

class DatabaseException(AppException):
    """Database operation errors"""
    def __init__(self, message: str = "A database error occurred", 
                 code: str = "DATABASE_ERROR", details: dict = None):
        super().__init__(message, code, status_code=500, details=details)

class ExternalServiceException(AppException):
    """External service (Gemini, Qdrant) errors"""
    def __init__(self, message: str, code: str = "EXTERNAL_SERVICE_ERROR", 
                 service: str = None, details: dict = None):
        full_details = {"service": service, **(details or {})}
        super().__init__(message, code, status_code=502, details=full_details)