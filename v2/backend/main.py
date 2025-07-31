from handlers.teacher_handler import handle_list_teachers, handle_assign_teacher
from handlers.school_handler import handle_list_schools
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
from database.db import engine, Base
from handlers.grade_handlers import handle_upload_grade, handle_bulk_grade_upload
from handlers.class_handler import handle_create_class
from handlers.course_handlers import handle_create_course
from handlers.enrollment_handlers import handle_enroll_student
from handlers.school_handler import handle_update_grading_system, handle_register_school
from handlers.class_handler import handle_list_classes
from handlers.course_handlers import handle_list_courses
from handlers.enrollment_handlers import handle_list_students
from handlers.grade_handlers import handle_list_grades
from handlers.auth_handler import handle_login  # Added import
from handlers.profile_handler import (
    handle_upload_profile_picture,
    handle_update_student_info,
    handle_view_profile,
    handle_update_profile,
    handle_change_password,
    handle_upload_profile_image
)
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


# --- Refactored SIAMSHandler with unified ROUTES dispatch table ---




ROUTES = {
    # School Registration & Management
    ("POST", "/register_school"): handle_register_school,
    ("GET", "/schools"): handle_list_schools,
    ("PUT", "/update_grading_system"): handle_update_grading_system,

    # Class Management
    ("POST", "/create_class"): handle_create_class,
    ("GET", "/classes"): handle_list_classes,

    # Course Management
    ("POST", "/create_course"): handle_create_course,
    ("GET", "/courses"): handle_list_courses,

    # Teacher Management
    ("GET", "/teachers"): handle_list_teachers,
    ("POST", "/assign_teacher"): handle_assign_teacher,

    # Student Enrollment
    ("POST", "/enroll_student"): handle_enroll_student,
    ("GET", "/students"): handle_list_students,

    # Grade Management
    ("POST", "/upload_grade"): handle_upload_grade,
    ("POST", "/upload_grades_bulk"): handle_bulk_grade_upload,  # Bulk upload endpoint
    ("GET", "/grades"): handle_list_grades,

    # Authentication
    ("POST", "/login"): handle_login,

    # Student Profile
    ("POST", "/student/profile_picture"): handle_upload_profile_picture,
    ("PATCH", "/student/profile"): handle_update_student_info,
    ("GET", "/profile"): handle_view_profile,
    ("POST", "/profile/update"): handle_update_profile,
    ("POST", "/profile/change_password"): handle_change_password,
    ("POST", "/profile/upload_image"): handle_upload_profile_image,
}

class SIAMSHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def _get_authenticated_user(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header:
            return None
        logger.warning("Authentication not fully implemented")
        return {"id": None, "role": "anonymous"}

    def do_GET(self):
        from urllib.parse import urlparse
        parsed = urlparse(self.path)
        clean_path = parsed.path.rstrip("/") or "/"
        if clean_path == "/":
            self._set_headers()
            response = {"message": "Backend is running successfully"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
        handler = ROUTES.get(("GET", clean_path))
        if handler:
            self.user = self._get_authenticated_user()
            handler(self)
        else:
            self._set_headers(404)
            response = {"error": "Not Found"}
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        from urllib.parse import urlparse
        parsed = urlparse(self.path)
        clean_path = parsed.path.rstrip("/") or "/"
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length <= 0:
                self._set_headers(400)
                response = {"error": "No data provided"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            request_body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(request_body) if request_body else {}
            except json.JSONDecodeError:
                self._set_headers(400)
                response = {"error": "Invalid JSON payload"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            self.user = self._get_authenticated_user()
            handler = ROUTES.get(("POST", clean_path))
            if handler:
                handler(self)
            else:
                self._set_headers(404)
                response = {"error": "Not Found"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        except Exception as e:
            logger.error(f"Error handling POST request: {str(e)}")
            self._set_headers(500)
            response = {"error": f"Internal Server Error: {str(e)}"}
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_PATCH(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length <= 0:
                self._set_headers(400)
                response = {"error": "No data provided"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            request_body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(request_body) if request_body else {}
            except json.JSONDecodeError:
                self._set_headers(400)
                response = {"error": "Invalid JSON payload"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            self.user = self._get_authenticated_user()
            handler = ROUTES.get(("PATCH", self.path))
            if handler:
                handler(self)
            else:
                self._set_headers(404)
                response = {"error": "Not Found"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        except Exception as e:
            logger.error(f"Error handling PATCH request: {str(e)}")
            self._set_headers(500)
            response = {"error": f"Internal Server Error: {str(e)}"}
            self.wfile.write(json.dumps(response).encode('utf-8'))





def run(server_class=HTTPServer, handler_class=SIAMSHandler, port=None):
    """Start the HTTP server."""
    # Use environment variable for port, default to 8000
    port = int(os.getenv('SIAMS_PORT', port or 8000))
    server_address = ('', port)
    try:
        httpd = server_class(server_address, handler_class)
        logger.info(f'Starting server on port {port}...')
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
        httpd.server_close()
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()
    run()