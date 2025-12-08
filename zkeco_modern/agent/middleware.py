"""
Middleware to track current user and request in thread-local storage.

This allows Django signals to access the current user and request context
when logging CRUD operations, even though signals don't have direct access
to the request object.
"""
from agent.signals import set_current_user, set_current_request


class AuditMiddleware:
    """Store current user and request in thread-local storage for audit logging."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Set current user and request before processing view
        set_current_user(request.user if request.user.is_authenticated else None)
        set_current_request(request)
        
        response = self.get_response(request)
        
        # Clean up after request (optional but good practice)
        set_current_user(None)
        set_current_request(None)
        
        return response
