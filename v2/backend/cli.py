import argparse
import sys
import datetime
from database.db import SessionLocal
from models.user import User, UserRole, Gender
from models.school import School
from services.accounts import register_school_admin, create_teacher_account, register_superuser
from services.class_services import create_class
from services.course_services import create_course, get_courses
from services.enrollment_services import enroll_student, get_students

def validate_gender(gender, prompt="Gender"):
    """Validate gender input against Gender enum."""
    valid_genders = [g.value for g in Gender]
    if gender.lower() not in valid_genders:
        print(f"[Error] {prompt} must be one of: {', '.join(valid_genders)}")
        return None
    return gender.lower()

def validate_date(date_str, prompt="Date of Birth", optional=True):
    """Validate date input (YYYY-MM-DD) or return None if optional."""
    if not date_str and optional:
        return None
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        print(f"[Error] {prompt} must be in YYYY-MM-DD format")
        return None

def validate_int(value, prompt, min_val=None):
    """Validate integer input."""
    try:
        val = int(value)
        if min_val is not None and val < min_val:
            print(f"[Error] {prompt} must be at least {min_val}")
            return None
        return val
    except ValueError:
        print(f"[Error] {prompt} must be an integer")
        return None

def validate_float(value, prompt, min_val=None, max_val=None):
    """Validate float input."""
    try:
        val = float(value)
        if min_val is not None and val < min_val:
            print(f"[Error] {prompt} must be at least {min_val}")
            return None
        if max_val is not None and val > max_val:
            print(f"[Error] {prompt} must be at most {max_val}")
            return None
        return val
    except ValueError:
        print(f"[Error] {prompt} must be a number")
        return None

def validate_non_empty(value, prompt):
    """Validate non-empty string input."""
    if not value.strip():
        print(f"[Error] {prompt} cannot be empty")
        return None
    return value.strip()

def validate_grading_system(grading_system):
    """Validate grading system as a Python list of dicts or return None."""
    if not grading_system:
        return None
    try:
        gs = eval(grading_system)
        if not isinstance(gs, list) or not all(isinstance(item, dict) for item in gs):
            print("[Error] Grading system must be a list of dictionaries")
            return None
        return gs
    except:
        print("[Error] Invalid grading system format. Use Python list of dicts (e.g., [{'grade': 'A', 'min': 90, 'max': 100}])")
        return None

def main():
    print("\n=== School Management System CLI ===\n")
    session = SessionLocal()

    def list_schools():
        schools = session.query(School).all()
        return [{"id": s.id, "name": s.name, "grading_system": s.grading_system or "Default"} for s in schools]

    while True:
        print("1. Register as School Admin")
        print("2. Login")
        print("3. Exit")
        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            print("\n--- Register as School Admin ---")
            school_name = validate_non_empty(input("School Name: "), "School Name")
            if not school_name:
                continue
            full_name = validate_non_empty(input("Admin Full Name: "), "Admin Full Name")
            if not full_name:
                continue
            phone = validate_non_empty(input("Phone: "), "Phone")
            if not phone:
                continue
            email = validate_non_empty(input("Email: "), "Email")
            if not email:
                continue
            gender = validate_gender(input(f"Gender ({', '.join([g.value for g in Gender])}): "), "Gender")
            if not gender:
                continue
            grading_system = input("Grading System (Python list of dicts, leave blank for default): ")
            grading_system_val = validate_grading_system(grading_system)
            date_of_birth = validate_date(input("Date of Birth (YYYY-MM-DD, optional): "), "Date of Birth")
            # No superuser required for admin registration
            result = register_school_admin(
                school_name=school_name,
                full_name=full_name,
                phone=phone,
                email=email,
                gender=gender,
                grading_system=grading_system_val,
                date_of_birth=date_of_birth,
                acting_user=None
            )
            if result["status"] == "success":
                print(f"[Success] School and admin created: {result['admin_username']} / {result['admin_email']}" )
            else:
                print(f"[Error] {result['message']}")
        elif choice == "2":
            print("\n--- Login ---")
            username = validate_non_empty(input("Username: "), "Username")
            if not username:
                continue
            password = validate_non_empty(input("Password: "), "Password")
            if not password:
                continue
            user = session.query(User).filter_by(username=username).first()
            if not user:
                print("[Error] User not found")
                continue
            import hashlib
            hashed = hashlib.sha256(password.encode()).hexdigest()
            if user.hashed_password != hashed:
                print("[Error] Incorrect password")
                continue
            print(f"[Success] Logged in as {user.username} ({user.role.value})")
            user_id = user.id

            while True:
                if user.role == UserRole.superuser:
                    print("\n--- Superuser Menu ---")
                    print("1. Register School and Admin")
                    print("2. List Schools")
                    print("3. Logout")
                    role_choice = input("Select an option (1-3): ").strip()
                    if role_choice == "1":
                        school_name = validate_non_empty(input("School Name: "), "School Name")
                        if not school_name:
                            continue
                        full_name = validate_non_empty(input("Admin Full Name: "), "Admin Full Name")
                        if not full_name:
                            continue
                        phone = validate_non_empty(input("Phone: "), "Phone")
                        if not phone:
                            continue
                        email = validate_non_empty(input("Email: "), "Email")
                        if not email:
                            continue
                        gender = validate_gender(input(f"Gender ({', '.join([g.value for g in Gender])}): "), "Gender")
                        if not gender:
                            continue
                        grading_system = input("Grading System (Python list of dicts, leave blank for default): ")
                        grading_system_val = validate_grading_system(grading_system)
                        date_of_birth = validate_date(input("Date of Birth (YYYY-MM-DD, optional): "), "Date of Birth")
                        result = register_school_admin(
                            school_name=school_name,
                            full_name=full_name,
                            phone=phone,
                            email=email,
                            gender=gender,
                            grading_system=grading_system_val,
                            date_of_birth=date_of_birth,
                            acting_user=user
                        )
                        if result["status"] == "success":
                            print(f"[Success] School and admin created: {result['admin_username']} / {result['admin_email']}")
                        else:
                            print(f"[Error] {result['message']}")
                    elif role_choice == "2":
                        schools = list_schools()
                        print("\nSchools:")
                        for s in schools:
                            print(f"- ID: {s['id']}, Name: {s['name']}, Grading: {s['grading_system']}")
                    elif role_choice == "3":
                        print("Logging out...")
                        break
                    else:
                        print("[Error] Invalid option")
                elif user.role == UserRole.admin:
                    print("\n--- Admin Menu ---")
                    print("1. List Schools")
                    print("2. Create Class")
                    print("3. Manage Courses")
                    print("4. Create Teacher")
                    print("5. List Students")
                    print("6. Enroll Student")
                    print("7. View Audit Logs")
                    print("8. Logout")
                    admin_choice = input("Select an option (1-8): ").strip()
                    if admin_choice == "1":
                        schools = list_schools()
                        print("\nSchools:")
                        for s in schools:
                            print(f"- ID: {s['id']}, Name: {s['name']}, Grading: {s['grading_system']}")
                    elif admin_choice == "2":
                        school_id = validate_int(input("School ID: "), "School ID", min_val=1)
                        if not school_id:
                            continue
                        class_name = validate_non_empty(input("Class Name: "), "Class Name")
                        if not class_name:
                            continue
                        academic_year = validate_non_empty(input("Academic Year: "), "Academic Year")
                        if not academic_year:
                            continue
                        description = input("Description (optional): ").strip() or None
                        success, msg, class_result = create_class(class_name, school_id, academic_year, description)
                        if success:
                            print(f"[Success] Class created: ID {class_result['id']}, Name: {class_result['name']}")
                        else:
                            print(f"[Error] {msg}")
                    elif admin_choice == "3":
                        class_id = validate_int(input("Class ID: "), "Class ID", min_val=1)
                        if not class_id:
                            continue
                        print("1. List Courses")
                        print("2. Create Course")
                        course_choice = input("Select (1-2): ").strip()
                        if course_choice == "1":
                            courses = get_courses(class_id=class_id)
                            print("\nCourses:")
                            for c in courses:
                                print(f"- ID: {c['id']}, Title: {c['title']}, Code: {c['code']}, Teacher ID: {c['teacher_id']}")
                        elif course_choice == "2":
                            title = validate_non_empty(input("Course Title: "), "Course Title")
                            if not title:
                                continue
                            code = validate_non_empty(input("Course Code: "), "Course Code")
                            if not code:
                                continue
                            credit_hours = validate_int(input("Credit Hours: "), "Credit Hours", min_val=1)
                            if not credit_hours:
                                continue
                            grading_type = validate_non_empty(input("Grading Type: "), "Grading Type")
                            if not grading_type:
                                continue
                            school_initials = validate_non_empty(input("School Initials: "), "School Initials")
                            if not school_initials:
                                continue
                            teacher_id = input("Teacher ID (optional): ").strip()
                            teacher_id_val = validate_int(teacher_id, "Teacher ID", min_val=1) if teacher_id else None
                            teacher_full_name = input("Teacher Full Name (optional): ").strip() or None
                            teacher_gender = validate_gender(input(f"Teacher Gender ({', '.join([g.value for g in Gender])}, default male): ") or "male", "Teacher Gender")
                            if not teacher_gender:
                                continue
                            teacher_dob = validate_date(input("Teacher DOB (YYYY-MM-DD, optional): "), "Teacher DOB")
                            success, msg, data = create_course(
                                title, code, credit_hours, grading_type, class_id, school_initials,
                                teacher_id=teacher_id_val, teacher_full_name=teacher_full_name,
                                teacher_gender=teacher_gender, teacher_dob=teacher_dob
                            )
                            if success:
                                print(f"[Success] Course created: ID {data['course_id']}, Title: {data['title']}")
                            else:
                                print(f"[Error] {msg}")
                    elif admin_choice == "4":
                        full_name = validate_non_empty(input("Teacher Full Name: "), "Teacher Full Name")
                        if not full_name:
                            continue
                        school_initials = validate_non_empty(input("School Initials: "), "School Initials")
                        if not school_initials:
                            continue
                        gender = validate_gender(input(f"Gender ({', '.join([g.value for g in Gender])}): "), "Gender")
                        if not gender:
                            continue
                        date_of_birth = validate_date(input("Date of Birth (YYYY-MM-DD, optional): "), "Date of Birth")
                        school_id = validate_int(input("School ID: "), "School ID", min_val=1)
                        if not school_id:
                            continue
                        teacher, _ = create_teacher_account(session, full_name, school_initials, gender, date_of_birth, school_id)
                        if teacher:
                            print(f"[Success] Teacher created: ID {teacher.id}, Name: {teacher.full_name}")
                        else:
                            print("[Error] Failed to create teacher")
                    elif admin_choice == "5":
                        class_id = validate_int(input("Class ID: "), "Class ID", min_val=1)
                        if not class_id:
                            continue
                        students = get_students(class_id)
                        print("\nStudents:")
                        for s in students:
                            print(f"- ID: {s['id']}, Name: {s['full_name']}, Email: {s['email']}")
                    elif admin_choice == "6":
                        full_name = validate_non_empty(input("Student Full Name: "), "Student Full Name")
                        if not full_name:
                            continue
                        school_initials = validate_non_empty(input("School Initials: "), "School Initials")
                        if not school_initials:
                            continue
                        class_id = validate_int(input("Class ID: "), "Class ID", min_val=1)
                        if not class_id:
                            continue
                        gender = validate_gender(input(f"Gender ({', '.join([g.value for g in Gender])}): "), "Gender")
                        if not gender:
                            continue
                        date_of_birth = validate_date(input("Date of Birth (YYYY-MM-DD, optional): "), "Date of Birth")
                        ok, msg, student_info = enroll_student(
                            full_name=full_name,
                            school_initials=school_initials,
                            class_id=class_id,
                            gender=gender,
                            date_of_birth=date_of_birth
                        )
                        if ok:
                            print(f"[Success] Student enrolled: ID {student_info['id']}, Name: {student_info['full_name']}")
                        else:
                            print(f"[Error] {msg}")
                    elif admin_choice == "7":
                        from services.audit_log_services import query_audit_logs
                        logs = query_audit_logs()
                        print("\nAudit Logs:")
                        for log in logs:
                            print(f"- {log['timestamp']}: {log['user_id']} {log['action']} - {log['message']}")
                    elif admin_choice == "8":
                        print("Logging out...")
                        break
                    else:
                        print("[Error] Invalid option")
                elif user.role == UserRole.staff:
                    print("\n--- Teacher Menu ---")
                    print("1. Upload Grade")
                    print("2. View My Courses")
                    print("3. View My Students")
                    print("4. Logout")
                    tch_choice = input("Select an option (1-4): ").strip()
                    if tch_choice == "1":
                        from services.grade_services import upload_grade
                        student_id = validate_int(input("Student ID: "), "Student ID", min_val=1)
                        if not student_id:
                            continue
                        course_id = validate_int(input("Course ID: "), "Course ID", min_val=1)
                        if not course_id:
                            continue
                        value = validate_float(input("Grade Value: "), "Grade Value", min_val=0, max_val=100)
                        if not value:
                            continue
                        ok, msg = upload_grade(student_id, course_id, value, user_id)
                        if ok:
                            print("[Success] Grade uploaded")
                        else:
                            print(f"[Error] {msg}")
                    elif tch_choice == "2":
                        courses = get_courses()
                        print("\nMy Courses:")
                        for c in courses:
                            if c["teacher_id"] == user_id:
                                print(f"- ID: {c['id']}, Title: {c['title']}, Code: {c['code']}")
                    elif tch_choice == "3":
                        class_id = validate_int(input("Class ID: "), "Class ID", min_val=1)
                        if not class_id:
                            continue
                        students = get_students(class_id)
                        print("\nMy Students:")
                        for s in students:
                            print(f"- ID: {s['id']}, Name: {s['full_name']}, Email: {s['email']}")
                    elif tch_choice == "4":
                        print("Logging out...")
                        break
                    else:
                        print("[Error] Invalid option")
                elif user.role == UserRole.student:
                    print("\n--- Student Menu ---")
                    print("1. View My Grades")
                    print("2. View My Profile")
                    print("3. Logout")
                    stu_choice = input("Select an option (1-3): ").strip()
                    if stu_choice == "1":
                        from services.grade_services import get_grades
                        course_id = validate_int(input("Course ID: "), "Course ID", min_val=1)
                        if not course_id:
                            continue
                        grade = get_grades(user_id, course_id)
                        if grade:
                            print(f"Grade: {grade['value']} (Graded by: {grade['graded_by']})")
                        else:
                            print("[Info] No grade found")
                    elif stu_choice == "2":
                        print(f"\nProfile:")
                        print(f"User ID: {user_id}")
                        print(f"Role: {user.role.value}")
                        print(f"Username: {user.username}")
                        print(f"Full Name: {user.full_name}")
                        print(f"Email: {user.email}")
                    elif stu_choice == "3":
                        print("Logging out...")
                        break
                    else:
                        print("[Error] Invalid option")
                else:
                    print("[Error] Unknown role. Logging out.")
                    break
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("[Error] Invalid option")
    session.close()

if __name__ == "__main__":
    main()