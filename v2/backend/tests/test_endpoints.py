import unittest
from unittest.mock import patch, MagicMock
from handlers.school_handler import handle_register_school, handle_list_schools
from handlers.course_handlers import handle_create_course, handle_list_courses
from handlers.teacher_handler import handle_list_teachers, handle_assign_teacher
from handlers.enrollment_handlers import handle_list_students, handle_enroll_student
from handlers.grade_handlers import handle_list_grades, handle_upload_grade
from handlers.auth_handler import handle_login
from handlers.profile_handler import (
    handle_upload_profile_picture,
    handle_update_student_info,
    handle_view_profile,
    handle_update_profile,
    handle_change_password,
    handle_upload_profile_image
)

from utils.test_utils import make_request
from utils.test_utils import make_user

class DummyRequest:
    def __init__(self, method="POST", path="/", headers=None, body=None, user=None, role="admin"):
        self.method = method
        self.path = path
        self.headers = headers or {}
        self.rfile = MagicMock()
        self.wfile = MagicMock()
        # Always provide a user with the correct role by default
        if user is not None:
            self.user = user
        else:
            self.user = make_user(role=role)
        self._body = body or b''
        self._status = None
        self._headers = {}
    def _set_headers(self, status=200, content_type="application/json"):
        self._status = status
        self._headers["Content-type"] = content_type
    def read(self, n):
        return self._body
    def set_user_role(self, role):
        self.user.role.value = role

class TestSchoolHandlers(unittest.TestCase):
    @patch("handlers.school_handler.register_school_admin")
    def test_handle_register_school_valid(self, mock_register):
        mock_register.return_value = {"status": "success", "school_id": 1, "admin_email": "admin@school.com"}
        req = make_request(DummyRequest, headers={"Content-Length": "100"}, body=b'{"school_name": "Test School", "full_name": "Admin", "phone": "123", "email": "admin@school.com"}')
        req.rfile.read.return_value = req._body
        handle_register_school(req)
        self.assertEqual(req._status, 201)
        self.assertIn(b"success", req.wfile.write.call_args[0][0])

    @patch("handlers.school_handler.register_school_admin")
    def test_handle_register_school_missing_field(self, mock_register):
        req = make_request(DummyRequest, headers={"Content-Length": "100"}, body=b'{"school_name": "Test School", "full_name": "Admin", "phone": "123"}')
        req.rfile.read.return_value = req._body
        handle_register_school(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"Missing required field", req.wfile.write.call_args[0][0])

    def test_handle_register_school_invalid_json(self):
        req = make_request(DummyRequest, headers={"Content-Length": "10"}, body=b'{bad json}')
        req.rfile.read.return_value = req._body
        handle_register_school(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"Invalid JSON body", req.wfile.write.call_args[0][0])

class TestCourseHandlers(unittest.TestCase):
    @patch("handlers.course_handlers.create_course")
    def test_handle_create_course_valid(self, mock_create):
        mock_create.return_value = (True, "Course created", {"id": 1, "title": "Math"})
        req = make_request(DummyRequest, headers={"Content-Length": "100"}, body=b'{"title": "Math", "code": "M101", "credit_hours": 3, "class_id": 1, "school_initials": "TS"}')
        req.rfile.read.return_value = req._body
        handle_create_course(req)
        self.assertEqual(req._status, 201)
        self.assertIn(b"Course created", req.wfile.write.call_args[0][0])

    @patch("handlers.course_handlers.create_course")
    def test_handle_create_course_missing_field(self, mock_create):
        req = make_request(DummyRequest, headers={"Content-Length": "100"}, body=b'{"title": "Math", "code": "M101", "credit_hours": 3, "class_id": 1}')
        req.rfile.read.return_value = req._body
        handle_create_course(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"Missing required field", req.wfile.write.call_args[0][0])

class TestTeacherHandlers(unittest.TestCase):
    @patch("handlers.teacher_handler.get_teachers")
    def test_handle_list_teachers_valid(self, mock_get_teachers):
        mock_get_teachers.return_value = [{"id": 1, "full_name": "Teacher A"}]
        req = make_request(DummyRequest, method="GET", path="/teachers?school_id=1")
        handle_list_teachers(req)
        self.assertEqual(req._status, 200)
        self.assertIn(b"Teacher A", req.wfile.write.call_args[0][0])

    @patch("handlers.teacher_handler.assign_teacher_to_course")
    def test_handle_assign_teacher_valid(self, mock_assign):
        mock_assign.return_value = (True, "Assigned")
        req = make_request(DummyRequest, headers={"Content-Length": "50"}, body=b'{"teacher_id": 1, "course_id": 2}')
        req.rfile.read.return_value = req._body
        handle_assign_teacher(req)
        self.assertEqual(req._status, 200)
        self.assertIn(b"Assigned", req.wfile.write.call_args[0][0])

class TestEnrollmentHandlers(unittest.TestCase):
    @patch("handlers.enrollment_handlers.get_students")
    def test_handle_list_students_valid(self, mock_get_students):
        mock_get_students.return_value = [{"id": 1, "full_name": "Student A"}]
        req = make_request(DummyRequest, method="GET", path="/students?class_id=1")
        handle_list_students(req)
        self.assertEqual(req._status, 200)
        self.assertIn(b"Student A", req.wfile.write.call_args[0][0])

class TestGradeHandlers(unittest.TestCase):
    @patch("handlers.grade_handlers.get_grades")
    def test_handle_list_grades_valid(self, mock_get_grades):
        mock_get_grades.return_value = [{"course_id": 1, "value": 90}]
        req = make_request(DummyRequest, method="GET", path="/grades?student_id=1")
        handle_list_grades(req)
        self.assertEqual(req._status, 200)
        self.assertIn(b"course_id", req.wfile.write.call_args[0][0])

class TestAuthHandlers(unittest.TestCase):
    @patch("handlers.auth_handler.login_user")
    def test_handle_login_valid(self, mock_login):
        mock_login.return_value = (True, {"token": "abc", "role": "admin", "user_id": 1})
        req = make_request(DummyRequest, headers={"Content-Length": "50"}, body=b'{"username": "admin", "password": "pass"}')
        req.rfile.read.return_value = req._body
        handle_login(req)
        self.assertEqual(req._status, 200)
        self.assertIn(b"token", req.wfile.write.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
