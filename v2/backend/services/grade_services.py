from services.audit_log_services import log_audit
from database.db import SessionLocal
from models.grade import Grade
from models.user import User, UserRole

from models.course import Course
import json

def get_grades_for_student(student_id):
    """
    Returns all grades for a student, including course info, for CLI display.
    Output: List of dicts with course code, title, credit hours, score, letter grade, remarks, semester, date, etc.
    """
    db = SessionLocal()
    try:
        from models.grade import Grade
        from models.course import Course
        from models.user import User
        from models.classes import Class
        from models.school import School

        # Get student
        student = db.query(User).filter_by(id=student_id, role=UserRole.student).first()
        if not student:
            return []

        # Get all grades for this student
        grades = db.query(Grade).filter_by(student_id=student_id).all()
        if not grades:
            return []

        # Get all course ids
        course_ids = [g.course_id for g in grades]
        courses = db.query(Course).filter(Course.id.in_(course_ids)).all()
        course_map = {c.id: c for c in courses}

        # Get grading system from school
        school = student.school
        grading_system = []
        if school and getattr(school, 'grading_system', None):
            try:
                grading_system = json.loads(school.grading_system)
            except Exception:
                grading_system = []

        def get_letter_grade(value):
            if value is None or not grading_system:
                return None
            for rule in grading_system:
                if rule["min"] <= value <= rule["max"]:
                    return rule["grade"]
            return None

        def get_remarks(letter):
            if grading_system:
                for rule in grading_system:
                    if rule.get("grade") == letter and rule.get("remarks"):
                        return rule["remarks"]
            remarks_map = {
                "A+": "Excellent", "A": "Excellent", "A-": "Excellent",
                "B+": "Very Good", "B": "Very Good", "B-": "Good",
                "C+": "Good", "C": "Good", "C-": "Satisfactory",
                "D+": "Pass", "D": "Pass", "D-": "Pass",
                "E": "Marginal Pass", "F": "Fail"
            }
            return remarks_map.get(letter, "")

        result = []
        for grade in grades:
            course = course_map.get(grade.course_id)
            if not course:
                continue
            value = grade.value
            letter = get_letter_grade(value)
            remarks = get_remarks(letter)
            result.append({
                "course_id": course.id,
                "course_code": course.code,
                "course_title": course.title,
                "credit_hours": course.credit_hours,
                "score": value,
                "grade": letter,
                "remarks": remarks,
                "semester": grade.semester,
                "date": grade.created_at.isoformat() if getattr(grade, "created_at", None) is not None else None
            })
        return result
    except Exception as e:
        log_audit(student_id, "get_grades_for_student_error", str(e))
        return []
    finally:
        db.close()

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
            "created_at": grade.created_at.isoformat() if getattr(grade, "created_at", None) else None,
            "updated_at": grade.updated_at.isoformat() if getattr(grade, "updated_at", None) else None,
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
        teacher = db.query(User).filter_by(id=graded_by, role=UserRole.staff).first()
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
            "created_at": grade.created_at.isoformat() if getattr(grade, "created_at", None) else None,
            "updated_at": grade.updated_at.isoformat() if getattr(grade, "updated_at", None) else None,
            "graded_by": grade.graded_by
        }
    except Exception as e:
        db.rollback()
        log_audit(graded_by if 'graded_by' in locals() else None, "upload_grade_error", str(e))
        return False, str(e), None
    finally:
        db.close()