from services.audit_log_services import log_audit
from database.db import SessionLocal
from models.course import Course
from models.classes import Class  
from models.user import User, UserRole
from services.accounts import create_teacher_account

def create_course(title, code, credit_hours, grading_type, class_id, school_initials, teacher_id=None, teacher_full_name=None):
    """
    Create a new course and assign a teacher (existing or auto-generated).

    Args:
        title (str): Course title
        code (str): Course code
        credit_hours (int): Number of credit hours
        grading_type (str): Type of grading system
        class_id (int): ID of the class
        school_initials (str): School identifier
        teacher_id (int, optional): ID of the teacher
        teacher_full_name (str, optional): Full name of the teacher

    Returns:
        tuple: (success: bool, message: str, data: dict or None)
    """
    db = SessionLocal()
    try:
        # Validate class existence
        class_obj = db.query(Class).filter_by(id=class_id).first()
        if not class_obj:
            log_audit(None, "create_course_error", f"Class not found for id {class_id}")
            return False, "Class not found", None

        # Assign existing teacher or auto-generate
        teacher = None
        password = None
        if teacher_id:
            teacher = db.query(User).filter_by(
                id=teacher_id, 
                school_id=class_obj.school_id, 
                role=UserRole.teacher
            ).first()
            if not teacher:
                log_audit(None, "create_course_error", f"Teacher not found or not in this school: {teacher_id}")
                return False, "Teacher not found or not in this school", None
        else:
            # Auto-generate teacher if no teacher_id provided
            if not teacher_full_name:
                teacher_full_name = f"Teacher for {title}"
            teacher, password = create_teacher_account(db, teacher_full_name, school_initials, class_obj.school_id)

        # Create course
        course = Course(
            title=title,
            code=code,
            credit_hours=credit_hours,
            grading_type=grading_type,
            class_id=class_id,
            teacher_id=teacher.id
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        log_audit(None, "create_course", f"Course {title} created for class {class_id} with teacher {teacher.id}")
        return True, "Course created successfully", {
            "course_id": course.id,
            "teacher_id": teacher.id,
            "teacher_password": password
        }

    except Exception as e:
        db.rollback()
        log_audit(None, "create_course_error", f"Error creating course: {str(e)}")
        return False, f"Error creating course: {str(e)}", None

    finally:
        db.close()