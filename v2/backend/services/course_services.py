import logging
import uuid
from sqlalchemy.exc import DatabaseError
from database.db import SessionLocal
from models.course import Course
from models.classes import Class
from models.user import User

# Configure logging for course service operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Stub for audit logging (replace with actual implementation if available)
def log_audit(user_id, action, message):
    """
    Stub for logging audit events.

    Args:
        user_id (int or None): ID of the user performing the action.
        action (str): Type of action (e.g., "create_course").
        message (str): Details of the action or error.
    """
    logger.info(f"Audit [user_id={user_id}]: {action} - {message}")

# Stub for teacher account creation (replace with actual implementation if available)
def create_teacher_account(db, full_name, school_initials, school_id):
    """
    Stub for creating a teacher account.

    Args:
        db: SQLAlchemy session.
        full_name (str): Full name of the teacher.
        school_initials (str): School identifier for email generation.
        school_id (int): ID of the school.

    Returns:
        tuple: (teacher: User, password: str)
    """
    try:
        email = f"{full_name.lower().replace(' ', '.')}.{school_initials}@school.com"
        password = str(uuid.uuid4())[:8]  # Generate random password
        teacher = User(
            full_name=full_name,
            email=email,
            role="teacher",
            school_id=school_id
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        logger.info(f"Created teacher account: {email}")
        return teacher, password
    except DatabaseError as e:
        db.rollback()
        logger.error(f"Failed to create teacher: {str(e)}")
        raise

def get_courses(class_id=None, school_id=None):
    """
    Retrieve all courses for a given class or school.

    Queries the database for courses filtered by class_id or school_id.
    Returns a list of course dictionaries, including optional student details with
    profile images via the class relationship.

    Args:
        class_id (int, optional): ID of the class to filter courses.
        school_id (int, optional): ID of the school to filter courses (requires join).

    Returns:
        list: List of dictionaries containing course details.

    Example:
        >>> get_courses(class_id=1)
        [
            {
                "id": 201,
                "title": "Algebra",
                "code": "MATH101",
                "credit_hours": 3,
                "grading_type": "default",
                "class_id": 1,
                "teacher_id": 10,
                "students": [
                    {"id": 1, "full_name": "John Doe", "profile_image": "uploads/123e4567-e89b-12d3-a456-426614174000.jpg"},
                    ...
                ]
            },
            ...
        ]

    Notes:
        - If both class_id and school_id are None, returns all courses (not recommended for production).
        - Validates input types and school/class existence.
        - Logs query attempts and errors for auditing.
        - In production, add pagination (e.g., ?page=1&limit=20).
        - Includes student profile images via class relationship.
    """
    if class_id is not None and not isinstance(class_id, int):
        logger.error(f"Invalid class_id: {class_id}")
        return []
    if school_id is not None and not isinstance(school_id, int):
        logger.error(f"Invalid school_id: {school_id}")
        return []

    db = SessionLocal()
    try:
        query = db.query(Course)
        if class_id is not None:
            # Verify class exists
            if not db.query(Class).filter_by(id=class_id).first():
                logger.error(f"Class not found: ID {class_id}")
                return []
            query = query.filter(Course.class_id == class_id)
        elif school_id is not None:
            # Verify school exists
            if not db.query(Class).filter_by(school_id=school_id).first():
                logger.error(f"No classes found for school_id: {school_id}")
                return []
            query = query.join(Class).filter(Class.school_id == school_id)

        courses = query.all()
        result = []
        for course in courses:
            course_data = {
                "id": course.id,
                "title": course.title,
                "code": course.code,
                "credit_hours": course.credit_hours,
                "grading_type": course.grading_type,
                "class_id": course.class_id,
                "teacher_id": course.teacher_id
            }
            # Include students via class relationship
            if course.class_:
                course_data["students"] = [
                    {
                        "id": student.id,
                        "full_name": student.full_name,
                        "profile_image": getattr(student, "profile_image", None)
                    } for student in course.class_.students
                ]
            result.append(course_data)
        logger.info(f"Retrieved {len(result)} courses for class_id={class_id} school_id={school_id}")
        return result

    except DatabaseError as e:
        logger.error(f"Database error retrieving courses for class_id={class_id} school_id={school_id}: {str(e)}")
        return []
    finally:
        db.close()

def create_course(title, code, credit_hours, grading_type, class_id, school_initials, teacher_id=None, teacher_full_name=None):
    """
    Create a new course and assign a teacher (existing or auto-generated).

    Creates a course with the specified details and assigns an existing teacher or
    creates a new one if none provided. Returns course details without sensitive data.

    Args:
        title (str): Course title (e.g., "Algebra").
        code (str): Course code (e.g., "MATH101").
        credit_hours (int): Number of credit hours (positive integer).
        grading_type (str): Type of grading system (e.g., "default").
        class_id (int): ID of the class.
        school_initials (str): School identifier for teacher email generation.
        teacher_id (int, optional): ID of the teacher.
        teacher_full_name (str, optional): Full name for auto-generated teacher.

    Returns:
        tuple: (success: bool, message: str, data: dict or None)
               data contains course details (id, title, code, credit_hours, grading_type, class_id, teacher_id).

    Example:
        >>> create_course("Algebra", "MATH101", 3, "default", 1, "SCH", teacher_id=10)
        (True, "Course created successfully", {
            "course_id": 201,
            "title": "Algebra",
            "code": "MATH101",
            "credit_hours": 3,
            "grading_type": "default",
            "class_id": 1,
            "teacher_id": 10
        })

    Notes:
        - Validates inputs and checks class/teacher existence.
        - Ensures unique course code per class.
        - Logs creation attempts and errors for auditing.
        - Does not return teacher_password for security.
        - In production, consider rate limiting and stricter validation.
        - Student profile images can be included via get_courses.
    """
    # Validate inputs
    if not isinstance(title, str) or not title.strip():
        logger.error("Invalid course title provided")
        return False, "Title must be a non-empty string", None
    if not isinstance(code, str) or not code.strip():
        logger.error("Invalid course code provided")
        return False, "Code must be a non-empty string", None
    if not isinstance(credit_hours, int) or credit_hours <= 0:
        logger.error(f"Invalid credit_hours: {credit_hours}")
        return False, "Credit hours must be a positive integer", None
    if not isinstance(grading_type, str) or not grading_type.strip():
        logger.error(f"Invalid grading_type: {grading_type}")
        return False, "Grading type must be a non-empty string", None
    if not isinstance(class_id, int):
        logger.error(f"Invalid class_id: {class_id}")
        return False, "Class ID must be an integer", None
    if not isinstance(school_initials, str) or not school_initials.strip():
        logger.error(f"Invalid school_initials: {school_initials}")
        return False, "School initials must be a non-empty string", None
    if teacher_id is not None and not isinstance(teacher_id, int):
        logger.error(f"Invalid teacher_id: {teacher_id}")
        return False, "Teacher ID must be an integer", None
    if teacher_full_name is not None and (not isinstance(teacher_full_name, str) or not teacher_full_name.strip()):
        logger.error(f"Invalid teacher_full_name: {teacher_full_name}")
        return False, "Teacher full name must be a non-empty string", None

    db = SessionLocal()
    try:
        # Validate class existence
        class_obj = db.query(Class).filter_by(id=class_id).first()
        if not class_obj:
            log_audit(None, "create_course_error", f"Class not found for id {class_id}")
            return False, "Class not found", None

        # Check for unique course code within class
        if db.query(Course).filter_by(class_id=class_id, code=code).first():
            log_audit(None, "create_course_error", f"Course code {code} already exists for class {class_id}")
            return False, "Course code already exists for this class", None

        # Assign existing teacher or auto-generate
        teacher = None
        password = None
        if teacher_id:
            teacher = db.query(User).filter_by(
                id=teacher_id,
                school_id=class_obj.school_id,
                role="teacher"
            ).first()
            if not teacher:
                log_audit(None, "create_course_error", f"Teacher not found or not in this school: {teacher_id}")
                return False, "Teacher not found or not in this school", None
        else:
            # Auto-generate teacher if no teacher_id provided
            if not teacher_full_name:
                teacher_full_name = f"Teacher for {title}"
            teacher, password = create_teacher_account(db, teacher_full_name, school_initials, class_obj.school_id)

        # Create course
        course = Course(
            title=title.strip(),
            code=code.strip(),
            credit_hours=credit_hours,
            grading_type=grading_type.strip(),
            class_id=class_id,
            teacher_id=teacher.id
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        log_audit(None, "create_course", f"Course {title} created for class {class_id} with teacher {teacher.id}")
        return True, "Course created successfully", {
            "course_id": course.id,
            "title": course.title,
            "code": course.code,
            "credit_hours": course.credit_hours,
            "grading_type": course.grading_type,
            "class_id": course.class_id,
            "teacher_id": course.teacher_id
        }

    except DatabaseError as e:
        db.rollback()
        log_audit(None, "create_course_error", f"Database error creating course: {str(e)}")
        return False, f"Database error: {str(e)}", None
    finally:
        db.close()