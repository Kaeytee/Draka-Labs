import json
from services.course_services import create_course
from services.course_services import get_courses
from utils.auth import require_role

@require_role(['admin'])
def handle_create_course(request):
    content_length = int(request.headers.get('Content-Length', 0))
    body = request.rfile.read(content_length)
    try:
        data = json.loads(body)
    except Exception:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Invalid JSON body."}).encode('utf-8'))
        return
    # Validate required fields
    for field in ["title", "code", "credit_hours", "class_id", "school_initials"]:
        if field not in data:
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": f"Missing required field: {field}"}).encode('utf-8'))
            return
    if not isinstance(data["title"], str) or not isinstance(data["code"], str) or not isinstance(data["school_initials"], str):
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "title, code, and school_initials must be strings."}).encode('utf-8'))
        return
    if not isinstance(data["credit_hours"], int) or not isinstance(data["class_id"], int):
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "credit_hours and class_id must be integers."}).encode('utf-8'))
        return
    # Optional fields
    grading_type = data.get("grading_type")
    teacher_id = data.get("teacher_id")
    teacher_full_name = data.get("teacher_full_name")
    title = data["title"]
    code = data["code"]
    credit_hours = data["credit_hours"]
    class_id = data["class_id"]
    school_initials = data["school_initials"]
    success, message, result = create_course(
        title, code, credit_hours, grading_type, class_id, school_initials, teacher_id, teacher_full_name
    )
    if success:
        request._set_headers(201)
        request.wfile.write(json.dumps({
            "message": message,
            **result
        }).encode('utf-8'))
    else:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": message}).encode('utf-8'))



def handle_list_courses(request):
    """
    GET /courses?class_id=...
    List all courses for a class.
    """
    from urllib.parse import urlparse, parse_qs
    query = parse_qs(urlparse(request.path).query)
    class_id = query.get("class_id", [None])[0]
    if not class_id:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "class_id is required"}).encode('utf-8'))
        return
    courses = get_courses(class_id)
    request._set_headers(200)
    request.wfile.write(json.dumps({"courses": courses}).encode('utf-8'))
