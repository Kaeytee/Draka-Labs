from handlers.teacher_handler import handle_list_teachers, handle_assign_teacher
from handlers.school_handler import handle_list_schools
from http.server import BaseHTTPRequestHandler, HTTPServer
from api.cors import add_cors_headers, handle_cors_preflight
import json
import logging
from database.db import engine, Base, SessionLocal
from handlers.grade_handlers import handle_upload_grade, handle_bulk_grade_upload
from handlers.class_handler import handle_create_class
from handlers.course_handlers import handle_create_course
from handlers.enrollment_handlers import handle_enroll_student
from handlers.school_handler import handle_update_grading_system, handle_register_school
from handlers.class_handler import handle_list_classes
from handlers.course_handlers import handle_list_courses
from handlers.enrollment_handlers import handle_list_students
from handlers.grade_handlers import handle_list_grades
from handlers.auth_handler import handle_login
from handlers.profile_handler import (
    handle_upload_profile_picture,
    handle_update_student_info,
    handle_view_profile,
    handle_update_profile,
    handle_change_password,
    handle_upload_profile_image,
    handle_student_profile_by_id
)
import os
import jwt
import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

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
    ("POST", "/upload_grades_bulk"): handle_bulk_grade_upload,
    ("GET", "/grades"): handle_list_grades,

    # Authentication
    ("POST", "/login"): handle_login,
    ("POST", "/auth/login"): handle_login,

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
        add_cors_headers(self)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_OPTIONS(self):
        handle_cors_preflight(self)

    def _get_authenticated_user(self):
        auth_header = self.headers.get('Authorization')
        logger.debug(f"Authorization header: {auth_header}")
        
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.debug("No valid Authorization header provided")
            return None
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, os.getenv('JWT_SECRET', 'your-secret-key'), algorithms=['HS256'])
            user_id = payload.get('user_id')
            role = payload.get('role')
            
            logger.debug(f"JWT payload: user_id={user_id}, role={role}")
            
            if not user_id or not role:
                logger.debug("Invalid token payload")
                return None
            return {"id": user_id, "role": role}
        except jwt.ExpiredSignatureError:
            logger.debug("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid token: {str(e)}")
            return None

    def do_GET(self):
        from urllib.parse import urlparse
        import re
        parsed = urlparse(self.path)
        clean_path = parsed.path.rstrip("/") or "/"
        if clean_path == "/":
            self._set_headers()
            response = {"message": "Backend is running successfully"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
        
        # Check for static routes first
        handler = ROUTES.get(("GET", clean_path))
        if handler:
            self.user = self._get_authenticated_user()
            logger.info(f"GET {clean_path} - User: {self.user}")
            handler(self)
            return
        
        # Check for dynamic routes
        # Handle /students/{id}/profile
        if re.match(r'/students/\d+/profile', clean_path):
            self.user = self._get_authenticated_user()
            logger.info(f"GET {clean_path} - User: {self.user}")
            handle_student_profile_by_id(self)
            return
        
        # No route found
        self._set_headers(404)
        response = {"error": "Not Found"}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        from urllib.parse import urlparse
        parsed = urlparse(self.path)
        clean_path = parsed.path.rstrip("/") or "/"
        try:
            logger.debug(f"POST request to {clean_path}")
            
            # Get user before handling the request (except for login endpoints)
            if clean_path not in ["/login", "/auth/login"]:
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
            logger.debug(f"PATCH {self.path} - Payload: {request_body}")
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
    port = int(os.getenv('SIAMS_PORT', port or 8000))
    server_address = ('', port)
    httpd = None
    try:
        httpd = server_class(server_address, handler_class)
        logger.info(f'Starting server on port {port}...')
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
        if httpd is not None:
            httpd.server_close()
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()
    run()