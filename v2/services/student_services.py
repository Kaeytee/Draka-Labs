"""
Student services module for student lookup and related operations.
"""
from models.user import User
from database.db import get_db_session



def student_lookup(name):
    """
    Looks up a student by their full name (case-insensitive).
    Returns a dict with student info if found, else None.
    Includes profile_picture_url if available.
    """
    session = get_db_session()
    try:
        # Split name for flexible matching (first, last, etc.)
        name_parts = [part.strip().lower() for part in name.split() if part.strip()]
        if not name_parts:
            return None
        # Query for user with role 'student' and name match
        query = session.query(User).filter(User.role == 'student')
        for part in name_parts:
            query = query.filter(User.full_name.ilike(f"%{part}%"))
        student = query.first()
        if student:
            return {
                "id": student.id,
                "full_name": student.full_name,
                "email": student.email,
                "role": student.role,
                "profile_picture_url": getattr(student, "profile_picture_url", None)
            }
        return None
    finally:
        session.close()

def set_student_profile_picture(student_id, url):
    """
    Sets the profile picture URL for a student.
    """
    session = get_db_session()
    try:
        student = session.query(User).filter(User.id == student_id, User.role == 'student').first()
        if not student:
            return False, "Student not found."
        student.profile_picture_url = url
        session.commit()
        return True, "Profile picture updated."
    finally:
        session.close()
