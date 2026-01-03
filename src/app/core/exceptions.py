class AppException(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

class AuthException(AppException):
    pass

class ValidationException(AppException):
    pass

class NotFound(AppException):
    pass