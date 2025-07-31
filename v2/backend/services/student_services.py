import logging
from sqlalchemy.exc import DatabaseError
from database.db import SessionLocal
from models.user import User

# Configure logging for student service operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def student_lookup(name):
    """
    Look up a student by their full name (case-insensitive).

    Searches for a student by matching name parts against the User.full_name field.
    Returns a dictionary with student details, including profile image, if found.

    Args:
        name (str): Full name of the student to look up.

    Returns:
        dict or None: Dictionary with student details (id, full_name, email, role,
                      profile_image) if found, else None.

    Example:
        >>> student_lookup("John Doe")
        {
            "id": 1,
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "role": "student",
            "profile_image": "uploads/123e4567-e89b-12d3-a456-426614174000.jpg"
        }

    Notes:
        - Performs case-insensitive partial matching on name parts.
        - Validates input to prevent empty or malformed names.
        - Logs lookup attempts for auditing.
        - In production, consider stricter matching or additional identifiers (e.g., student ID).
        - Uses profile_image field for consistency with file-based uploads.
    """
    if not name or not isinstance(name, str) or not name.strip():
        logger.error("Invalid name provided for student lookup")
        return None

    session = SessionLocal()
    try:
        # Split name for flexible matching
        name_parts = [part.strip().lower() for part in name.split() if part.strip()]
        if not name_parts:
            logger.error("No valid name parts provided for student lookup")
            return None

        # Query for student with role 'student' and name match
        query = session.query(User).filter(User.role == 'student')
        for part in name_parts:
            query = query.filter(User.full_name.ilike(f"%{part}%"))
        student = query.first()

        if student:
            logger.info(f"Found student: {student.full_name} (ID: {student.id})")
            return {
                "id": student.id,
                "full_name": student.full_name,
                "email": student.email,
                "role": student.role,
                "profile_image": getattr(student, "profile_image", None)
            }
        logger.info(f"No student found for name: {name}")
        return None

    except DatabaseError as e:
        logger.error(f"Database error during student lookup for name '{name}': {str(e)}")
        return None
    finally:
        session.close()

def set_student_profile_picture(student_id, url):
    """
    Set the profile image URL for a student (DEPRECATED).

    Updates the student's profile_image field with the provided URL. Restricted to
    students. This function is deprecated in favor of file-based uploads via
    handle_upload_profile_image.

    Args:
        student_id (int): ID of the student.
        url (str): URL of the profile image.

    Returns:
        tuple: (success: bool, message: str) indicating success or failure.

    Example:
        >>> set_student_profile_picture(1, "uploads/123e4567-e89b-12d3-a456-426614174000.jpg")
        (True, "Profile image updated.")

    Notes:
        - Deprecated in favor of handle_upload_profile_image for direct file uploads.
        - Validates URL format and student existence.
        - Logs all update attempts for auditing.
        - In production, consider removing or enhancing URL validation (e.g., check accessibility).
        - Uses profile_image field for consistency with file-based uploads.
    """
    if not isinstance(student_id, int) or not isinstance(url, str) or not url.strip():
        logger.error(f"Invalid input: student_id={student_id}, url={url}")
        return False, "Invalid student_id or URL."

    # Basic URL validation (could be enhanced with regex or requests.head)
    if not url.startswith(('http://', 'https://', 'uploads/')):
        logger.error(f"Invalid URL scheme for student_id {student_id}: {url}")
        return False, "URL must start with http://, https://, or uploads/"

    session = SessionLocal()
    try:
        student = session.query(User).filter(User.id == student_id, User.role == 'student').first()
        if not student:
            logger.error(f"Student not found: ID {student_id}")
            return False, "Student not found."

        student.profile_image = url
        session.commit()
        logger.info(f"Updated profile image for student_id {student_id}: {url}")
        return True, "Profile image updated."

    except DatabaseError as e:
        session.rollback()
        logger.error(f"Database error updating profile image for student_id {student_id}: {str(e)}")
        return False, f"Database error: {str(e)}"
    finally:
        session.close()