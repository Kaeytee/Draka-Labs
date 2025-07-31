
import json
import logging
from urllib.parse import urlparse, parse_qs
from utils.auth import require_role
from services.accounts import register_school_admin
from services.school_services import list_schools, update_school_grading_system
# Configure logging for handler operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@require_role(['admin'])
def handle_register_school(request):
    """
    Handle POST requests to register a new school and its admin.
    """
    user = getattr(request, 'user', None)
    try:
        content_length = int(request.headers.get('Content-Length', 0))
        if content_length <= 0:
            logger.error(f"User {getattr(user, 'id', None)} sent empty request body for register_school")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "No data provided"}).encode('utf-8'))
            return
        body = request.rfile.read(content_length).decode('utf-8')
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            logger.error(f"User {getattr(user, 'id', None)} sent invalid JSON for register_school")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "Invalid JSON body"}).encode('utf-8'))
            return
        required_fields = ["school_name", "full_name", "phone", "email"]
        for field in required_fields:
            if field not in data or not data[field]:
                logger.error(f"Missing required field: {field} in register_school")
                request._set_headers(400)
                request.wfile.write(json.dumps({"error": f"Missing required field: {field}"}).encode('utf-8'))
                return
        school_name = data["school_name"]
        full_name = data["full_name"]
        phone = data["phone"]
        email = data["email"]
        grading_system = data.get("grading_system")
        result = register_school_admin(school_name, full_name, phone, email, grading_system)
        if result.get("status") == "success":
            logger.info(f"School {school_name} registered successfully by admin {full_name}")
            request._set_headers(201)
            request.wfile.write(json.dumps(result).encode('utf-8'))
        else:
            logger.error(f"Failed to register school: {result.get('message')}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": result.get("message")}).encode('utf-8'))
    except Exception as e:
        logger.error(f"Error registering school: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))

@require_role(['admin'])
def handle_list_schools(request):
    """
    Handle GET requests to list all schools.

    Retrieves schools, optionally filtered by query parameters (e.g., school_id).
    Accessible only to admin users. Returns school details, including optional
    class and student data with profile images.

    Args:
        request: HTTP request object with query parameters and user authentication
                 details set by the @require_role decorator.

    Query Parameters:
        school_id (int, optional): ID of a specific school to retrieve.

    Returns:
        HTTP response with status code and JSON body:
            - 200: {"schools": [school_data, ...]} on success
            - 400: {"error": "error message"} for invalid input
            - 500: {"error": "internal error"} for unexpected errors

    Example:
        GET /schools?school_id=1
        Authorization: Bearer <admin-token>
        Response: {
            "schools": [
                {
                    "id": 1,
                    "name": "Springfield High",
                    "grading_system": [{"grade": "A", "min": 90, "max": 100}, ...],
                    "classes": [
                        {
                            "id": 101,
                            "name": "Math 101",
                            "students": [
                                {"id": 1, "full_name": "John Doe", "profile_image": "uploads/123e4567-e89b-12d3-a456-426614174000.jpg"},
                                ...
                            ]
                        },
                        ...
                    ]
                }
            ]
        }

    Notes:
        - Validates school_id as an integer if provided.
        - Logs requests and errors for auditing.
        - In production, consider pagination for large school lists (e.g., ?page=1&limit=20).
        - Includes student profile images via class relationship.
        - For image serving, use GET /uploads/<filename> endpoint.
    """
    user = request.user
    try:
        # Parse query parameters
        query = parse_qs(urlparse(request.path).query)
        school_id = query.get("school_id", [None])[0]
        if school_id is not None:
            try:
                school_id = int(school_id)
            except ValueError:
                logger.error(f"User {user.id} provided invalid school_id: {school_id}")
                request._set_headers(400)
                request.wfile.write(json.dumps({"error": "school_id must be an integer"}).encode('utf-8'))
                return

        # Fetch schools
        schools = list_schools(school_id)
        logger.info(f"User {user.id} retrieved {len(schools)} schools for school_id={school_id}")
        request._set_headers(200)
        request.wfile.write(json.dumps({"schools": schools}).encode('utf-8'))

    except Exception as e:
        logger.error(f"User {user.id} failed to list schools for school_id={school_id}: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))

@require_role(['admin'])
def handle_update_grading_system(request, school_id):
    """
    Handle POST requests to update a school's grading system.

    Updates the grading_system field for the specified school with a list of grading rules.
    Expects a JSON body with a grading_system list. Accessible only to admin users.

    Args:
        request: HTTP request object with JSON body and user authentication details.
        school_id (int): ID of the school to update.

    Body:
        {
            "grading_system": [
                {"grade": str, "min": float, "max": float},
                ...
            ]
        }

    Returns:
        HTTP response with status code and JSON body:
            - 200: {"message": "success message", "school_id": int, "grading_system": list} on success
            - 400: {"error": "error message"} for invalid input
            - 500: {"error": "internal error"} for unexpected errors

    Example:
        POST /schools/1/grading_system
        Authorization: Bearer <admin-token>
        Body: {
            "grading_system": [
                {"grade": "A", "min": 90, "max": 100},
                {"grade": "B", "min": 80, "max": 89.9}
            ]
        }
        Response: {
            "message": "Grading system updated successfully",
            "school_id": 1,
            "grading_system": [
                {"grade": "A", "min": 90, "max": 100},
                {"grade": "B", "min": 80, "max": 89.9}
            ]
        }

    Notes:
        - Validates school_id and grading_system format (list of dicts with grade, min, max).
        - Ensures min/max are numeric and min <= max.
        - Logs requests and errors for auditing.
        - In production, consider rate limiting and stricter validation (e.g., unique grades).
        - Student profile images are not directly affected but may be included in list_schools.
    """
    user = request.user
    try:
        # Validate school_id
        if not isinstance(school_id, int):
            logger.error(f"User {user.id} provided invalid school_id: {school_id}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "school_id must be an integer"}).encode('utf-8'))
            return

        # Parse JSON body
        content_length = int(request.headers.get('Content-Length', 0))
        if content_length <= 0:
            logger.error(f"User {user.id} sent empty request body for school_id {school_id}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "No data provided"}).encode('utf-8'))
            return
        body = request.rfile.read(content_length).decode('utf-8')
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            logger.error(f"User {user.id} sent invalid JSON for school_id {school_id}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "Invalid JSON body"}).encode('utf-8'))
            return

        # Validate grading_system
        grading_system = data.get("grading_system")
        if grading_system is None:
            logger.error(f"User {user.id} missing grading_system for school_id {school_id}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "Missing required field: grading_system"}).encode('utf-8'))
            return
        if not isinstance(grading_system, list):
            logger.error(f"User {user.id} provided invalid grading_system type for school_id {school_id}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "grading_system must be a list"}).encode('utf-8'))
            return
        for rule in grading_system:
            if not (isinstance(rule, dict) and "grade" in rule and "min" in rule and "max" in rule):
                logger.error(f"User {user.id} provided invalid grading rule for school_id {school_id}")
                request._set_headers(400)
                request.wfile.write(json.dumps({"error": "Each grading rule must be a dict with grade, min, and max"}).encode('utf-8'))
                return
            if not (isinstance(rule["min"], (int, float)) and isinstance(rule["max"], (int, float)) and rule["min"] <= rule["max"]):
                logger.error(f"User {user.id} provided invalid min/max for school_id {school_id}")
                request._set_headers(400)
                request.wfile.write(json.dumps({"error": "min and max must be numbers with min <= max"}).encode('utf-8'))
                return

        # Update grading system
        success, message, result = update_school_grading_system(school_id, grading_system)
        if success:
            logger.info(f"User {user.id} updated grading system for school_id {school_id}")
            request._set_headers(200)
            request.wfile.write(json.dumps({
                "message": message,
                "school_id": result["school_id"],
                "grading_system": result["grading_system"]
            }).encode('utf-8'))
        else:
            logger.error(f"User {user.id} failed to update grading system for school_id {school_id}: {message}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": message}).encode('utf-8'))

    except Exception as e:
        logger.error(f"User {user.id} encountered error updating school_id {school_id}: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))

@require_role(['admin'])
def not_implemented(request):
    """
    Handle unimplemented endpoints.

    Returns a 501 Not Implemented response for routes that are not yet supported.

    Args:
        request: HTTP request object.

    Returns:
        HTTP response with status 501 and JSON body: {"error": "Not implemented"}
    """
    logger.info(f"User {request.user.id} accessed unimplemented endpoint: {request.path}")
    request._set_headers(501)
    request.wfile.write(json.dumps({"error": "Not implemented"}).encode('utf-8'))