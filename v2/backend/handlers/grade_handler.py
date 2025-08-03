import json
from services.grade_services import get_grades_for_student
from utils.auth import require_role

@require_role(['admin', 'teacher', 'student'])
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
    
    # Students can only access their own grades
    if hasattr(request, 'user') and request.user:
        user_role = request.user.get('role')
        user_id = request.user.get('id')
        
        if user_role == 'student' and str(user_id) != str(student_id):
            request._set_headers(403)
            request.wfile.write(json.dumps({"error": "Students can only access their own grades"}).encode('utf-8'))
            return
    
    grades = get_grades_for_student(student_id)
    request._set_headers(200)
    request.wfile.write(json.dumps({"grades": grades}).encode('utf-8'))
