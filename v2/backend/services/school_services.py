import json
import logging
from sqlalchemy.exc import DatabaseError
from database.db import SessionLocal
from models.classes import Class
from models.user import User
from models.school import School

# Configure logging for school service operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def list_schools(school_id=None):
    """
    Retrieve all schools or a specific school by ID.

    Queries the database for schools, optionally filtered by school_id.
    Includes class and student data with profile images.

    Args:
        school_id (int, optional): ID of the school to retrieve. If None, returns all schools.

    Returns:
        list: List of dictionaries containing school details (id, name, grading_system,
              and optionally classes with students).

    Example:
        >>> list_schools(school_id=1)
        [
            {
                "id": 1,
                "name": "Springfield High",
                "grading_system": [{"grade": "A", "min": 90, "max": 100}, ...],
                "classes": [
                    {
                        "id": 101,
                        "name": "Math 101",
                        "students": [
                            {"id": 1, "full_name": "John Doe", "profile_image": "uploads/123e4567-e89b-12d3-a456-426614174000.jpg"},
                            ...
                        ]
                    },
                    ...
                ]
            }
        ]

    Notes:
        - Validates school_id if provided.
        - Logs query attempts and errors for auditing.
        - In production, add pagination for large school lists.
        - Includes student profile images via class relationship.
    """
    if school_id is not None and not isinstance(school_id, int):
        logger.error(f"Invalid school_id: {school_id}")
        return []

    db = SessionLocal()
    try:
        query = db.query(School)
        if school_id is not None:
            query = query.filter(School.id == school_id)
        schools = query.all()
        result = []
        for school in schools:
            school_data = {
                "id": school.id,
                "name": school.name,
                "grading_system": json.loads(school.grading_system) if school.grading_system else []
            }
            # Include classes and students
            classes = db.query(Class).filter(Class.school_id == school.id).all()
            school_data["classes"] = [
                {
                    "id": cls.id,
                    "name": cls.name,
                    "students": [
                        {
                            "id": student.id,
                            "full_name": student.full_name,
                            "profile_image": getattr(student, "profile_image", None)
                        } for student in cls.students
                    ]
                } for cls in classes
            ]
            result.append(school_data)
        logger.info(f"Retrieved {len(result)} schools for school_id={school_id}")
        return result

    except DatabaseError as e:
        logger.error(f"Database error retrieving schools for school_id={school_id}: {str(e)}")
        return []
    finally:
        db.close()

def update_school_grading_system(school_id, grading_system):
    """
    Update the grading system for a school.

    Updates the grading_system field (stored as JSON string) for the specified school.
    Validates the grading_system format and school existence.

    Args:
        school_id (int): ID of the school to update.
        grading_system (list): List of grading rules, each with grade, min, and max.

    Returns:
        tuple: (success: bool, message: str, result: dict or None)
               result contains school_id and updated grading_system.

    Example:
        >>> update_school_grading_system(1, [{"grade": "A", "min": 90, "max": 100}, {"grade": "B", "min": 80, "max": 89.9}])
        (True, "Grading system updated successfully", {
            "school_id": 1,
            "grading_system": [{"grade": "A", "min": 90, "max": 100}, {"grade": "B", "min": 80, "max": 89.9}]
        })

    Notes:
        - Validates school_id and grading_system format.
        - Ensures min/max are numeric and min <= max.
        - Logs updates and errors for auditing.
        - Uses database transactions with rollback on failure.
        - In production, consider unique grade checks and rate limiting.
    """
    if not isinstance(school_id, int):
        logger.error(f"Invalid school_id: {school_id}")
        return False, "school_id must be an integer", None
    if not isinstance(grading_system, list):
        logger.error(f"Invalid grading_system type for school_id {school_id}")
        return False, "grading_system must be a list", None
    for rule in grading_system:
        if not (isinstance(rule, dict) and "grade" in rule and "min" in rule and "max" in rule):
            logger.error(f"Invalid grading rule for school_id {school_id}")
            return False, "Each grading rule must be a dict with grade, min, and max", None
        if not (isinstance(rule["min"], (int, float)) and isinstance(rule["max"], (int, float)) and rule["min"] <= rule["max"]):
            logger.error(f"Invalid min/max for school_id {school_id}")
            return False, "min and max must be numbers with min <= max", None

    db = SessionLocal()
    try:
        school = db.query(School).filter_by(id=school_id).first()
        if not school:
            logger.error(f"School not found: ID {school_id}")
            return False, "School not found", None

        school.grading_system = json.dumps(grading_system)
        db.commit()
        db.refresh(school)
        logger.info(f"Updated grading system for school_id {school_id}")
        return True, "Grading system updated successfully", {
            "school_id": school.id,
            "grading_system": json.loads(school.grading_system)
        }

    except DatabaseError as e:
        db.rollback()
        logger.error(f"Database error updating grading system for school_id {school_id}: {str(e)}")
        return False, f"Database error: {str(e)}", None
    finally:
        db.close()