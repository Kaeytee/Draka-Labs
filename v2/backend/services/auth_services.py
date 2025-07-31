import hashlib
from models.user import User
from database.db import SessionLocal
from utils.session import generate_token

def login_user(username, password):
    """
    Authenticates a user by username and password.
    Returns (True, {token, role, user_id}) on success, (False, error_message) on failure.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username=username).first()
        if not user:
            return False, "Invalid credentials."
        hashed = hashlib.sha256(password.encode()).hexdigest()
        if user.hashed_password != hashed:
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
