import hashlib
import hmac
import time
import base64
import json
import os

SECRET_KEY = os.environ.get("SESSION_SECRET", "supersecretkey")

def generate_token(user_id, role, expires_in=3600):
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": int(time.time()) + expires_in
    }
    payload_b = json.dumps(payload).encode()
    signature = hmac.new(SECRET_KEY.encode(), payload_b, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(payload_b + b"." + signature).decode()
    return token

def decode_token(token):
    try:
        decoded = base64.urlsafe_b64decode(token.encode())
        payload_b, signature = decoded.rsplit(b".", 1)
        expected_sig = hmac.new(SECRET_KEY.encode(), payload_b, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        payload = json.loads(payload_b.decode())
        if payload["exp"] < int(time.time()):
            return None
        return payload
    except Exception:
        return None