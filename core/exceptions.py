from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses.
    
    Format:
    {
        "error": "Human readable message",
        "code": "error_code",
        "field": "field_name" (optional)
    }
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        # Handle DRF validation errors
        if isinstance(response.data, dict):
            # Extract first error
            for field, errors in response.data.items():
                if isinstance(errors, list):
                    error_message = errors[0]
                else:
                    error_message = str(errors)
                
                return Response(
                    {
                        "error": error_message,
                        "code": "validation_error",
                        "field": field if field != "non_field_errors" else None,
                    },
                    status=response.status_code,
                )
        
        # Handle simple string errors
        if isinstance(response.data, str):
            return Response(
                {
                    "error": response.data,
                    "code": "error",
                },
                status=response.status_code,
            )
    
    # Handle unexpected errors
    return Response(
        {
            "error": "An unexpected error occurred.",
            "code": "internal_error",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


class BusinessError(Exception):
    """Base exception for business logic errors."""
    
    def __init__(self, message, code="business_error"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class PermissionDeniedError(BusinessError):
    """Raised when user doesn't have permission for an action."""
    
    def __init__(self, message="Permission denied"):
        super().__init__(message, code="permission_denied")


class NotFoundError(BusinessError):
    """Raised when a resource is not found."""
    
    def __init__(self, message="Resource not found"):
        super().__init__(message, code="not_found")


class ValidationError(BusinessError):
    """Raised when validation fails."""
    
    def __init__(self, message, field=None):
        self.field = field
        super().__init__(message, code="validation_error")
