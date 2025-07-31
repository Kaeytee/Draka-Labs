
import json

def require_role(allowed_roles):
    """
    Decorator to enforce role-based access control on handlers.
    Args:
        allowed_roles (list): List of allowed role strings, e.g. ['admin', 'teacher']
    Returns:
        function: Decorated handler function that enforces RBAC.
    Usage:
        @require_role(['admin'])
        def handler(request): ...
    """
    def decorator(handler):
        def wrapper(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if not user or not hasattr(user, 'role') or user.role.value not in allowed_roles:
                request._set_headers(403)
                request.wfile.write(json.dumps({"error": "Forbidden: insufficient permissions"}).encode())
                return
            return handler(request, *args, **kwargs)
        return wrapper
    return decorator