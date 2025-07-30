from services.audit_log_services import log_audit
from database.db import SessionLocal
from models.classes import Class
from models.school import School

def create_class(name, description, academic_year, school_id, class_teacher_id=None):
    """
    Create a new class for a school. Only school admins can perform this action.
    """
    db = SessionLocal()
    try:
        # Check if school exists
        school = db.query(School).filter_by(id=school_id).first()
        if not school:
            log_audit(None, "create_class_error", f"School not found for id {school_id}")
            return False, "School not found", None

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
        log_audit(None, "create_class", f"Class {name} created for school {school_id}")
        return True, "Class created successfully", new_class
    except Exception as e:
        db.rollback()
        log_audit(None, "create_class_error", str(e))
        return False, str(e), None
    finally:
        db.close()