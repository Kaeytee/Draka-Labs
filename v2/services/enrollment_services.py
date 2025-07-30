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