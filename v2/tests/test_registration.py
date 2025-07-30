import unittest
from services.accounts import register_school_admin
from models.school import School
from database.db import SessionLocal

class TestRegistration(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.school_name = "Test School"
        self.full_name = "Test Admin"
        self.phone = "1234567890"
        self.email = "test@school.com"
        self.grading_system = None  # Should use default

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_register_school_admin(self):
        success, message, result = register_school_admin(
            self.school_name, self.full_name, self.phone, self.email, self.grading_system
        )
        self.assertTrue(success)
        self.assertIn("school_id", result)
        self.assertIn("admin_username", result)
        self.assertIn("admin_email", result)

if __name__ == "__main__":
    unittest.main()