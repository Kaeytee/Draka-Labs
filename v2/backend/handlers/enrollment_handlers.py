import json
import logging
from urllib.parse import urlparse, parse_qs
from services.enrollment_services import get_students, enroll_student
from utils.auth import require_role

# Configure logging for debugging and auditing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@require_role(['admin'])
def handle_list_students(request):
    """
    Handle GET requests to list all students in a specified class.

    This endpoint retrieves a list of students enrolled in a class identified by
    `class_id` provided in the query parameters. Only accessible to admin users.

    Args:
        request: HTTP request object with path containing query parameters and
                 user authentication details set by the @require_role decorator.

    Query Parameters:
        class_id (int): The ID of the class to retrieve students for.

    Returns:
        HTTP response with status code and JSON body:
            - 200: {"students": [student_data, ...]} on success.
            - 400: {"error": "error message"} if class_id is missing or invalid.

    Example:
        GET /students?class_id=101
        Response: {"students": [{"id": 1, "full_name": "John Doe"}, ...]}

    Notes:
        - Assumes `get_students` returns a list of student dictionaries.
        - Logs errors for debugging and auditing.
        - Consider adding pagination for large class sizes in production.
        - Validate class_id existence in the database for stricter checks.
    """
    try:
        # Parse query parameters from the URL
        query = parse_qs(urlparse(request.path).query)
        class_id = query.get("class_id", [None])[0]

        # Validate class_id presence and type
        if not class_id:
            logger.error("Missing class_id in query parameters")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "class_id is required"}).encode('utf-8'))
            return

        try:
            class_id = int(class_id)
        except ValueError:
            logger.error(f"Invalid class_id: {class_id}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "class_id must be an integer"}).encode('utf-8'))
            return

        # Retrieve students from the service
        students = get_students(class_id)
        logger.info(f"Retrieved {len(students)} students for class_id {class_id}")

        # Send successful response
        request._set_headers(200)
        request.wfile.write(json.dumps({"students": students}).encode('utf-8'))

    except Exception as e:
        # Log unexpected errors and return a generic error response
        logger.error(f"Error listing students for class_id {class_id}: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))

@require_role(['admin'])
def handle_enroll_student(request):
    """
    Handle POST requests to enroll a student in a class.

    This endpoint creates or enrolls a student with the provided details in the
    specified class. Expects a JSON body with `full_name`, `school_initials`, and
    `class_id`. Only accessible to admin users.

    Args:
        request: HTTP request object containing the JSON body and user
                 authentication details set by the @require_role decorator.

    Body:
        {
            "full_name": str,        // Student's full name (e.g., "John Doe")
            "school_initials": str,  // School identifier (e.g., "XYZ")
            "class_id": int          // ID of the class to enroll in
        }

    Returns:
        HTTP response with status code and JSON body:
            - 201: {"message": "success message", ...result} on success.
            - 400: {"error": "error message"} for invalid input or enrollment failure.
            - 500: {"error": "internal error"} for unexpected errors.

    Example:
        POST /enroll_student
        Body: {"full_name": "John Doe", "school_initials": "XYZ", "class_id": 101}
        Response: {"message": "Student enrolled", "student_id": 123, "class_id": 101}

    Notes:
        - Assumes `enroll_student` handles student creation or lookup and enrollment.
        - Validates input types and presence of required fields.
        - Logs all actions for auditing and debugging.
        - Consider adding email validation or uniqueness checks for students.
        - In production, add rate limiting to prevent abuse.
        - Consider validating `school_initials` against a predefined list.
    """
    content_length = int(request.headers.get('Content-Length', 0))
    if content_length <= 0:
        logger.error("No data provided in request body")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "No data provided"}).encode('utf-8'))
        return

    try:
        # Parse JSON body
        body = request.rfile.read(content_length)
        data = json.loads(body)

        # Validate required fields
        required_fields = ["full_name", "school_initials", "class_id"]
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                request._set_headers(400)
                request.wfile.write(json.dumps({"error": f"Missing required field: {field}"}).encode('utf-8'))
                return

        # Validate data types
        if not isinstance(data["full_name"], str) or not data["full_name"].strip():
            logger.error("Invalid full_name: must be a non-empty string")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "full_name must be a non-empty string"}).encode('utf-8'))
            return
        if not isinstance(data["school_initials"], str) or not data["school_initials"].strip():
            logger.error("Invalid school_initials: must be a non-empty string")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "school_initials must be a non-empty string"}).encode('utf-8'))
            return
        if not isinstance(data["class_id"], int):
            logger.error(f"Invalid class_id: {data['class_id']} is not an integer")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "class_id must be an integer"}).encode('utf-8'))
            return

        # Extract validated data
        full_name = data["full_name"].strip()
        school_initials = data["school_initials"].strip()
        class_id = data["class_id"]

        # Additional validation (production-ready)
        if len(full_name) < 2:
            logger.error("Invalid full_name: too short")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "full_name must be at least 2 characters"}).encode('utf-8'))
            return
        if len(school_initials) > 10:  # Arbitrary limit; adjust as needed
            logger.error("Invalid school_initials: too long")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "school_initials must not exceed 10 characters"}).encode('utf-8'))
            return

        # Call enrollment service
        success, message, result = enroll_student(full_name, school_initials, class_id)
        logger.info(f"Enroll student attempt: {full_name} in class_id {class_id}, success: {success}")

        if success:
            request._set_headers(201)
            request.wfile.write(json.dumps({
                "message": message,
                **result
            }).encode('utf-8'))
        else:
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": message}).encode('utf-8'))

    except json.JSONDecodeError:
        logger.error("Invalid JSON body in enroll_student request")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Invalid JSON body"}).encode('utf-8'))
    except Exception as e:
        logger.error(f"Error enrolling student: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))