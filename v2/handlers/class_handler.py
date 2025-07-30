import json
from services.class_services import get_classes
from utils.auth import require_role

@require_role(['admin'])
def handle_list_classes(request):
    """
    GET /classes?school_id=...
    List all classes for a school.
    """
    from urllib.parse import urlparse, parse_qs
    query = parse_qs(urlparse(request.path).query)
    school_id = query.get("school_id", [None])[0]
    if not school_id:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "school_id is required"}).encode('utf-8'))
        return
    classes = get_classes(school_id)
    request._set_headers(200)
    request.wfile.write(json.dumps({"classes": classes}).encode('utf-8'))
