# Simple CORS middleware for Python's BaseHTTPRequestHandler

def add_cors_headers(handler):
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-CSRF-Token')
    handler.send_header('Access-Control-Allow-Credentials', 'true')


def handle_cors_preflight(handler):
    handler.send_response(204)
    add_cors_headers(handler)
    handler.end_headers()
