
import json
import logging

# Configure logging with debug level
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
            logger.info(f"Auth check - User: {user}, Required roles: {allowed_roles}")
            
            if not user:
                logger.warning("Authentication required - no user found")
                request._set_headers(403)
                request.wfile.write(json.dumps({"error": "Forbidden: authentication required"}).encode())
                return
            
            # Handle both dictionary format (from JWT) and object format (from DB)
            if isinstance(user, dict):
                user_role = user.get('role')
            elif hasattr(user, 'role'):
                # Handle enum role
                user_role = user.role.value if hasattr(user.role, 'value') else user.role
            else:
                user_role = None
            
            logger.info(f"User role: {user_role}, Allowed roles: {allowed_roles}")
            
            if not user_role or user_role not in allowed_roles:
                logger.warning(f"Insufficient permissions - user role: {user_role}, required: {allowed_roles}")
                request._set_headers(403)
                request.wfile.write(json.dumps({"error": "Forbidden: insufficient permissions"}).encode())
                return
                
            return handler(request, *args, **kwargs)
        return wrapper
    return decorator