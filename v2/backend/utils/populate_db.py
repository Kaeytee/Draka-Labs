from subprocess import call
import os
import sys
import json
import datetime
from sqlalchemy.exc import SQLAlchemyError

# Adjust the path to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from database.db import SessionLocal
from services.accounts import register_school_admin, create_teacher_account
from services.class_services import create_class
from services.course_services import Course
from services.enrollment_services import enroll_student
from models.school import School
from models.user import UserRole, Gender

# Initialize output dictionary for credentials
output = {"schools": []}

def random_name(role, idx):
    """Generate unique names for users based on role."""
    if role == "admin":
        return f"Admin{idx} User"
    if role == "teacher":
        return f"Teacher{idx} User"
    if role == "student":
        return f"Student{idx} User"
    return f"User{idx}"


def main():
    # Always reset the database before populating
    print("Resetting database...")
    call([sys.executable, os.path.join(os.path.dirname(__file__), '..', 'utils', 'reset_db.py')])
    # Create a new database session
    session = SessionLocal()
    try:
        # Create 2 schools
        for s in range(1, 3):
            school_name = f"Demo School {s}"
            admin_name = random_name("admin", s)
            admin_email = f"admin{s}@school.com"
            admin_phone = f"02000000{s}"
            admin_gender = Gender.male.value if s % 2 == 1 else Gender.female.value
            grading_system = [
                {"grade": "A", "min": 80, "max": 100},
                {"grade": "B", "min": 70, "max": 79},
                {"grade": "C", "min": 60, "max": 69},
                {"grade": "F", "min": 0, "max": 59}
            ]
            admin_dob = datetime.date(1980 + s, 1, 1)

            # 1. Create admin user first (without school)
            from services.accounts import generate_initials, generate_username, generate_unique_username_email, generate_password
            initials = generate_initials(school_name)
            base_username = generate_username(admin_name)
            username, email = generate_unique_username_email(session, base_username, initials, "admin")
            password = generate_password(initials, f"{s}0001")
            from models.user import User, UserRole
            import hashlib
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            admin_user = User(
                username=username,
                full_name=admin_name,
                hashed_password=hashed_password,
                email=admin_email,
                role=UserRole.admin,
                gender=Gender.male if s % 2 == 1 else Gender.female,
                date_of_birth=admin_dob,
                phone=admin_phone
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)

            # 2. Create school with admin_id
            from models.school import School
            school = School(
                name=school_name,
                initials=initials,
                grading_system=json.dumps(grading_system),
                phone=admin_phone,
                email=admin_email,
                admin_id=admin_user.id
            )
            session.add(school)
            session.commit()
            session.refresh(school)

            # 3. Update admin user with school_id
            admin_user.school_id = school.id
            session.commit()

            school_data = {
                "name": school_name,
                "initials": school.initials,
                "admin": {
                    "username": admin_user.username,
                    "email": admin_user.email,
                    "password": password
                },
                "classes": []
            }

            # Create 4 classes per school
            for c in range(1, 5):
                class_name = f"Class {c} - {school.initials}"
                academic_year = "2025"  # Use string to match class_services validation
                success, msg, class_result = create_class(class_name, school.id, academic_year)
                if not success:
                    print(f"Failed to create class {class_name}: {msg}")
                    continue
                class_id = class_result["id"]
                class_data = {"name": class_name, "id": class_id, "courses": [], "teachers": [], "students": []}

                # Create 2 teachers per class and store their objects
                teachers_in_class = []
                for t in range(1, 3):
                    teacher_name = random_name("teacher", f"{s}{c}{t}")
                    teacher_dob = datetime.date(1975 + t, 6, 15)
                    teacher_gender = "male" if t % 2 == 1 else "female"
                    try:
                        result = create_teacher_account(
                            session,
                            teacher_name,
                            school.initials,
                            school_id=school.id,
                            gender=teacher_gender,
                            date_of_birth=teacher_dob
                        )
                        if result is None:
                            print(f"[ERROR] Failed to create teacher {teacher_name}: returned None. See previous error output for details.")
                            continue
                        teacher, teacher_password = result
                        if teacher is None or teacher_password is None:
                            print(f"[ERROR] Teacher or password is None for {teacher_name}. This should not happen.")
                            continue
                        teacher.role = UserRole.staff
                        teacher.class_id = class_id  # Assign teacher to class
                        session.commit()
                        teachers_in_class.append(teacher)
                        class_data["teachers"].append({
                            "username": teacher.username,
                            "email": teacher.email,
                            "password": teacher_password
                        })
                    except SQLAlchemyError as e:
                        print(f"Failed to create teacher {teacher_name}: {str(e)}")
                        session.rollback()
                        continue

                # Create 2 courses per class, assign a teacher to each
                for co in range(1, 3):
                    course_title = f"Course {co} - {class_name}"
                    course_code = f"C{c}{co}{s}"
                    try:
                        # Assign teachers in round-robin fashion
                        assigned_teacher = teachers_in_class[(co - 1) % len(teachers_in_class)] if teachers_in_class else None
                        if assigned_teacher is None:
                            print(f"[ERROR] No teacher available to assign to course {course_title}.")
                            continue
                        course = Course(
                            title=course_title,
                            code=course_code,
                            credit_hours=3,
                            grading_type="default",
                            class_id=class_id,
                            teacher_id=assigned_teacher.id
                        )
                        session.add(course)
                        session.commit()
                        class_data["courses"].append({
                            "title": course.title,
                            "code": course.code,
                            "id": course.id
                        })
                    except SQLAlchemyError as e:
                        print(f"Failed to create course {course_title}: {str(e)}")
                        session.rollback()
                        continue

                # Enroll 3 students per class
                for st in range(1, 4):
                    student_name = random_name("student", f"{s}{c}{st}")
                    student_dob = datetime.date(2010 + st, 9, 1)
                    student_gender = "male" if st % 2 == 1 else "female"
                    try:
                        ok, msg, student_info = enroll_student(
                            full_name=student_name,
                            school_initials=school.initials,
                            class_id=class_id,
                            gender=student_gender,
                            date_of_birth=student_dob
                        )
                        if not ok or student_info is None:
                            print(f"Failed to enroll student {student_name}: {msg}")
                            continue
                        class_data["students"].append({
                            "username": student_info["student_username"],
                            "email": student_info["student_email"],
                            "password": student_info["student_password"]
                        })
                    except SQLAlchemyError as e:
                        print(f"Failed to enroll student {student_name}: {str(e)}")
                        session.rollback()
                        continue

                school_data["classes"].append(class_data)
            output["schools"].append(school_data)

        # Write credentials to populated_data.md
        output_path = os.path.join(os.path.dirname(__file__), "..", "populated_data.md")
        with open(output_path, "w") as f:
            f.write("# Populated Demo Data\n\n")
            for school in output["schools"]:
                f.write(f"## {school['name']} ({school['initials']})\n")
                f.write(f"- **Admin:** {school['admin']['username']} / {school['admin']['email']} / {school['admin']['password']}\n")
                for cls in school["classes"]:
                    f.write(f"  - **Class:** {cls['name']} (ID: {cls['id']})\n")
                    for t in cls["teachers"]:
                        f.write(f"    - Teacher: {t['username']} / {t['email']} / {t['password']}\n")
                    for c in cls["courses"]:
                        f.write(f"    - Course: {c['title']} (Code: {c['code']}, ID: {c['id']})\n")
                    for s in cls["students"]:
                        f.write(f"    - Student: {s['username']} / {s['email']} / {s['password']}\n")
                f.write("\n")
        print(f"Database populated and credentials written to {output_path}")

    except SQLAlchemyError as e:
        print(f"Database error: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()