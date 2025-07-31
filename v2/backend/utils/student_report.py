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

    # --- GPA Calculation Utilities ---
    def grade_point(letter):
        # Custom mapping: use school's grading system if it includes points, else fallback to standard
        # Example grading_system entry: {"grade": "A", "min": 80, "max": 100, "points": 4.0}
        if grading_system:
            for rule in grading_system:
                if rule.get("grade") == letter:
                    # Use custom points if present, else fallback
                    return float(rule.get("points", 0.0))
        # Fallback: standard 4.0 scale with plus/minus
        points = {
            "A+": 4.0, "A": 4.0, "A-": 3.7,
            "B+": 3.3, "B": 3.0, "B-": 2.7,
            "C+": 2.3, "C": 2.0, "C-": 1.7,
            "D+": 1.3, "D": 1.0, "D-": 0.7,
            "E": 0.5, "F": 0.0
        }
        return points.get(letter, 0.0)

    def get_letter_grade(value):
        if value is None or not grading_system:
            return None
        for rule in grading_system:
            if rule["min"] <= value <= rule["max"]:
                return rule["grade"]
        return None

    def get_remarks(letter):
        # Optionally, allow remarks in grading_system
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

    # --- Per-Year/Level Reporting ---
    # For university: fetch all enrollments, group by academic_year (level 100, 200, ...)
    all_enrollments = db.query(Enrollment).filter_by(student_id=student_id).join(Class).order_by(Class.academic_year).all()
    year_reports = {}
    accumulated_points = 0.0
    accumulated_credits = 0

    for enr in all_enrollments:
        yr = db.query(Class).filter_by(id=enr.class_id).first().academic_year
        if yr not in year_reports:
            year_reports[yr] = {"courses": [], "total_points": 0.0, "total_credits": 0}
        class_courses = db.query(Course).filter_by(class_id=enr.class_id).all()
        for course in class_courses:
            grade = db.query(Grade).filter_by(student_id=student_id, course_id=course.id).first()
            value = grade.value if grade else None
            letter = get_letter_grade(value)
            remarks = get_remarks(letter)
            points = grade_point(letter) * course.credit_hours if letter else 0.0
            year_reports[yr]["courses"].append({
                "id": course.id,
                "title": course.title,
                "code": course.code,
                "credit_hours": course.credit_hours,
                "grade_value": value,
                "grade_id": grade.id if grade else None,
                "graded_at": grade.created_at.isoformat() if grade and grade.created_at else None,
                "letter_grade": letter,
                "remarks": remarks,
                "grade_points": points
            })
            if letter and course.credit_hours:
                year_reports[yr]["total_points"] += points
                year_reports[yr]["total_credits"] += course.credit_hours
                accumulated_points += points
                accumulated_credits += course.credit_hours

    # Current year report (for the requested academic_year)
    course_reports = []
    gpa = None
    if academic_year and academic_year in year_reports:
        course_reports = year_reports[academic_year]["courses"]
        if year_reports[academic_year]["total_credits"] > 0:
            gpa = round(year_reports[academic_year]["total_points"] / year_reports[academic_year]["total_credits"], 2)
    else:
        # Default to latest year
        if year_reports:
            latest_year = sorted(year_reports.keys())[-1]
            course_reports = year_reports[latest_year]["courses"]
            if year_reports[latest_year]["total_credits"] > 0:
                gpa = round(year_reports[latest_year]["total_points"] / year_reports[latest_year]["total_credits"], 2)

    accumulated_gpa = round(accumulated_points / accumulated_credits, 2) if accumulated_credits > 0 else None

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
        "courses": course_reports,
        "gpa": gpa,
        "accumulated_gpa": accumulated_gpa,
        "yearly_reports": year_reports
    }

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
