import unittest
from services.accounts import register_school_admin
from models.school import School
from database.db import SessionLocal

class TestRegistration(unittest.TestCase):
    def setUp(self):
        import time
        self.db = SessionLocal()
        unique_suffix = str(int(time.time() * 1000))[-6:]
        self.school_name = f"Test School {unique_suffix}"
        self.full_name = "Test Admin"
        self.phone = "1234567890"
        self.email = f"test_{unique_suffix}@school.com"
        self.gender = "male"
        self.grading_system = None  # Should use default

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_register_school_admin(self):
        result = register_school_admin(
            self.school_name, self.full_name, self.phone, self.email, self.gender, self.grading_system
        )
        if result["status"] != "success":
            print("register_school_admin error:", result)
        self.assertEqual(result["status"], "success")
        self.assertIn("admin_username", result)
        self.assertIn("admin_email", result)
        self.assertIn("password", result)

if __name__ == "__main__":
    unittest.main()