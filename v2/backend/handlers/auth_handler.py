from models.user import User, UserRole
from database.db import SessionLocal
import hashlib
import jwt
import datetime
import os
import logging
import json

logger = logging.getLogger(__name__)

def handle_login(handler):
    """Handle user login and return a JWT token."""
    try:
        # Get content length and read request body
        content_length = int(handler.headers.get('Content-Length', 0))
        if content_length <= 0:
            handler._set_headers(400)
            response = {"success": False, "message": "No data provided"}
            handler.wfile.write(json.dumps(response).encode('utf-8'))
            return
            
        raw_data = handler.rfile.read(content_length).decode('utf-8')
        data = json.loads(raw_data)

        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        logger.info(f"Login attempt: email={email}, role={role}")

        if not password or not email:
            handler._set_headers(400)
            response = {"success": False, "message": "Email and password are required"}
            handler.wfile.write(json.dumps(response).encode('utf-8'))
            return

        session = SessionLocal()
        try:
            user = session.query(User).filter_by(email=email).first()
            if not user:
                handler._set_headers(401)
                response = {"success": False, "message": "User not found"}
                handler.wfile.write(json.dumps(response).encode('utf-8'))
                return

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if str(user.hashed_password) != hashed_password:
                handler._set_headers(401)
                response = {"success": False, "message": "Incorrect password"}
                handler.wfile.write(json.dumps(response).encode('utf-8'))
                return

            if role and user.role.value != role:
                handler._set_headers(401)
                response = {"success": False, "message": f"User is not a {role}"}
                handler.wfile.write(json.dumps(response).encode('utf-8'))
                return

            # Generate JWT token
            payload = {
                'user_id': user.id,
                'role': user.role.value,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }
            token = jwt.encode(payload, os.getenv('JWT_SECRET', 'your-secret-key'), algorithm='HS256')

            handler._set_headers(200)
            response = {
                "success": True,
                "data": {
                    "token": token,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "role": user.role.value,
                        "full_name": user.full_name,
                        "email": user.email
                    }
                },
                "message": "Login successful"
            }
            logger.info(f"User {user.username or user.email} logged in successfully")
            handler.wfile.write(json.dumps(response).encode('utf-8'))
        finally:
            session.close()
    except json.JSONDecodeError:
        handler._set_headers(400)
        response = {"success": False, "message": "Invalid JSON payload"}
        handler.wfile.write(json.dumps(response).encode('utf-8'))
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        handler._set_headers(500)
        response = {"success": False, "message": f"Internal server error: {str(e)}"}
        handler.wfile.write(json.dumps(response).encode('utf-8'))