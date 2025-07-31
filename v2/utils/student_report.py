"""
Student Report Utility
Generates a comprehensive report for a student, including academic year, class, courses, and grades.
"""
from typing import Optional, Dict, Any

def generate_student_report(student_id: int, academic_year: Optional[str] = None, db=None) -> Dict[str, Any]:
    """
    Generate a detailed report for a student for a given academic year.
    Args:
        student_id (int): The ID of the student.
        academic_year (str, optional): The academic year to filter by. Defaults to latest if not provided.
        db: SQLAlchemy session. If None, creates a new session.
    Returns:
        dict: Structured report with student info, class, courses, and grades.
    """
    from database.db import SessionLocal
    from models.user import User
    from models.classes import Class
    from models.enrollment import Enrollment
    from models.course import Course
    from models.grade import Grade
    import json
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    # Fetch student
    student = db.query(User).filter_by(id=student_id).first()
    if not student:
        if close_db:
            db.close()
        raise ValueError(f"Student with id {student_id} not found.")

    # Find enrollment for the academic year (or latest)
    enrollment_query = db.query(Enrollment).filter_by(student_id=student_id)
    if academic_year:
        enrollment_query = enrollment_query.join(Class).filter(Class.academic_year == academic_year)
    enrollment = enrollment_query.order_by(Enrollment.enrolled_at.desc()).first()
    if not enrollment:
        if close_db:
            db.close()
        raise ValueError(f"No enrollment found for student {student_id} in year '{academic_year or 'latest'}'.")

    class_ = db.query(Class).filter_by(id=enrollment.class_id).first()
    if not class_:
        if close_db:
            db.close()
        raise ValueError(f"Class with id {enrollment.class_id} not found.")

    # Fetch all courses for the class
    courses = db.query(Course).filter_by(class_id=class_.id).all()
    course_ids = [c.id for c in courses]

    # Fetch all grades for the student in these courses
    grades = db.query(Grade).filter(Grade.student_id == student_id, Grade.course_id.in_(course_ids)).all()
    grades_by_course = {g.course_id: g for g in grades}

    # Fetch grading system from the school (as JSON)
    school = class_.school
    grading_system = []
    if school and school.grading_system:
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
        # Professional, customizable remarks per grade
        remarks_map = {
            "A": "Excellent",
            "B": "Very Good",
            "C": "Good",
            "D": "Satisfactory",
            "E": "Pass",
            "F": "Fail"
        }
        return remarks_map.get(letter, "")

    course_reports = []
    for course in courses:
        grade = grades_by_course.get(course.id)
        value = grade.value if grade else None
        letter = get_letter_grade(value)
        remarks = get_remarks(letter)
        course_reports.append({
            "id": course.id,
            "title": course.title,
            "code": course.code,
            "credit_hours": course.credit_hours,
            "grade_value": value,
            "grade_id": grade.id if grade else None,
            "graded_at": grade.created_at.isoformat() if grade and grade.created_at else None,
            "letter_grade": letter,
            "remarks": remarks
        })

    report = {
        "student": {
            "id": student.id,
            "username": student.username,
            "full_name": student.full_name,
            "email": student.email,
            "gender": str(student.gender),
        },
        "academic_year": class_.academic_year,
        "class": {
            "id": class_.id,
            "name": class_.name,
            "description": class_.description,
        },
        "courses": course_reports
    }

    if close_db:
        db.close()

    return report
