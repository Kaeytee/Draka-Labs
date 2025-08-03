import json
import logging
import csv
import io
import os
from urllib.parse import urlparse, parse_qs
from services.grade_services import get_grades, upload_grade, get_grades_for_student
from services.student_services import student_lookup
from utils.auth import require_role
import json
import logging
import os
import csv

# Configure logging for debugging and auditing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for bulk upload validation
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB max file size
ALLOWED_FILE_EXTENSIONS = {'.csv', '.txt'}

@require_role(['admin', 'teacher', 'student'])
def handle_list_grades(request):
    """
    Handle GET requests to retrieve all grades for a student.

    This endpoint fetches grades for a specified student using the student_id
    provided in query parameters. Accessible to admin, teacher, and student roles.

    Args:
        request: HTTP request object with query parameters and user authentication
                 details set by the @require_role decorator.

    Query Parameters:
        student_id (int): The ID of the student whose grades are requested.

    Returns:
        HTTP response with status code and JSON body:
            - 200: {"grades": [grade_data, ...]} on success
            - 400: {"error": "error message"} for invalid input
            - 500: {"error": "internal error"} for unexpected errors

    Example:
        GET /grades?student_id=123
        Authorization: Bearer <token>
        Response: {"grades": [{"course_id": 101, "value": 85}, ...]}

    Notes:
        - Assumes `get_grades` returns a list of grade dictionaries.
        - Logs access for auditing.
        - In production, consider validating student_id existence in the database.
        - Add pagination for large grade lists to improve performance.
    """
    try:
        # Parse query parameters
        query = parse_qs(urlparse(request.path).query)
        student_id = query.get("student_id", [None])[0]
        if not student_id:
            logger.error(f"User {request.user.id} missing student_id in grades request")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "student_id is required"}).encode('utf-8'))
            return

        # Validate student_id type
        try:
            student_id = int(student_id)
        except ValueError:
            logger.error(f"User {request.user.id} provided invalid student_id: {student_id}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "student_id must be an integer"}).encode('utf-8'))
            return

        # Students can only access their own grades
        if hasattr(request, 'user') and request.user:
            user_role = request.user.get('role') if isinstance(request.user, dict) else getattr(request.user, 'role', None)
            user_id = request.user.get('id') if isinstance(request.user, dict) else getattr(request.user, 'id', None)
            
            if user_role == 'student' and user_id != student_id:
                logger.warning(f"Student {user_id} attempted to access grades for student {student_id}")
                request._set_headers(403)
                request.wfile.write(json.dumps({"error": "Students can only access their own grades"}).encode('utf-8'))
                return

        # Fetch grades
        grades = get_grades_for_student(student_id)
        logger.info(f"User {request.user.id} retrieved {len(grades)} grades for student_id {student_id}")
        request._set_headers(200)
        request.wfile.write(json.dumps({"grades": grades}).encode('utf-8'))

    except Exception as e:
        logger.error(f"User {request.user.id} failed to list grades: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))

@require_role(['admin', 'teacher'])
def handle_upload_grade(request):
    """
    Handle POST requests to upload a single grade for a student.

    Expects a JSON body with student_id, course_id, value, and graded_by. Validates
    input types and score range (0-100). Accessible to admin and teacher roles.

    Args:
        request: HTTP request object containing JSON body and user authentication
                 details set by the @require_role decorator.

    Body:
        {
            "student_id": int,      // Student ID
            "course_id": int,       // Course ID
            "value": float/int,     // Grade value (0-100)
            "graded_by": int        // ID of the user assigning the grade
        }

    Returns:
        HTTP response with status code and JSON body:
            - 201: {"message": "success message", ...result} on success
            - 400: {"error": "error message"} for invalid input or failure
            - 500: {"error": "internal error"} for unexpected errors

    Example:
        POST /upload_grade
        Authorization: Bearer <token>
        Body: {"student_id": 123, "course_id": 101, "value": 85, "graded_by": 1}
        Response: {"message": "Grade uploaded successfully", "grade_id": 456}

    Notes:
        - Validates input types and score range.
        - Logs all upload attempts for auditing.
        - In production, verify student_id and course_id existence in the database.
        - Consider rate limiting to prevent abuse.
        - For image integration, grades could include a reference to student profile images
          (e.g., via handle_upload_profile_image from previous code).
    """
    user = request.user
    content_length = int(request.headers.get('Content-Length', 0))
    if content_length <= 0:
        logger.error(f"User {user.id} sent empty request body for grade upload")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "No data provided"}).encode('utf-8'))
        return

    try:
        body = request.rfile.read(content_length)
        data = json.loads(body)
    except json.JSONDecodeError:
        logger.error(f"User {user.id} sent invalid JSON for grade upload")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Invalid JSON body."}).encode('utf-8'))
        return

    # Validate required fields
    required_fields = ["student_id", "course_id", "value", "graded_by"]
    for field in required_fields:
        if field not in data:
            logger.error(f"User {user.id} missing required field: {field}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": f"Missing required field: {field}"}).encode('utf-8'))
            return

    # Validate types
    if not all(isinstance(data[field], int) for field in ["student_id", "course_id", "graded_by"]):
        logger.error(f"User {user.id} provided invalid integer fields")
        request._set_headers(400)
        request.wfile.write(json.dumps({
            "error": "student_id, course_id, and graded_by must be integers."
        }).encode('utf-8'))
        return
    if not isinstance(data["value"], (int, float)):
        logger.error(f"User {user.id} provided invalid value type: {type(data['value'])}")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "value must be a number."}).encode('utf-8'))
        return

    # Validate score range
    student_id = data["student_id"]
    course_id = data["course_id"]
    value = data["value"]
    graded_by = data["graded_by"]
    if not 0 <= value <= 100:
        logger.error(f"User {user.id} provided invalid score: {value}")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "value must be between 0 and 100."}).encode('utf-8'))
        return

    # Ensure graded_by matches authenticated user (optional security check)
    if graded_by != user.id:
        logger.warning(f"User {user.id} attempted to set graded_by to {graded_by}")
        request._set_headers(403)
        request.wfile.write(json.dumps({"error": "graded_by must match authenticated user."}).encode('utf-8'))
        return

    success, message, result = upload_grade(student_id, course_id, value, graded_by)
    if success:
        logger.info(f"User {user.id} uploaded grade for student_id {student_id}, course_id {course_id}")
        request._set_headers(201)
        request.wfile.write(json.dumps({"message": message, **result}).encode('utf-8'))
    else:
        logger.error(f"User {user.id} failed to upload grade: {message}")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": message}).encode('utf-8'))

@require_role(['admin', 'teacher'])
def handle_bulk_grade_upload(request):
    """
    Handle POST requests to upload grades in bulk via CSV or TXT file.

    Accepts a multipart/form-data request with a CSV or TXT file containing student
    names and scores, and a course_id in the form data. Processes each row to assign
    grades using the upload_grade service. Accessible to admin and teacher roles.

    Args:
        request: HTTP request object containing multipart/form-data body and user
                 authentication details set by the @require_role decorator.

    Body:
        Form-data with:
            - course_id: int, the ID of the course
            - file: CSV or TXT file with format "name,score" (e.g., "John Doe,85")

    Returns:
        HTTP response with status code and JSON body:
            - 200: {"message": "Bulk grades processed...", "results": [...]} on success
            - 400: {"error": "error message"} for invalid input or file format
            - 500: {"error": "internal error"} for unexpected errors

    Example:
        POST /upload_grades_bulk
        Authorization: Bearer <token>
        Content-Type: multipart/form-data; boundary=----WebKitFormBoundary123
        Body:
        ------WebKitFormBoundary123
        Content-Disposition: form-data; name="course_id"
        101
        ------WebKitFormBoundary123
        Content-Disposition: form-data; name="file"; filename="grades.csv"
        Content-Type: text/csv
        name,score
        John Doe,85
        Jane Smith,90
        ------WebKitFormBoundary123--
        Response: {
            "message": "Bulk grades processed (CSV)",
            "results": [
                {"name": "John Doe", "status": "success", "message": "Grade uploaded", "result": {...}},
                {"name": "Jane Smith", "status": "success", "message": "Grade uploaded", "result": {...}}
            ]
        }

    Notes:
        - Supports CSV and TXT files with "name,score" format.
        - Validates file size, extension, and score range.
        - Uses student_lookup to resolve student names to IDs.
        - Logs all processing steps for auditing.
        - In production, use database transactions for atomicity in bulk uploads.
        - Consider adding file content validation (e.g., python-magic for MIME types).
        - For image integration, student profile images could be referenced in grade reports
          (e.g., via handle_upload_profile_image from previous code).
    """
    user = request.user
    content_type = request.headers.get('Content-Type', '')
    if 'multipart/form-data' not in content_type:
        logger.error(f"User {user.id} sent invalid Content-Type for bulk grade upload: {content_type}")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Content-Type must be multipart/form-data"}).encode('utf-8'))
        return

    # Parse multipart form data
    boundary = content_type.split("boundary=")[-1].strip()
    remainbytes = int(request.headers.get('Content-Length', 0))
    if remainbytes > MAX_FILE_SIZE:
        logger.error(f"User {user.id} sent oversized file: {remainbytes} bytes")
        request._set_headers(400)
        request.wfile.write(json.dumps({
            "error": f"File size exceeds {MAX_FILE_SIZE // 1024 // 1024}MB limit"
        }).encode('utf-8'))
        return

    line = request.rfile.readline()
    remainbytes -= len(line)
    if boundary not in line.decode('utf-8'):
        logger.error(f"User {user.id} sent invalid multipart boundary")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Content does not start with boundary"}).encode('utf-8'))
        return

    # Read until file content or course_id
    course_id = None
    filename = None
    content_type = None
    while remainbytes > 0:
        line = request.rfile.readline()
        remainbytes -= len(line)
        if b'filename=' in line:
            filename = line.decode('utf-8').split('filename="')[1].split('"')[0]
            break
        if b'name="course_id"' in line:
            request.rfile.readline()  # Skip blank line
            remainbytes -= len(request.rfile.readline())
            course_id_line = request.rfile.readline().decode('utf-8').strip()
            remainbytes -= len(course_id_line.encode('utf-8')) + 2  # Account for \r\n
            try:
                course_id = int(course_id_line)
            except ValueError:
                logger.error(f"User {user.id} provided invalid course_id: {course_id_line}")
                request._set_headers(400)
                request.wfile.write(json.dumps({"error": "course_id must be an integer"}).encode('utf-8'))
                return

    if not filename:
        logger.error(f"User {user.id} did not provide a file for bulk grade upload")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "No file provided"}).encode('utf-8'))
        return

    # Validate course_id
    if not course_id:
        logger.error(f"User {user.id} missing course_id for bulk grade upload")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "course_id is required"}).encode('utf-8'))
        return

    # Validate file extension
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in ALLOWED_FILE_EXTENSIONS:
        logger.error(f"User {user.id} sent invalid file extension: {file_ext}")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "File must be .csv or .txt"}).encode('utf-8'))
        return

    # Read Content-Type and skip blank line
    line = request.rfile.readline()
    remainbytes -= len(line)
    content_type = line.decode('utf-8').split('Content-Type: ')[1].split('\r\n')[0]
    if content_type not in ['text/csv', 'text/plain']:
        logger.error(f"User {user.id} sent invalid file content type: {content_type}")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "File must be CSV or plain text"}).encode('utf-8'))
        return

    request.rfile.readline()
    remainbytes -= len(request.rfile.readline())

    # Read file content
    file_data = b""
    while remainbytes > 0:
        line = request.rfile.readline()
        remainbytes -= len(line)
        if boundary.encode() in line:
            break
        file_data += line

    try:
        decoded = file_data.decode('utf-8')
        results = []
        graded_by = user.id

        # Process CSV or TXT
        try:
            reader = csv.reader(io.StringIO(decoded))
            header = next(reader, None)
            if header and len(header) >= 2 and header[0].strip().lower() != 'name':
                reader = csv.reader(io.StringIO(decoded))  # Reset if no header
            for row in reader:
                if len(row) < 2:
                    results.append({"name": "unknown", "status": "error", "message": "Invalid row format"})
                    continue
                name, score = row[0].strip(), row[1].strip()
                student = student_lookup(name)
                if not student:
                    results.append({"name": name, "status": "error", "message": "Student not found"})
                    continue
                try:
                    score_value = float(score)
                    if not 0 <= score_value <= 100:
                        results.append({"name": name, "status": "error", "message": "Score must be between 0 and 100"})
                        continue
                except ValueError:
                    results.append({"name": name, "status": "error", "message": "Invalid score format"})
                    continue
                success, message, result = upload_grade(student["id"], course_id, score_value, graded_by)
                results.append({
                    "name": name,
                    "status": "success" if success else "error",
                    "message": message,
                    "result": result
                })
            logger.info(f"User {user.id} processed {len(results)} grades via CSV for course_id {course_id}")
            request._set_headers(200)
            request.wfile.write(json.dumps({
                "message": "Bulk grades processed (CSV)",
                "results": results
            }).encode('utf-8'))
            return

        except csv.Error:
            # Try TXT format
            results = []
            for line in decoded.splitlines():
                if not line.strip():
                    continue
                parts = line.split(",")
                if len(parts) < 2:
                    results.append({"name": "unknown", "status": "error", "message": "Invalid row format"})
                    continue
                name, score = parts[0].strip(), parts[1].strip()
                student = student_lookup(name)
                if not student:
                    results.append({"name": name, "status": "error", "message": "Student not found"})
                    continue
                try:
                    score_value = float(score)
                    if not 0 <= score_value <= 100:
                        results.append({"name": name, "status": "error", "message": "Score must be between 0 and 100"})
                        continue
                except ValueError:
                    results.append({"name": name, "status": "error", "message": "Invalid score format"})
                    continue
                success, message, result = upload_grade(student["id"], course_id, score_value, graded_by)
                results.append({
                    "name": name,
                    "status": "success" if success else "error",
                    "message": message,
                    "result": result
                })
            if results:
                logger.info(f"User {user.id} processed {len(results)} grades via TXT for course_id {course_id}")
                request._set_headers(200)
                request.wfile.write(json.dumps({
                    "message": "Bulk grades processed (TXT)",
                    "results": results
                }).encode('utf-8'))
                return

            raise ValueError("No valid data processed")

    except UnicodeDecodeError:
        logger.error(f"User {user.id} sent file with invalid encoding")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Failed to decode file. Ensure valid UTF-8 encoding"}).encode('utf-8'))
    except Exception as e:
        logger.error(f"User {user.id} failed to process bulk grades: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))