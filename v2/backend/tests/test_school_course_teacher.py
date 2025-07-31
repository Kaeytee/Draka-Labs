import unittest
from unittest.mock import patch, MagicMock
from handlers.school_handler import handle_register_school, handle_list_schools
from handlers.course_handlers import handle_create_course, handle_list_courses
from handlers.teacher_handler import handle_list_teachers, handle_assign_teacher
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
    def test_handle_register_school_valid(self, mock_register_school_admin):
        mock_register_school_admin.return_value = {"status": "success", "school_id": 1}
        req = make_request(DummyRequest, headers={"Content-Length": "100"}, body=b'{"school_name": "Test School", "full_name": "Admin", "phone": "123", "email": "admin@test.com"}')
        req.rfile.read.return_value = req._body
        handle_register_school(req)
        self.assertEqual(req._status, 201)
        self.assertIn(b"success", req.wfile.write.call_args[0][0])

@patch("handlers.school_handler.register_school_admin")
def test_handle_register_school_invalid(self, mock_register_school_admin):
    mock_register_school_admin.return_value = {"status": "error", "message": "Missing required field: school_name"}
    req = make_request(DummyRequest, headers={"Content-Length": "100"}, body=b'{"school_name": "", "full_name": "", "phone": "", "email": ""}')
    req.rfile.read.return_value = req._body
    handle_register_school(req)
    self.assertEqual(req._status, 400)
    self.assertIn(b"Missing required field: school_name", req.wfile.write.call_args[0][0])

    def test_handle_register_school_no_data(self):
        req = make_request(DummyRequest, headers={"Content-Length": "0"})
        handle_register_school(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"No data provided", req.wfile.write.call_args[0][0])

    def test_handle_register_school_invalid_json(self):
        req = make_request(DummyRequest, headers={"Content-Length": "10"}, body=b'{bad json}')
        req.rfile.read.return_value = req._body
        handle_register_school(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"Invalid JSON body", req.wfile.write.call_args[0][0])

    @patch("handlers.school_handler.list_schools")
    def test_handle_list_schools(self, mock_list_schools):
        mock_list_schools.return_value = [{"id": 1, "name": "Test School"}]
        req = make_request(DummyRequest, method="GET", path="/schools?school_id=1")
        handle_list_schools(req)
        self.assertEqual(req._status, 200)
        self.assertIn(b"Test School", req.wfile.write.call_args[0][0])

class TestCourseHandlers(unittest.TestCase):
    @patch("handlers.course_handlers.create_course")
    def test_handle_create_course_valid(self, mock_create_course):
        mock_create_course.return_value = (True, "Course created", {"id": 1, "title": "Math"})
        req = make_request(DummyRequest, headers={"Content-Length": "100"}, body=b'{"title": "Math", "code": "MATH101", "credit_hours": 3, "class_id": 1, "school_initials": "TS"}')
        req.rfile.read.return_value = req._body
        handle_create_course(req)
        self.assertEqual(req._status, 201)
        self.assertIn(b"Course created", req.wfile.write.call_args[0][0])

@patch("handlers.course_handlers.create_course")
def test_handle_create_course_invalid(self, mock_create_course):
    mock_create_course.return_value = (False, "credit_hours and class_id must be integers.", {})
    req = make_request(DummyRequest, headers={"Content-Length": "100"}, body=b'{"title": "", "code": "", "credit_hours": "bad", "class_id": "abc", "school_initials": ""}')
    req.rfile.read.return_value = req._body
    handle_create_course(req)
    self.assertEqual(req._status, 400)
    self.assertIn(b"credit_hours and class_id must be integers.", req.wfile.write.call_args[0][0])

def test_handle_create_course_no_data(self):
    req = make_request(DummyRequest, headers={"Content-Length": "0"})
    handle_create_course(req)
    self.assertEqual(req._status, 400)
    self.assertIn(b"Invalid JSON body", req.wfile.write.call_args[0][0])

    def test_handle_create_course_invalid_json(self):
        req = make_request(DummyRequest, headers={"Content-Length": "10"}, body=b'{bad json}')
        req.rfile.read.return_value = req._body
        handle_create_course(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"Invalid JSON body", req.wfile.write.call_args[0][0])

    @patch("handlers.course_handlers.get_courses")
    def test_handle_list_courses(self, mock_get_courses):
        mock_get_courses.return_value = [{"id": 1, "title": "Math"}]
        req = make_request(DummyRequest, method="GET", path="/courses?class_id=1")
        handle_list_courses(req)
        self.assertEqual(req._status, 200)
        self.assertIn(b"Math", req.wfile.write.call_args[0][0])

class TestTeacherHandlers(unittest.TestCase):
    @patch("handlers.teacher_handler.get_teachers")
    def test_handle_list_teachers(self, mock_get_teachers):
        mock_get_teachers.return_value = [{"id": 1, "full_name": "Jane Teacher"}]
        req = make_request(DummyRequest, method="GET", path="/teachers?school_id=1")
        handle_list_teachers(req)
        self.assertEqual(req._status, 200)
        self.assertIn(b"Jane Teacher", req.wfile.write.call_args[0][0])
@patch("handlers.teacher_handler.assign_teacher_to_course")
def test_handle_assign_teacher(self, mock_assign_teacher):
    mock_assign_teacher.return_value = (True, "Teacher assigned")
    req = make_request(DummyRequest, headers={"Content-Length": "50"}, body=b'{"teacher_id": 1, "course_id": 2}')
    req.rfile.read.return_value = req._body
    handle_assign_teacher(req)
    self.assertEqual(req._status, 200)
    self.assertIn(b"Teacher assigned", req.wfile.write.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
