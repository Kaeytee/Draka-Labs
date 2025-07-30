from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from database.db import engine, Base
from models.user import User
from handlers.class_handlers import handle_create_class

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

# Custom HTTP request handler for SIAMS
class SIAMSHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/":
            self._set_headers()
            self.wfile.write(json.dumps({"message": "Backend is running successfully"}).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

    def do_POST(self):
        """Handle POST requests."""
        if self.path == "/create_class":
            handle_create_class(self)
			elif self.path == "create_course":
				handle_create_course(self)
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=SIAMSHandler, port=8000):
    """Start the HTTP server."""
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    init_db()
    run()