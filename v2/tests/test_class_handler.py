import unittest
from unittest.mock import patch, MagicMock
from handlers.class_handler import handle_create_class, handle_list_classes
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

class TestClassHandlers(unittest.TestCase):
    @patch("handlers.class_handler.create_class")
    def test_handle_create_class_valid(self, mock_create_class):
        mock_create_class.return_value = (True, "Class created successfully", {"id": 1, "name": "Math"})
        req = make_request(DummyRequest, headers={"Content-Length": "50"}, body=b'{"name": "Math", "school_id": 1, "academic_year": "2025"}')
        req.rfile.read.return_value = req._body
        handle_create_class(req)
        self.assertEqual(req._status, 201)
        self.assertIn(b"Class created successfully", req.wfile.write.call_args[0][0])

    @patch("handlers.class_handler.create_class")
    def test_handle_create_class_invalid(self, mock_create_class):
        mock_create_class.return_value = (False, "Invalid data", {})
        req = make_request(DummyRequest, headers={"Content-Length": "50"}, body=b'{"name": "", "school_id": "abc", "academic_year": ""}')
        req.rfile.read.return_value = req._body
        handle_create_class(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"Invalid data", req.wfile.write.call_args[0][0])

    def test_handle_create_class_no_data(self):
        req = make_request(DummyRequest, headers={"Content-Length": "0"})
        handle_create_class(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"No data provided", req.wfile.write.call_args[0][0])

    def test_handle_create_class_invalid_json(self):
        req = make_request(DummyRequest, headers={"Content-Length": "10"}, body=b'{bad json}')
        req.rfile.read.return_value = req._body
        handle_create_class(req)
        self.assertEqual(req._status, 400)
        self.assertIn(b"Invalid JSON body", req.wfile.write.call_args[0][0])

# Similar unit tests can be written for other handlers following this pattern.
# For brevity, only class handler tests are shown here. You can expand for all endpoints.

if __name__ == "__main__":
    unittest.main()
