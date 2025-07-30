from database.db import SessionLocal
from models.course import Course
from models.classes import Class
from models.user import User, UserRole
from services.user_services import generate_username, generate_unique_username_email, generate_password

import random

def create_course(title, code, credit_hours, grading_type, class_id, school_initials, teacher_full_name=None):
    """
    Create a new course and auto-generate a teacher account if not provided.
    """
    db = SessionLocal()
    try:
        # Check if class exists
        class_obj = db.query(Class).filter_by(id=class_id).first()
        if not class_obj:
            return False, "Class not found", None

        # Auto-generate teacher if not provided
        if not teacher_full_name:
            teacher_full_name = f"Teacher for {title}"

        # Generate teacher account
        base_username = generate_username(teacher_full_name)
        username, email = generate_unique_username_email(db, base_username, school_initials, "teacher")
        user_id = ''.join(random.choices("0123456789", k=5))
        password = generate_password(school_initials, user_id)
        hashed_password = password  # Hash as needed

        teacher = User(
            username=username,
            full_name=teacher_full_name,
            hashed_password=hashed_password,
            email=email,
            role=UserRole.teacher,
            school_id=class_obj.school_id
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)

        # Create course
        course = Course(
            title=title,
            code=code,
            credit_hours=credit_hours,
            grading_type=grading_type,
            class_id=class_id,
            teacher_id=teacher.id
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        return True, "Course and teacher created successfully", {
            "course_id": course.id,
            "teacher_username": teacher.username,
            "teacher_email": teacher.email,
            "teacher_password": password
        }
    except Exception as e:
        db.rollback()
        return False, str(e), None
    finally:
        db.close()