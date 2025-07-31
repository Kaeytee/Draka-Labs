from database.db import SessionLocal
from models.user import User, UserRole
from models.school import School
from services.accounts import (
    generate_initials,
    generate_school_id,
    generate_username,
    generate_unique_username_email,
    generate_password
)
import hashlib

def register_user(full_name, password=None, role="student", school_name=None, user_id=None):
    """
    Register a new user in the system.
    - Usernames, emails, and passwords are generated using helpers from accounts.py.
    - Ensures uniqueness and follows the system's email/password conventions.
    """
    db = SessionLocal()
    try:
        if not school_name:
            return False, "School name is required", None

        initials = generate_initials(school_name)
        base_username = generate_username(full_name)
        username, email = generate_unique_username_email(db, base_username, initials, role)

        # Generate user_id if not provided
        if not user_id:
            user_id = generate_school_id(school_name, length=5)[-5:]  # Use last 5 digits for user_id

        # Auto-generate password if not provided
        if not password:
            password = generate_password(initials, user_id)
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        user = User(
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            email=email,
            role=UserRole(role)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return True, "User registered successfully", user
    except Exception as e:
        db.rollback()
        return False, str(e), None
    finally:
        db.close()