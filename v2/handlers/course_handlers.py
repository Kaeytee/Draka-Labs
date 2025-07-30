import json
from services.course_services import create_course

def handle_create_course(request):
    content_length = int(request.headers.get('Content-Length', 0))
    body = request.rfile.read(content_length)
    try:
        data = json.loads(body)
        title = data["title"]
        code = data["code"]
        credit_hours = data["credit_hours"]
        grading_type = data.get("grading_type")
        class_id = data["class_id"]
        school_initials = data["school_initials"]
        teacher_full_name = data.get("teacher_full_name")
        success, message, result = create_course(
            title, code, credit_hours, grading_type, class_id, school_initials, teacher_full_name
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
    except Exception as e:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))