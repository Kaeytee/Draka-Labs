import unittest
from unittest.mock import patch, MagicMock
from handlers.enrollment_handlers import handle_enroll_student, handle_list_students
from handlers.auth_handler import handle_login
from handlers.grade_handlers import handle_upload_grade

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

class TestStudentEnrollmentAndLogin(unittest.TestCase):
    @patch("handlers.enrollment_handlers.enroll_student")
    def test_handle_enroll_student_valid(self, mock_enroll_student):
        mock_enroll_student.return_value = (True, "Student enrolled", {"student_id": 1, "class_id": 101, "email": "test@school.com", "password": "pass"})
        req = make_request(DummyRequest, headers={"Content-Length": "80"}, body=b'{"full_name": "John Doe", "school_initials": "XYZ", "class_id": 101}')
        req.rfile.read.return_value = req._body
        handle_enroll_student(req)
        self.assertEqual(req._status, 201)
        self.assertIn(b"Student enrolled", req.wfile.write.call_args[0][0])
        self.assertIn(b"email", req.wfile.write.call_args[0][0])
        self.assertIn(b"password", req.wfile.write.call_args[0][0])

    @patch("handlers.enrollment_handlers.enroll_student")
    def test_handle_enroll_student_invalid(self, mock_enroll_student):
        mock_enroll_student.return_value = (False, "full_name must be a non-empty string", {})
        req = make_request(DummyRequest, headers={"Content-Length": "80"}, body=b'{"full_name": "", "school_initials": "", "class_id": "abc"}')
        req.rfile.read.return_value = req._body
        handle_enroll_student(req)
        self.assertEqual(req._status, 400)
        if b"full_name must be a non-empty string" not in req.wfile.write.call_args[0][0]:
            print("Actual error message:", req.wfile.write.call_args[0][0])
        self.assertIn(b"full_name must be a non-empty string", req.wfile.write.call_args[0][0])

    def test_handle_enroll_student_no_data(self):
        req = make_request(DummyRequest, headers={"Content-Length": "0"})
        handle_enroll_student(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"No data provided", req.wfile.write.call_args[0][0])

    def test_handle_enroll_student_invalid_json(self):
        req = make_request(DummyRequest, headers={"Content-Length": "10"}, body=b'{bad json}')
        req.rfile.read.return_value = req._body
        handle_enroll_student(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"Invalid JSON body", req.wfile.write.call_args[0][0])

    @patch("handlers.auth_handler.login_user")
    def test_handle_login_valid(self, mock_login_user):
        mock_login_user.return_value = (True, {"token": "abc", "role": "student", "user_id": 1})
        req = make_request(DummyRequest, headers={"Content-Length": "50"}, body=b'{"username": "test@school.com", "password": "pass"}')
        req.rfile.read.return_value = req._body
        handle_login(req)
        self.assertEqual(req._status, 200)
        self.assertIn(b"token", req.wfile.write.call_args[0][0])

    @patch("handlers.auth_handler.login_user")
    def test_handle_login_invalid(self, mock_login_user):
        mock_login_user.return_value = (False, "Invalid credentials")
        req = make_request(DummyRequest, headers={"Content-Length": "50"}, body=b'{"username": "wrong", "password": "bad"}')
        req.rfile.read.return_value = req._body
        handle_login(req)
        self.assertEqual(req._status, 401)
        self.assertIn(b"Invalid credentials", req.wfile.write.call_args[0][0])

    def test_handle_login_no_data(self):
        req = make_request(DummyRequest, headers={"Content-Length": "0"})
        handle_login(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"Invalid JSON body", req.wfile.write.call_args[0][0])

class TestGradeUpload(unittest.TestCase):
    @patch("handlers.grade_handlers.upload_grade")
    def test_handle_upload_grade_invalid(self, mock_upload_grade):
        mock_upload_grade.return_value = (False, "Missing required field: value", None)
        req = make_request(DummyRequest, headers={"Content-Length": "80"}, body=b'{"student_id": 1, "course_id": 1, "graded_by": 1}')
        req.rfile.read.return_value = req._body
        handle_upload_grade(req)
        self.assertEqual(req._status, 400)
        if b"Missing required field: value" not in req.wfile.write.call_args[0][0]:
            print("Actual error message:", req.wfile.write.call_args[0][0])
        self.assertIn(b"Missing required field: value", req.wfile.write.call_args[0][0])

    @patch("handlers.grade_handlers.upload_grade")
    def test_handle_upload_grade_valid(self, mock_upload_grade):
        mock_upload_grade.return_value = (True, "Grade uploaded successfully", {"grade_id": 1})
        req = make_request(DummyRequest, headers={"Content-Length": "80"}, body=b'{"student_id": 1, "course_id": 1, "value": 90, "graded_by": 1}')
        req.rfile.read.return_value = req._body
        handle_upload_grade(req)
        self.assertIn(req._status, (200, 201))
        self.assertIn(b"Grade uploaded successfully", req.wfile.write.call_args[0][0])

    def test_handle_upload_grade_no_data(self):
        req = make_request(DummyRequest, headers={"Content-Length": "0"})
        handle_upload_grade(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"No data provided", req.wfile.write.call_args[0][0])

    def test_handle_upload_grade_invalid_json(self):
        req = make_request(DummyRequest, headers={"Content-Length": "10"}, body=b'{bad json}')
        req.rfile.read.return_value = req._body
        handle_upload_grade(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"Invalid JSON body", req.wfile.write.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
