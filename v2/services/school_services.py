from database.db import SessionLocal
from models.school import School
from models.grade import Grade
import json

def update_grading_system(school_id, new_grading_system_json):
    """
    Update the grading system for a school and trigger grade recalculation.
    Returns (school, error_message) where error_message is None on success.
    """
    db = SessionLocal()
    try:
        school = db.query(School).filter_by(id=school_id).first()
        if not school:
            return None, "School not found."

        # Validate grading system format (basic check)
        if not isinstance(new_grading_system_json, list) or not all(
            isinstance(item, dict) and "grade" in item and "min" in item and "max" in item
            for item in new_grading_system_json
        ):
            return None, "Invalid grading system format."

        # Use model method for updating grading system
        school.update_grading_system(json.dumps(new_grading_system_json))
        db.commit()

        # Recalculate grades for all students in this school
        recalculate_grades(db, school_id, new_grading_system_json)

        return school, None
    except Exception as e:
        db.rollback()
        return None, str(e)
    finally:
        db.close()

def recalculate_grades(db, school_id, grading_system):
    """
    Recalculate grade mappings for all grades in the school.
    """
    # Example: Loop through all grades and update their letter grade if needed
    grades = db.query(Grade).join(Grade.course).filter_by(school_id=school_id).all()
    for grade in grades:
        # You can implement logic here to update grade fields based on new grading_system
        # For example, add a 'letter_grade' field to Grade and update it here
        pass
    db.commit()