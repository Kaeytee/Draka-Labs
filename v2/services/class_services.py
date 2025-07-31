import logging
from sqlalchemy.exc import DatabaseError
from database.db import SessionLocal
from models.classes import Class
from models.user import User
from models.school import School

# Configure logging for class service operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_classes(school_id):
    """
    Retrieve all classes for a given school.

    Queries the database for classes associated with the specified school_id.
    Returns a list of class dictionaries, including optional student details with
    profile images.

    Args:
        school_id (int): ID of the school to query classes for.

    Returns:
        list: List of dictionaries containing class details (id, name, school_id,
              description, academic_year, and optionally students with profile_image).

    Example:
        >>> get_classes(1)
        [
            {
                "id": 101,
                "name": "Math 101",
                "school_id": 1,
                "description": "Introductory Math",
                "academic_year": "2024-2025",
                "students": [
                    {"id": 1, "full_name": "John Doe", "profile_image": "uploads/123e4567-e89b-12d3-a456-426614174000.jpg"},
                    ...
                ]
            },
            ...
        ]

    Notes:
        - Validates school_id as an integer and checks existence.
        - Logs query attempts and errors for auditing.
        - In production, consider pagination for large class lists.
        - Includes student profile images for consistency with image handling.
    """
    if not isinstance(school_id, int):
        logger.error(f"Invalid school_id: {school_id}")
        return []

    session = SessionLocal()
    try:
        # Verify school exists
        if not session.query(School).filter_by(id=school_id).first():
            logger.error(f"School not found: ID {school_id}")
            return []

        classes = session.query(Class).filter(Class.school_id == school_id).all()
        result = []
        for cls in classes:
            class_data = {
                "id": cls.id,
                "name": cls.name,
                "school_id": cls.school_id,
                "description": cls.description,
                "academic_year": cls.academic_year
            }
            # Include students if relationship exists
            if cls.students:
                class_data["students"] = [
                    {
                        "id": student.id,
                        "full_name": student.full_name,
                        "profile_image": getattr(student, "profile_image", None)
                    } for student in cls.students
                ]
            result.append(class_data)
        logger.info(f"Retrieved {len(result)} classes for school_id {school_id}")
        return result

    except DatabaseError as e:
        logger.error(f"Database error retrieving classes for school_id {school_id}: {str(e)}")
        return []
    finally:
        session.close()

def create_class(name, school_id, academic_year, description=None):
    """
    Create a new class in the database.

    Creates a class with the specified name, school_id, academic_year, and optional
    description. Returns the created class details or an error message.

    Args:
        name (str): Name of the class (e.g., "Math 101").
        school_id (int): ID of the school the class belongs to.
        academic_year (str): Academic year (e.g., "2024-2025").
        description (str, optional): Description of the class (max 256 characters).

    Returns:
        tuple: (success: bool, message: str, result: dict) indicating success or failure.
               result contains class details (id, name, school_id, description, academic_year).

    Example:
        >>> create_class("Math 101", 1, "2024-2025", "Introductory Math")
        (True, "Class created successfully", {"id": 101, "name": "Math 101", ...})

    Notes:
        - Validates inputs and school_id existence.
        - Logs creation attempts and errors for auditing.
        - Uses database transactions with rollback on failure.
        - In production, ensure unique class names per school if required.
    """
    if not isinstance(name, str) or not name.strip():
        logger.error("Invalid class name provided")
        return False, "Class name must be a non-empty string", {}
    if not isinstance(school_id, int):
        logger.error(f"Invalid school_id: {school_id}")
        return False, "school_id must be an integer", {}
    if not isinstance(academic_year, str) or not academic_year.strip():
        logger.error(f"Invalid academic_year: {academic_year}")
        return False, "academic_year must be a non-empty string", {}
    if description is not None and (not isinstance(description, str) or len(description) > 256):
        logger.error(f"Invalid description: {description}")
        return False, "description must be a string (max 256 characters)", {}

    session = SessionLocal()
    try:
        # Verify school exists
        if not session.query(School).filter_by(id=school_id).first():
            logger.error(f"School not found: ID {school_id}")
            return False, "School not found", {}

        # Create class
        new_class = Class(
            name=name.strip(),
            school_id=school_id,
            academic_year=academic_year.strip(),
            description=description.strip() if description else None
        )
        session.add(new_class)
        session.commit()
        session.refresh(new_class)
        logger.info(f"Created class激烈的class_id {new_class.id} for school_id {school_id}")
        result = {
            "id": new_class.id,
            "name": new_class.name,
            "school_id": new_class.school_id,
            "description": new_class.description,
            "academic_year": new_class.academic_year
        }
        return True, "Class created successfully", result

    except DatabaseError as e:
        session.rollback()
        logger.error(f"Database error creating class: {str(e)}")
        return False, f"Database error: {str(e)}", {}
    finally:
        session.close()