from services.audit_log_services import log_audit
from database.db import SessionLocal
from models.grade import Grade
from models.user import User, UserRole
from models.course import Course

def get_grades(student_id, course_id):
    db = SessionLocal()
    try:
        grade = db.query(Grade).filter_by(student_id=student_id, course_id=course_id).first()
        if not grade:
            return None
        return {
            "grade_id": grade.id,
            "student_id": grade.student_id,
            "course_id": grade.course_id,
            "value": grade.value,
            "created_at": grade.created_at.isoformat() if grade.created_at else None,
            "updated_at": grade.updated_at.isoformat() if grade.updated_at else None,
            "graded_by": grade.graded_by
        }
    except Exception as e:
        log_audit(None, "get_grade_error", str(e))
        return None
    finally:
        db.close()

def upload_grade(student_id, course_id, value, graded_by):
    """
    Teacher uploads a grade for a student in a course.
    """
    db = SessionLocal()
    try:
        # Validate teacher
        teacher = db.query(User).filter_by(id=graded_by, role=UserRole.teacher).first()
        if not teacher:
            log_audit(graded_by, "upload_grade_error", "Grader is not a valid teacher")
            return False, "Grader is not a valid teacher", None

        # Validate student and course
        student = db.query(User).filter_by(id=student_id, role=UserRole.student).first()
        if not student:
            log_audit(graded_by, "upload_grade_error", f"Student not found: {student_id}")
            return False, "Student not found", None

        course = db.query(Course).filter_by(id=course_id, teacher_id=graded_by).first()
        if not course:
            log_audit(graded_by, "upload_grade_error", f"Course not found or not assigned to this teacher: {course_id}")
            return False, "Course not found or not assigned to this teacher", None

        # Create or update grade
        grade = db.query(Grade).filter_by(student_id=student_id, course_id=course_id).first()
        if grade:
            grade.value = value
        else:
            grade = Grade(
                student_id=student_id,
                course_id=course_id,
                value=value,
                graded_by=graded_by
            )
            db.add(grade)
        db.commit()
        db.refresh(grade)
        log_audit(graded_by, "upload_grade", f"Grade uploaded for student {student_id} in course {course_id}")
        return True, "Grade uploaded successfully", {
            "grade_id": grade.id,
            "student_id": grade.student_id,
            "course_id": grade.course_id,
            "value": grade.value,
            "created_at": grade.created_at.isoformat() if grade.created_at else None,
            "updated_at": grade.updated_at.isoformat() if grade.updated_at else None,
            "graded_by": grade.graded_by
        }
    except Exception as e:
        db.rollback()
        log_audit(graded_by if 'graded_by' in locals() else None, "upload_grade_error", str(e))
        return False, str(e), None
    finally:
        db.close()