import json
from services.grade_services import get_grades
from utils.auth import require_role

@require_role(['admin', 'teacher'])
def handle_list_grades(request):
    """
    GET /grades?student_id=...
    Get all grades for a student.
    """
    from urllib.parse import urlparse, parse_qs
    query = parse_qs(urlparse(request.path).query)
    student_id = query.get("student_id", [None])[0]
    if not student_id:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "student_id is required"}).encode('utf-8'))
        return
    grades = get_grades(student_id)
    request._set_headers(200)
    request.wfile.write(json.dumps({"grades": grades}).encode('utf-8'))
import csv
import io
import json
from services.grade_services import upload_grade
from services.student_services import student_lookup  # Added import for student lookup
from utils.auth import require_role

@require_role(['teacher'])
def handle_upload_grade(request):
    """
    HTTP handler for uploading a grade.
    Expects JSON body with: student_id, course_id, value, graded_by
    """
    content_length = int(request.headers.get('Content-Length', 0))
    body = request.rfile.read(content_length)
    try:
        data = json.loads(body)
    except Exception:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Invalid JSON body."}).encode('utf-8'))
        return
    # Validate required fields
    for field in ["student_id", "course_id", "value", "graded_by"]:
        if field not in data:
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": f"Missing required field: {field}"}).encode('utf-8'))
            return
    # Validate types
    if not isinstance(data["student_id"], int) or not isinstance(data["course_id"], int) or not isinstance(data["graded_by"], int):
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "student_id, course_id, and graded_by must be integers."}).encode('utf-8'))
        return
    if not (isinstance(data["value"], int) or isinstance(data["value"], float)):
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "value must be a number."}).encode('utf-8'))
        return
    student_id = data["student_id"]
    course_id = data["course_id"]
    value = data["value"]
    graded_by = data["graded_by"]
    success, message, result = upload_grade(student_id, course_id, value, graded_by)
    if success:
        request._set_headers(201)
        request.wfile.write(json.dumps({
            "message": message,
            **result
        }).encode('utf-8'))
    else:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": message}).encode('utf-8'))

@require_role(['teacher'])
def handle_bulk_grade_upload(request):
    """
    POST /upload_grades_bulk
    Accepts multipart/form-data with a file (CSV or XLSX).
    CSV format: name,score
    Expects course_id in the form data or request context.
    """
    content_type = request.headers.get('Content-Type', '')
    if 'multipart/form-data' not in content_type:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Content-Type must be multipart/form-data"}).encode('utf-8'))
        return

    # Parse multipart form data
    boundary = content_type.split("boundary=")[-1].strip()
    remainbytes = int(request.headers.get('Content-Length', 0))
    line = request.rfile.readline()
    remainbytes -= len(line)
    if boundary not in line.decode('utf-8'):
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Content does not start with boundary"}).encode('utf-8'))
        return

    # Read until file content
    course_id = None  # Initialize course_id
    while remainbytes > 0:
        line = request.rfile.readline()
        remainbytes -= len(line)
        if b'filename=' in line:
            break
        # Check for course_id in form data
        if b'name="course_id"' in line:
            request.rfile.readline()  # Skip blank line
            remainbytes -= len(request.rfile.readline())
            course_id_line = request.rfile.readline().decode('utf-8').strip()
            remainbytes -= len(course_id_line.encode('utf-8')) + 2  # Account for \r\n
            try:
                course_id = int(course_id_line)
            except ValueError:
                request._set_headers(400)
                request.wfile.write(json.dumps({"error": "course_id must be an integer"}).encode('utf-8'))
                return

    # Skip Content-Type line and blank line
    request.rfile.readline()
    remainbytes -= len(line)
    request.rfile.readline()
    remainbytes -= len(line)

    # Read file content
    file_data = b""
    while remainbytes > 0:
        line = request.rfile.readline()
        remainbytes -= len(line)
        if boundary.encode() in line:
            break
        file_data += line

    # Validate course_id
    if not course_id:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "course_id is required"}).encode('utf-8'))
        return

    # Try CSV or TXT processing
    try:
        decoded = file_data.decode('utf-8')
        results = []
        graded_by = request.user.id  # Assume user ID from authenticated teacher

        # Try CSV first
        try:
            reader = csv.reader(io.StringIO(decoded))
            # Skip header if present (assuming first row might be a header)
            header = next(reader, None)
            if header and len(header) >= 2 and header[0].strip().lower() != 'name':
                reader = csv.reader(io.StringIO(decoded))  # Reset reader if no header
            for row in reader:
                if len(row) < 2:
                    results.append({"name": "unknown", "status": "error", "message": "Invalid row format"})
                    continue
                name, score = row[0].strip(), row[1].strip()
                # Lookup student by name
                student = student_lookup(name)
                if not student:
                    results.append({"name": name, "status": "error", "message": "Student not found"})
                    continue
                # Validate score
                try:
                    score_value = float(score)
                except ValueError:
                    results.append({"name": name, "status": "error", "message": "Invalid score format"})
                    continue
                # Upload grade
                success, message, result = upload_grade(student["id"], course_id, score_value, graded_by)
                results.append({
                    "name": name,
                    "status": "success" if success else "error",
                    "message": message,
                    "result": result
                })
            request._set_headers(200)
            request.wfile.write(json.dumps({
                "message": "Bulk grades processed (CSV)",
                "results": results
            }).encode('utf-8'))
            return
        except Exception:
            pass

        # Try TXT: each line is name,score
        txt_results = []
        for line in decoded.splitlines():
            if not line.strip():
                continue
            parts = line.split(",")
            if len(parts) < 2:
                txt_results.append({"name": "unknown", "status": "error", "message": "Invalid row format"})
                continue
            name, score = parts[0].strip(), parts[1].strip()
            student = student_lookup(name)
            if not student:
                txt_results.append({"name": name, "status": "error", "message": "Student not found"})
                continue
            try:
                score_value = float(score)
            except ValueError:
                txt_results.append({"name": name, "status": "error", "message": "Invalid score format"})
                continue
            success, message, result = upload_grade(student["id"], course_id, score_value, graded_by)
            txt_results.append({
                "name": name,
                "status": "success" if success else "error",
                "message": message,
                "result": result
            })
        if txt_results:
            request._set_headers(200)
            request.wfile.write(json.dumps({
                "message": "Bulk grades processed (TXT)",
                "results": txt_results
            }).encode('utf-8'))
            return

        # If nothing worked
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Failed to process file. Ensure valid CSV or TXT format: name,score"}).encode('utf-8'))
        return

    except UnicodeDecodeError:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Failed to decode file. Ensure valid encoding"}).encode('utf-8'))
    except Exception as e:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": f"Failed to process file: {str(e)}"}).encode('utf-8'))
