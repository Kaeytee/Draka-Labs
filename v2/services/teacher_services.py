from models.user import User, UserRole
from models.course import Course
from database.db import get_db_session

def get_teachers(school_id):
    """
    Returns a list of teachers for a given school_id.
    """
    session = get_db_session()
    try:
        teachers = session.query(User).filter(User.role == UserRole.staff, User.school_id == school_id).all()
        return [
            {
                "id": t.id,
                "full_name": t.full_name,
                "email": t.email,
                "username": t.username
            } for t in teachers
        ]
    finally:
        session.close()

def assign_teacher_to_course(teacher_id, course_id):
    """
    Assigns a teacher to a course.
    """
    session = get_db_session()
    try:
        teacher = session.query(User).filter(User.id == teacher_id, User.role == UserRole.staff).first()
        course = session.query(Course).filter(Course.id == course_id).first()
        if not teacher:
            return False, "Teacher not found."
        if not course:
            return False, "Course not found."
        course.teacher_id = teacher.id
        session.commit()
        return True, f"Teacher {teacher.full_name} assigned to course {course.title}."
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()
