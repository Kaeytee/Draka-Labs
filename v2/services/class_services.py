from database.db import SessionLocal
from models.classes import Class
from models.school import School
from models.user import User, UserRole

def create_class(name, description, academic_year, school_id, class_teacher_id=None):
    """
    Create a new class for a school. Only school admins can perform this action.
    """
    db = SessionLocal()
    try:
        # Check if school exists
        school = db.query(School).filter_by(id=school_id).first()
        if not school:
            return False, "School not found", None

        # Optionally check if teacher exists and belongs to this school
        if class_teacher_id:
            teacher = db.query(User).filter_by(id=class_teacher_id, school_id=school_id, role=UserRole.staff).first()
            if not teacher:
                return False, "Class teacher not found or not a staff of this school", None

        new_class = Class(
            name=name,
            description=description,
            academic_year=academic_year,
            school_id=school_id,
            class_teacher_id=class_teacher_id
        )
        db.add(new_class)
        db.commit()
        db.refresh(new_class)
        return True, "Class created successfully", new_class
    except Exception as e:
        db.rollback()
        return False, str(e), None
    finally:
        db.close()