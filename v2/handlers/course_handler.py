import json
from services.course_services import get_courses
from utils.auth import require_role

@require_role(['admin'])
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
