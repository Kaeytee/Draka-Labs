import logging

# Configure logging for enrollment service operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_students(class_id):
    """
    Retrieve all students enrolled in a given class.

    Args:
        class_id (int): ID of the class to retrieve students for.

    Returns:
        list: List of dictionaries containing student details (id, full_name, email, profile_image, enrollment_id).

    Example:
        >>> get_students(1)
        [
            {"id": 1, "full_name": "John Doe", "email": "john@example.com", "profile_image": "uploads/uuid.jpg", "enrollment_id": 10},
            ...
        ]

    Notes:
        - Validates class_id as an integer.
        - Logs query attempts and errors for auditing.
        - In production, consider pagination for large student lists.
        - Assumes Enrollment model links User and Class.
    """
    if not isinstance(class_id, int):
        logger.error(f"Invalid class_id: {class_id}")
        return []

    db = SessionLocal()
    try:
        enrollments = db.query(Enrollment).filter(Enrollment.class_id == class_id).all()
        students = []
        for enrollment in enrollments:
            student = db.query(User).filter(User.id == enrollment.student_id).first()
            if student:
                students.append({
                    "id": student.id,
                    "full_name": getattr(student, "full_name", None),
                    "email": getattr(student, "email", None),
                    "profile_image": getattr(student, "profile_image", None),
                    "enrollment_id": enrollment.id
                })
        logger.info(f"Retrieved {len(students)} students for class_id {class_id}")
        return students
    except Exception as e:
        logger.error(f"Error retrieving students for class_id {class_id}: {str(e)}")
        return []
    finally:
        db.close()
from services.audit_log_services import log_audit
from database.db import SessionLocal
from models.enrollment import Enrollment
from models.user import User, UserRole
from models.classes import Class
from services.accounts import create_student_account

def enroll_student(full_name, school_initials, class_id):
    """
    Enroll a student in a class, auto-generating their account if needed.
    """
    db = SessionLocal()
    try:
        class_obj = db.query(Class).filter_by(id=class_id).first()
        if not class_obj:
            log_audit(None, "enroll_student_error", f"Class not found for id {class_id}")
            return False, "Class not found", None

        # Auto-generate student account
        student, password = create_student_account(db, full_name, school_initials, class_obj.school_id)

        # Create enrollment record
        enrollment = Enrollment(student_id=student.id, class_id=class_id)
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

        log_audit(student.id, "enroll_student", f"Student {student.username} enrolled in class {class_id}")

        return True, "Student enrolled successfully", {
            "student_id": student.id,
            "student_username": student.username,
            "student_email": student.email,
            "student_password": password,
            "enrollment_id": enrollment.id
        }
    except Exception as e:
        db.rollback()
        log_audit(None, "enroll_student_error", str(e))
        return False, str(e), None
    finally:
        db.close()