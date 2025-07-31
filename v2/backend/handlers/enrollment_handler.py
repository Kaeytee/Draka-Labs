import json
from services.enrollment_services import get_students
from utils.auth import require_role

@require_role(['admin'])
def handle_list_students(request):
    """
    GET /students?class_id=...
    List all students in a class.
    """
    from urllib.parse import urlparse, parse_qs
    query = parse_qs(urlparse(request.path).query)
    class_id = query.get("class_id", [None])[0]
    if not class_id:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "class_id is required"}).encode('utf-8'))
        return
    students = get_students(class_id)
    request._set_headers(200)
    request.wfile.write(json.dumps({"students": students}).encode('utf-8'))
