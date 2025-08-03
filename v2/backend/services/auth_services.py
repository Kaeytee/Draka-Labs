import hashlib
from models.user import User
from database.db import SessionLocal
from utils.session import generate_token

def login_user(identifier, password, school_id=None):
    """
    Authenticates a user.
    For students: identifier=email, must provide school_id.
    For staff/admin: identifier=username, must provide school_id.
    Returns (True, {token, role, user_id}) on success, (False, error_message) on failure.
    """
    db = SessionLocal()
    try:
        user = None
        if school_id is None:
            return False, "School ID is required."
        # Try student login by email
        user = db.query(User).filter_by(email=identifier, school_id=school_id).first()
        if user and user.role.value == "student":
            pass
        else:
            # Try staff/admin login by username
            user = db.query(User).filter_by(username=identifier, school_id=school_id).first()
        if user is None:
            return False, "Invalid credentials."
        hashed = hashlib.sha256(password.encode()).hexdigest()
        if getattr(user, "hashed_password", None) != hashed:
            return False, "Invalid credentials."
        token = generate_token(user.id, user.role.value)
        return True, {
            "token": token,
            "role": user.role.value,
            "user_id": user.id
        }
    except Exception as e:
        return False, str(e)
    finally:
        db.close()
