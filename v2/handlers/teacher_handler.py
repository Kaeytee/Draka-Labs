import json
from services.teacher_services import get_teachers, assign_teacher_to_course
from utils.auth import require_role

@require_role(['admin'])
def handle_list_teachers(request):
    """
    GET /teachers?school_id=...
    List all teachers for a school.
    """
    from urllib.parse import urlparse, parse_qs
    query = parse_qs(urlparse(request.path).query)
    school_id = query.get("school_id", [None])[0]
    if not school_id:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "school_id is required"}).encode('utf-8'))
        return
    teachers = get_teachers(school_id)
    request._set_headers(200)
    request.wfile.write(json.dumps({"teachers": teachers}).encode('utf-8'))

@require_role(['admin'])
def handle_assign_teacher(request):
    """
    POST /assign_teacher
    Assign an existing teacher to a course.
    """
    content_length = int(request.headers.get('Content-Length', 0))
    body = request.rfile.read(content_length)
    try:
        data = json.loads(body)
    except Exception:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Invalid JSON body."}).encode('utf-8'))
        return
    teacher_id = data.get("teacher_id")
    course_id = data.get("course_id")
    if not teacher_id or not course_id:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "teacher_id and course_id required."}).encode('utf-8'))
        return
    success, message = assign_teacher_to_course(teacher_id, course_id)
    if success:
        request._set_headers(200)
        request.wfile.write(json.dumps({"message": message}).encode('utf-8'))
    else:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": message}).encode('utf-8'))
