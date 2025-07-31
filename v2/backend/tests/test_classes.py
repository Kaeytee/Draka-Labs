import unittest
from services.class_services import create_class
from database.db import SessionLocal

class TestClassCreation(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        # Create a dummy admin user for testing
        import time
        from models.user import User, UserRole, Gender
        unique_suffix = str(int(time.time() * 1000))[-6:]
        admin_username = f"testadmin_{unique_suffix}"
        admin_email = f"testadmin_{unique_suffix}@school.com"
        admin_user = User(
            username=admin_username,
            full_name="Test Admin",
            hashed_password="dummyhash",
            email=admin_email,
            role=UserRole.admin,
            gender=Gender.male
        )
        self.db.add(admin_user)
        self.db.commit()
        self.db.refresh(admin_user)
        # Create a school for testing, using the admin user's id and generated initials
        from models.school import School
        from services.accounts import generate_initials
        self.school_name = f"Test School {unique_suffix}"
        initials = generate_initials(self.school_name)
        school = School(
            name=self.school_name,
            initials=initials,
            grading_system='[{"grade": "A", "min": 80, "max": 100}]',
            phone="1234567890",
            email=f"test_{unique_suffix}@school.com",
            address="123 Test St",
            admin_id=admin_user.id
        )
        self.db.add(school)
        self.db.commit()
        self.db.refresh(school)
        self.school_id = school.id
        self.name = "JHS 1"
        self.description = "Junior High School 1"
        self.academic_year = "2025"

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_create_class(self):
        # create_class(name, school_id, academic_year, description=None)
        success, message, result = create_class(
            self.name, self.school_id, self.academic_year, self.description
        )
        self.assertTrue(success)
        self.assertIn("id", result)
        self.assertEqual(result["name"], self.name)

if __name__ == "__main__":
    unittest.main()