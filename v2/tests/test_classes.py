import unittest
from services.class_services import create_class
from database.db import SessionLocal

class TestClassCreation(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.school_id = 1  # Use a valid school_id from your test DB
        self.name = "JHS 1"
        self.description = "Junior High School 1"
        self.academic_year = "2025"

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_create_class(self):
        success, message, result = create_class(
            self.name, self.description, self.academic_year, self.school_id
        )
        self.assertTrue(success)
        self.assertIn("class_id", result)
        self.assertEqual(result["name"], self.name)

if __name__ == "__main__":
    unittest.main()