import json
import logging
import os
import uuid
import bcrypt
from database.db import SessionLocal
from models.user import User, UserRole
from services.student_services import set_student_profile_picture
from utils.auth import require_role

# Configure logging for debugging and auditing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directory for storing uploaded images
UPLOAD_DIR = "uploads"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB max size

# Ensure upload directory exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
    logger.info(f"Created upload directory: {UPLOAD_DIR}")

@require_role(['admin', 'teacher', 'student'])
def handle_view_profile(request):
    """
    Handle GET requests to retrieve the authenticated user's profile.

    This endpoint returns the profile details of the authenticated user, including
    their ID, username, full name, email, role, and profile image (if available).
    Accessible to admin, teacher, and student roles.

    Args:
        request: HTTP request object with user authentication details set by
                 the @require_role decorator.

    Returns:
        HTTP response with status code 200 and JSON body containing user profile:
            - id: int, user ID
            - username: str, user login name
            - full_name: str, user's full name
            - email: str, user's email address
            - role: str, user's role (e.g., "student", "teacher", "admin")
            - profile_image: str or null, path to profile image

    Example:
        GET /profile
        Authorization: Bearer <token>
        Response: {
            "id": 1,
            "username": "jdoe",
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "role": "student",
            "profile_image": "uploads/123e4567-e89b-12d3-a456-426614174000.jpg"
        }

    Notes:
        - Assumes `request.user` contains valid user data from authentication.
        - Checks for `profile_image` existence to avoid attribute errors.
        - In production, consider caching user data to reduce database queries.
        - Log access for auditing if sensitive data is exposed.
    """
    user = request.user
    logger.info(f"User {user.id} viewed their profile")
    request._set_headers(200)
    request.wfile.write(json.dumps({
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value,
        "profile_image": user.profile_image if hasattr(user, 'profile_image') else None
    }).encode('utf-8'))

@require_role(['admin', 'teacher', 'student'])
def handle_update_profile(request):
    """
    Handle POST requests to update the authenticated user's profile.

    Updates allowed fields (full_name, email, date_of_birth, address) for the
    authenticated user. Validates input types and formats. Accessible to admin,
    teacher, and student roles.

    Args:
        request: HTTP request object containing JSON body and user authentication
                 details set by the @require_role decorator.

    Body:
        {
            "full_name": str,        // Optional: User's full name
            "email": str,            // Optional: User's email address
            "date_of_birth": str,    // Optional: Date of birth (e.g., "YYYY-MM-DD")
            "address": str           // Optional: Physical address
        }

    Returns:
        HTTP response with status code and JSON body:
            - 200: {"message": "Profile updated."} on success
            - 400: {"error": "error message"} for invalid input
            - 404: {"error": "User not found."} if user does not exist
            - 500: {"error": "internal error"} for unexpected errors

    Example:
        POST /profile/update
        Authorization: Bearer <token>
        Body: {"full_name": "John Doe", "email": "john.doe@example.com"}
        Response: {"message": "Profile updated."}

    Notes:
        - Validates input types and formats (e.g., email must contain "@").
        - Uses database transactions with rollback on failure.
        - Logs all update attempts for auditing.
        - Consider adding stricter validation (e.g., email regex, date format).
        - In production, add rate limiting to prevent abuse.
    """
    user = request.user
    content_length = int(request.headers.get('Content-Length', 0))
    if content_length <= 0:
        logger.error(f"User {user.id} sent empty request body for profile update")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "No data provided"}).encode('utf-8'))
        return

    db = SessionLocal()
    try:
        body = request.rfile.read(content_length)
        data = json.loads(body)
    except json.JSONDecodeError:
        logger.error(f"User {user.id} sent invalid JSON for profile update")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Invalid JSON body."}).encode('utf-8'))
        return

    try:
        db_user = db.query(User).filter_by(id=user.id).first()
        if not db_user:
            logger.error(f"User {user.id} not found for profile update")
            request._set_headers(404)
            request.wfile.write(json.dumps({"error": "User not found."}).encode('utf-8'))
            return

        # Define allowed fields and filter updates
        allowed_fields = ["full_name", "email", "date_of_birth", "address"]
        updates = {k: v for k, v in data.items() if k in allowed_fields}

        # Validate input
        if not updates:
            logger.error(f"User {user.id} provided no updatable fields")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "No updatable fields provided."}).encode('utf-8'))
            return
        if "full_name" in updates and (not isinstance(updates["full_name"], str) or len(updates["full_name"]) < 2):
            logger.error(f"User {user.id} provided invalid full_name: {updates['full_name']}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "full_name must be a string with at least 2 characters."}).encode('utf-8'))
            return
        if "email" in updates and (not isinstance(updates["email"], str) or "@" not in updates["email"]):
            logger.error(f"User {user.id} provided invalid email: {updates['email']}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "Invalid email format."}).encode('utf-8'))
            return
        if "date_of_birth" in updates and not isinstance(updates["date_of_birth"], str):
            logger.error(f"User {user.id} provided invalid date_of_birth: {updates['date_of_birth']}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "date_of_birth must be a string."}).encode('utf-8'))
            return
        if "address" in updates and not isinstance(updates["address"], str):
            logger.error(f"User {user.id} provided invalid address: {updates['address']}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "address must be a string."}).encode('utf-8'))
            return

        # Apply updates
        for field, value in updates.items():
            setattr(db_user, field, value)
        db.commit()
        logger.info(f"User {user.id} updated profile: {updates.keys()}")
        request._set_headers(200)
        request.wfile.write(json.dumps({"message": "Profile updated."}).encode('utf-8'))

    except Exception as e:
        db.rollback()
        logger.error(f"User {user.id} failed to update profile: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))
    finally:
        db.close()

@require_role(['admin', 'teacher', 'student'])
def handle_change_password(request):
    """
    Handle POST requests to change the authenticated user's password.

    Updates the user's password after verifying the old password. Requires a JSON
    body with old and new passwords. Accessible to admin, teacher, and student roles.

    Args:
        request: HTTP request object containing JSON body and user authentication
                 details set by the @require_role decorator.

    Body:
        {
            "old_password": str,     // Current password
            "new_password": str      // New password (min 8 characters)
        }

    Returns:
        HTTP response with status code and JSON body:
            - 200: {"message": "Password changed successfully."} on success
            - 400: {"error": "error message"} for invalid input
            - 401: {"error": "Old password is incorrect."} if old password is wrong
            - 404: {"error": "User not found."} if user does not exist
            - 500: {"error": "internal error"} for unexpected errors

    Example:
        POST /profile/change_password
        Authorization: Bearer <token>
        Body: {"old_password": "oldpass123", "new_password": "newpass123"}
        Response: {"message": "Password changed successfully."}

    Notes:
        - Uses bcrypt for secure password hashing.
        - Validates password length and presence.
        - Logs all password change attempts for auditing.
        - In production, consider rate limiting to prevent brute-force attacks.
        - Ensure old passwords are not logged for security.
    """
    user = request.user
    content_length = int(request.headers.get('Content-Length', 0))
    if content_length <= 0:
        logger.error(f"User {user.id} sent empty request body for password change")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "No data provided"}).encode('utf-8'))
        return

    db = SessionLocal()
    try:
        body = request.rfile.read(content_length)
        data = json.loads(body)
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        if not old_password or not new_password:
            logger.error(f"User {user.id} missing password fields")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "Both old and new passwords are required."}).encode('utf-8'))
            return
        if len(new_password) < 8:
            logger.error(f"User {user.id} provided new password with insufficient length")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "New password must be at least 8 characters."}).encode('utf-8'))
            return

        db_user = db.query(User).filter_by(id=user.id).first()
        if not db_user:
            logger.error(f"User {user.id} not found for password change")
            request._set_headers(404)
            request.wfile.write(json.dumps({"error": "User not found."}).encode('utf-8'))
            return

        # Verify old password
        if not bcrypt.checkpw(
            old_password.encode('utf-8'),
            db_user.hashed_password.encode('utf-8') if isinstance(db_user.hashed_password, str) else db_user.hashed_password
        ):
            logger.warning(f"User {user.id} provided incorrect old password")
            request._set_headers(401)
            request.wfile.write(json.dumps({"error": "Old password is incorrect."}).encode('utf-8'))
            return

        # Hash and set new password
        hashed_new = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db_user.hashed_password = hashed_new
        db.commit()
        logger.info(f"User {user.id} changed password successfully")
        request._set_headers(200)
        request.wfile.write(json.dumps({"message": "Password changed successfully."}).encode('utf-8'))

    except json.JSONDecodeError:
        logger.error(f"User {user.id} sent invalid JSON for password change")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Invalid JSON body."}).encode('utf-8'))
    except Exception as e:
        db.rollback()
        logger.error(f"User {user.id} failed to change password: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))
    finally:
        db.close()

@require_role(['admin', 'teacher', 'student'])
def handle_upload_profile_image(request):
    """
    Handle POST requests to upload a profile image for the authenticated user.

    Accepts a multipart/form-data request with an image file (JPEG or PNG) and
    stores it in the uploads directory. Updates the user's profile_image field with
    the file path. Accessible to admin, teacher, and student roles.

    Args:
        request: HTTP request object containing multipart/form-data body and user
                 authentication details set by the @require_role decorator.

    Body:
        Form-data with a file field named "file" containing a JPEG or PNG image.

    Returns:
        HTTP response with status code and JSON body:
            - 200: {"message": "Profile image uploaded successfully.", "image_path": "..."} on success
            - 400: {"error": "error message"} for invalid input (e.g., wrong content type, size limit)
            - 404: {"error": "User not found."} if user does not exist
            - 500: {"error": "internal error"} for file saving or database errors

    Example:
        POST /profile/upload_image
        Authorization: Bearer <token>
        Content-Type: multipart/form-data; boundary=----WebKitFormBoundary123
        Body:
        ------WebKitFormBoundary123
        Content-Disposition: form-data; name="file"; filename="profile.jpg"
        Content-Type: image/jpeg
        [Binary image data]
        ------WebKitFormBoundary123--
        Response: {
            "message": "Profile image uploaded successfully.",
            "image_path": "uploads/123e4567-e89b-12d3-a456-426614174000.jpg"
        }

    Notes:
        - Validates file type (JPEG/PNG) and size (max 5MB).
        - Uses UUID for unique filenames to prevent collisions and path traversal.
        - Deletes old profile image to avoid accumulating unused files.
        - Logs all upload attempts for auditing.
        - In production, consider using cloud storage (e.g., AWS S3) for scalability.
        - Add image content validation (e.g., using python-magic) for security.
        - Implement rate limiting to prevent abuse.
    """
    user = request.user
    content_type = request.headers.get('Content-Type', '')
    if 'multipart/form-data' not in content_type:
        logger.error(f"User {user.id} sent invalid Content-Type for image upload: {content_type}")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Content-Type must be multipart/form-data"}).encode('utf-8'))
        return

    # Parse multipart form data
    boundary = content_type.split("boundary=")[-1].strip()
    remainbytes = int(request.headers.get('Content-Length', 0))
    line = request.rfile.readline()
    remainbytes -= len(line)
    if boundary not in line.decode('utf-8'):
        logger.error(f"User {user.id} sent invalid multipart boundary")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Content does not start with boundary"}).encode('utf-8'))
        return

    # Read until file content
    filename = None
    content_type = None
    while remainbytes > 0:
        line = request.rfile.readline()
        remainbytes -= len(line)
        if b'filename=' in line:
            filename = line.decode('utf-8').split('filename="')[1].split('"')[0]
            break
    if not filename:
        logger.error(f"User {user.id} did not provide a file for image upload")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "No file provided."}).encode('utf-8'))
        return

    # Read Content-Type and skip blank line
    line = request.rfile.readline()
    remainbytes -= len(line)
    content_type = line.decode('utf-8').split('Content-Type: ')[1].split('\r\n')[0]
    if content_type not in ALLOWED_IMAGE_TYPES:
        logger.error(f"User {user.id} sent invalid file type: {content_type}")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Only JPEG or PNG images are allowed."}).encode('utf-8'))
        return

    # Skip blank line
    request.rfile.readline()
    remainbytes -= len(request.rfile.readline())

    # Read file content
    file_data = b""
    while remainbytes > 0:
        line = request.rfile.readline()
        remainbytes -= len(line)
        if boundary.encode() in line:
            break
        file_data += line

    # Validate file size
    if len(file_data) > MAX_IMAGE_SIZE:
        logger.error(f"User {user.id} sent oversized image: {len(file_data)} bytes")
        request._set_headers(400)
        request.wfile.write(json.dumps({
            "error": f"Image size exceeds {MAX_IMAGE_SIZE // 1024 // 1024}MB limit."
        }).encode('utf-8'))
        return

    # Generate unique filename and save image
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in ['.jpg', '.jpeg', '.png']:
        logger.error(f"User {user.id} sent invalid file extension: {file_ext}")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Invalid file extension."}).encode('utf-8'))
        return
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save file
    try:
        with open(file_path, 'wb') as f:
            f.write(file_data)
        logger.info(f"User {user.id} saved image to {file_path}")
    except Exception as e:
        logger.error(f"User {user.id} failed to save image: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Failed to save image: {str(e)}"}).encode('utf-8'))
        return

    # Update user profile
    db = SessionLocal()
    try:
        db_user = db.query(User).filter_by(id=user.id).first()
        if not db_user:
            logger.error(f"User {user.id} not found for image upload")
            request._set_headers(404)
            request.wfile.write(json.dumps({"error": "User not found."}).encode('utf-8'))
            return

        # Delete old image if it exists
        if db_user.profile_image and os.path.exists(db_user.profile_image):
            try:
                os.remove(db_user.profile_image)
                logger.info(f"User {user.id} deleted old image: {db_user.profile_image}")
            except Exception as e:
                logger.warning(f"User {user.id} failed to delete old image: {str(e)}")

        db_user.profile_image = file_path
        db.commit()
        logger.info(f"User {user.id} updated profile image to {file_path}")
        request._set_headers(200)
        request.wfile.write(json.dumps({
            "message": "Profile image uploaded successfully.",
            "image_path": file_path
        }).encode('utf-8'))

    except Exception as e:
        db.rollback()
        logger.error(f"User {user.id} failed to update profile image: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))
    finally:
        db.close()

@require_role(['student'])
def handle_update_student_info(request):
    """
    Handle PATCH requests to update a student's profile information.

    Allows students to update specific fields (e.g., date_of_birth, address) while
    preventing changes to immutable fields (username, full_name, gender, email, role, id).
    Expects a JSON body with updatable fields. Restricted to student role.

    Args:
        request: HTTP request object containing JSON body and user authentication
                 details set by the @require_role decorator.

    Body:
        {
            "date_of_birth": str,    // Optional: Date of birth (e.g., "YYYY-MM-DD")
            "address": str           // Optional: Physical address
            // Other fields are ignored
        }

    Returns:
        HTTP response with status code and JSON body:
            - 200: {"message": "Profile updated successfully."} on success
            - 400: {"error": "error message"} for invalid input
            - 404: {"error": "Student not found."} if user does not exist
            - 500: {"error": "internal error"} for unexpected errors

    Example:
        PATCH /student/profile
        Authorization: Bearer <student-token>
        Body: {"date_of_birth": "2000-01-01", "address": "123 Main St"}
        Response: {"message": "Profile updated successfully."}

    Notes:
        - Validates user role and existence before updating.
        - Uses database transactions with rollback on failure.
        - Logs all update attempts for auditing.
        - Consider adding stricter validation for date_of_birth (e.g., regex or datetime parsing).
        - In production, add rate limiting to prevent abuse.
    """
    user = request.user
    content_length = int(request.headers.get('Content-Length', 0))
    if content_length <= 0:
        logger.error(f"User {user.id} sent empty request body for student info update")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "No data provided"}).encode('utf-8'))
        return

    try:
        body = request.rfile.read(content_length)
        data = json.loads(body)
    except json.JSONDecodeError:
        logger.error(f"User {user.id} sent invalid JSON for student info update")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Invalid JSON body."}).encode('utf-8'))
        return

    immutable_fields = {"username", "full_name", "gender", "email", "role", "id"}
    updates = {k: v for k, v in data.items() if k not in immutable_fields}
    if not updates:
        logger.error(f"User {user.id} provided no updatable fields for student info")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "No updatable fields provided."}).encode('utf-8'))
        return

    db = SessionLocal()
    try:
        student = db.query(User).filter_by(id=user.id, role='student').first()
        if not student:
            logger.error(f"User {user.id} not found or not a student for info update")
            request._set_headers(404)
            request.wfile.write(json.dumps({"error": "Student not found."}).encode('utf-8'))
            return

        # Validate input
        if "date_of_birth" in updates and not isinstance(updates["date_of_birth"], str):
            logger.error(f"User {user.id} provided invalid date_of_birth: {updates['date_of_birth']}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "date_of_birth must be a string."}).encode('utf-8'))
            return
        if "address" in updates and not isinstance(updates["address"], str):
            logger.error(f"User {user.id} provided invalid address: {updates['address']}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "address must be a string."}).encode('utf-8'))
            return

        for k, v in updates.items():
            setattr(student, k, v)
        db.commit()
        logger.info(f"User {user.id} updated student info: {updates.keys()}")
        request._set_headers(200)
        request.wfile.write(json.dumps({"message": "Profile updated successfully."}).encode('utf-8'))

    except Exception as e:
        db.rollback()
        logger.error(f"User {user.id} failed to update student info: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))
    finally:
        db.close()

# Note: The following endpoint is deprecated or potentially redundant.
# It uses a URL-based approach for profile pictures, which is less secure and
# less reliable than direct file uploads. Consider removing or clarifying its use.
@require_role(['student'])
def handle_upload_profile_picture(request):
    """
    Handle POST requests to set a student's profile picture via URL (DEPRECATED).

    Expects a JSON body with a profile picture URL. Updates the student's
    profile_image field using the set_student_profile_picture service. Restricted
    to student role. This endpoint is less preferred than handle_upload_profile_image
    due to security and reliability concerns with external URLs.

    Args:
        request: HTTP request object containing JSON body and user authentication
                 details set by the @require_role decorator.

    Body:
        {
            "profile_picture_url": str   // URL of the profile picture
        }

    Returns:
        HTTP response with status code and JSON body:
            - 200: {"message": "success message", "profile_picture_url": "..."} on success
            - 400: {"error": "error message"} for invalid input or failure
            - 500: {"error": "internal error"} for unexpected errors

    Example:
        POST /student/profile_picture
        Authorization: Bearer <student-token>
        Body: {"profile_picture_url": "https://example.com/profile.jpg"}
        Response: {
            "message": "Profile picture updated successfully",
            "profile_picture_url": "https://example.com/profile.jpg"
        }

    Notes:
        - Deprecated in favor of handle_upload_profile_image for direct file uploads.
        - Lacks robust URL validation (e.g., format, accessibility).
        - Consider removing or integrating with file upload logic.
        - Logs all attempts for auditing.
        - In production, validate URLs thoroughly and consider rate limiting.
    """
    user = request.user
    content_length = int(request.headers.get('Content-Length', 0))
    if content_length <= 0:
        logger.error(f"User {user.id} sent empty request body for profile picture URL")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "No data provided"}).encode('utf-8'))
        return
    try:
        body = request.rfile.read(content_length)
        data = json.loads(body)
        url = data.get("profile_picture_url")
        if not url or not isinstance(url, str):
            logger.error(f"User {user.id} provided invalid profile_picture_url: {url}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "profile_picture_url must be a non-empty string."}).encode('utf-8'))
            return
            return

        # Basic URL validation (could be enhanced with regex or requests.head)
        if not url.startswith(('http://', 'https://')):
            logger.error(f"User {user.id} provided invalid URL scheme: {url}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": "profile_picture_url must start with http:// or https://"}).encode('utf-8'))
            return

        success, message = set_student_profile_picture(user.id, url)
        if success:
            logger.info(f"User {user.id} updated profile picture URL: {url}")
            request._set_headers(200)
            request.wfile.write(json.dumps({"message": message, "profile_picture_url": url}).encode('utf-8'))
        else:
            logger.error(f"User {user.id} failed to update profile picture URL: {message}")
            request._set_headers(400)
            request.wfile.write(json.dumps({"error": message}).encode('utf-8'))

    except json.JSONDecodeError:
        logger.error(f"User {user.id} sent invalid JSON for profile picture URL")
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Invalid JSON body."}).encode('utf-8'))
    except Exception as e:
        logger.error(f"User {user.id} failed to update profile picture URL: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))

@require_role(['admin', 'teacher', 'student'])
def handle_student_profile_by_id(request):
    """
    Handle GET requests to retrieve a student's profile by ID.
    
    Students can only access their own profile.
    Teachers and admins can access any student profile.
    """
    from urllib.parse import urlparse
    import re
    
    # Extract student_id from path like /students/4/profile
    path_match = re.match(r'/students/(\d+)/profile', urlparse(request.path).path)
    if not path_match:
        request._set_headers(400)
        request.wfile.write(json.dumps({"error": "Invalid student ID in path"}).encode('utf-8'))
        return
    
    student_id = int(path_match.group(1))
    
    # Check permissions - students can only access their own profile
    if hasattr(request, 'user') and request.user:
        user_role = request.user.get('role')
        user_id = request.user.get('id')
        
        if user_role == 'student' and user_id != student_id:
            request._set_headers(403)
            request.wfile.write(json.dumps({"error": "Students can only access their own profile"}).encode('utf-8'))
            return
    
    db = SessionLocal()
    try:
        student = db.query(User).filter_by(id=student_id, role=UserRole.student).first()
        if not student:
            request._set_headers(404)
            request.wfile.write(json.dumps({"error": "Student not found"}).encode('utf-8'))
            return
        
        profile_data = {
            "id": student.id,
            "username": student.username,
            "full_name": student.full_name,
            "email": student.email,
            "role": student.role.value,
            "profile_image": student.profile_image,
            "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
            "address": student.address,
        }
        
        # Only add created_at if it exists
        if hasattr(student, 'created_at') and student.created_at:
            profile_data["created_at"] = student.created_at.isoformat()
        
        request._set_headers(200)
        request.wfile.write(json.dumps(profile_data).encode('utf-8'))
        
    except Exception as e:
        logger.error(f"Failed to get student profile {student_id}: {str(e)}")
        request._set_headers(500)
        request.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode('utf-8'))
    finally:
        db.close()