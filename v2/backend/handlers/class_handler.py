import json
import logging

from urllib.parse import urlparse, parse_qs
from services.class_services import get_classes, create_class
from utils.auth import require_role

# Configure logging for handler operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@require_role(['admin'])
def handle_create_class(request):
    """
    Handle POST requests to create a new class.
    Accepts JSON body with: name (str), school_id (int), academic_year (str), description (optional str).
    Returns 201 and class data on success, 400 on validation error, 500 on server error.
    """
    try:
        content_length = int(request.headers.get('Content-Length', 0))
        if content_length <= 0:
            logger.error("No data provided for create_class")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "No data provided"}).encode('utf-8'))
            return
        body = request.rfile.read(content_length).decode('utf-8')
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON body for create_class")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "Invalid JSON body"}).encode('utf-8'))
            return
        name = data.get("name")
        school_id = data.get("school_id")
        academic_year = data.get("academic_year")
        description = data.get("description")
        success, message, result = create_class(name, school_id, academic_year, description)
        if success:
            logger.info(f"Class '{name}' created for school_id {school_id}")
            request._set_headers(201)
            request.wfile.write(json.dumps({"message": message, "class": result}).encode('utf-8'))
        else:
            logger.error(f"Failed to create class: {message}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": message}).encode('utf-8'))
    except Exception as e:
        logger.error(f"Internal error in handle_create_class: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))

def handle_list_classes(request):
    """
    Handle GET requests to list all classes for a specified school.

    Retrieves classes for a given school_id provided in query parameters.
    Accessible only to admin users. Returns class details, including optional
    student lists with profile images.

    Args:
        request: HTTP request object with query parameters and user authentication
                 details set by the @require_role decorator.

    Query Parameters:
        school_id (int): The ID of the school to retrieve classes for.

    Returns:
        HTTP response with status code and JSON body:
            - 200: {"classes": [class_data, ...]} on success
            - 400: {"error": "error message"} for invalid input
            - 500: {"error": "internal error"} for unexpected errors

    Example:
        GET /classes?school_id=1
        Authorization: Bearer <admin-token>
        Response: {
            "classes": [
                {
                    "id": 101,
                    "name": "Math 101",
                    "school_id": 1,
                    "students": [
                        {"id": 1, "full_name": "John Doe", "profile_image": "uploads/123e4567-e89b-12d3-a456-426614174000.jpg"},
                        ...
                    ]
                },
                ...
            ]
        }

    Notes:
        - Validates school_id as an integer.
        - Logs requests and errors for auditing.
        - In production, consider pagination for large class lists (e.g., ?page=1&limit=20).
        - Includes student profile images for consistency with image handling.
        - Assumes get_classes returns a list of class dictionaries.
        - For image serving, use GET /uploads/<filename> endpoint from previous responses.
    """
    user = request.user
    try:
        # Parse query parameters
        query = parse_qs(urlparse(request.path).query)
        school_id = query.get("school_id", [None])[0]
        if not school_id:
            logger.error(f"User {user.id} missing school_id in classes request")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "school_id is required"}).encode('utf-8'))
            return

        # Validate school_id type
        try:
            school_id = int(school_id)
        except ValueError:
            logger.error(f"User {user.id} provided invalid school_id: {school_id}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "school_id must be an integer"}).encode('utf-8'))
            return

        # Fetch classes
        classes = get_classes(school_id)
        logger.info(f"User {user.id} retrieved {len(classes)} classes for school_id {school_id}")
        request._set_headers(200)
        request.wfile.write(json.dumps({"classes": classes}).encode('utf-8'))

    except Exception as e:
        logger.error(f"User {user.id} failed to list classes for school_id {school_id}: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))