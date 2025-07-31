import json
from services.auth_services import login_user

def handle_login(request):
    """
    POST /login
    Body: { "username": "...", "password": "..." }
    Returns: { "token": "...", "role": "...", "user_id": ... }
    """
    content_length = int(request.headers.get('Content-Length', 0))
    body = request.rfile.read(content_length)
    try:
        data = json.loads(body)
    except Exception:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Invalid JSON body."}).encode('utf-8'))
        return
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Username and password required."}).encode('utf-8'))
        return
    success, result = login_user(username, password)
    if success:
        request._set_headers(200)
        request.wfile.write(json.dumps(result).encode('utf-8'))
    else:
        request._set_headers(401)
        request.wfile.write(json.dumps({"error": result}).encode('utf-8'))
