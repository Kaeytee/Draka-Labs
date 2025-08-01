import sys
import datetime
from database.db import SessionLocal
from models.user import User, UserRole, Gender
from models.school import School
from services.accounts import register_school_admin, create_teacher_account, register_superuser
from services.class_services import create_class
from services.course_services import create_course, get_courses
from services.enrollment_services import enroll_student, get_students
from models.classes import Class

def validate_gender(prompt="Gender"):
    """Validate gender input against Gender enum with retries."""
    valid_genders = {g.value.lower(): g.value for g in Gender}  # Map lowercase to enum value
    short_forms = {'m': 'male', 'f': 'female', 'o': 'other'}  # Allow short forms
    while True:
        gender = input(f"{prompt} ({', '.join(valid_genders.values())}): ").strip().lower()
        # Check exact match or short form
        if gender in valid_genders:
            return valid_genders[gender]
        if gender in short_forms:
            return short_forms[gender]
        print(f"[Error] {prompt} must be one of: {', '.join(valid_genders.values())} (or m, f, o)")
        retry = input("Try again? (y/n): ").strip().lower()
        if retry != 'y':
            return None

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
        for item in gs:
            if not all(key in item for key in ['grade', 'min', 'max']):
                print("[Error] Each grade must have 'grade', 'min', and 'max' keys")
                return None
        return gs
    except:
        print("[Error] Invalid grading system format. Use Python list of dicts (e.g., [{'grade': 'A', 'min': 90, 'max': 100}])")
        return None

def validate_initials(initials, prompt="School Initials"):
    """Validate school initials (2-5 uppercase letters)."""
    initials = initials.strip().upper()
    if not (2 <= len(initials) <= 5 and initials.isalpha()):
        print(f"[Error] {prompt} must be 2-5 uppercase letters")
        return None
    return initials

def main():
    print("\n=== School Management System CLI ===\n")
    session = SessionLocal()

    def list_schools():
        schools = session.query(School).all()
        return [{"id": s.id, "name": s.name, "grading_system": s.grading_system or "Default"} for s in schools]

    def get_analytics():
        schools = session.query(School).all()
        analytics = []
        for s in schools:
            num_students = session.query(User).filter_by(school_id=s.id, role=UserRole.student).count()
            num_teachers = session.query(User).filter_by(school_id=s.id, role=UserRole.staff).count()
            analytics.append({
                "school_id": s.id,
                "name": s.name,
                "students": num_students,
                "teachers": num_teachers
            })
        return analytics

    while True:
        print("1. Register as Superuser")
        print("2. Register as School Admin")
        print("3. Login")
        print("4. Exit")
        choice = input("Select an option (1-4): ").strip()

        if choice == "1":
            print("\n--- Register as Superuser ---")
            full_name = validate_non_empty(input("Full Name: "), "Full Name")
            if not full_name:
                continue
            phone = validate_non_empty(input("Phone: "), "Phone")
            if not phone:
                continue
            email = validate_non_empty(input("Email: "), "Email")
            if not email:
                continue
            gender = validate_gender("Gender")
            if not gender:
                continue
            password = validate_non_empty(input("Password: "), "Password")
            if not password:
                continue
            result = register_superuser(full_name, phone, email, gender, password)
            if result["status"] == "success":
                print(f"[Success] Superuser created: {result['username']} / {result['email']}")
            else:
                print(f"[Error] {result['message']}")
        elif choice == "2":
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
            gender = validate_gender("Gender")
            if not gender:
                continue
            initials = validate_initials(input("School Initials (2-5 uppercase letters): "), "School Initials")
            if not initials:
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
                initials=initials,
                acting_user=None
            )
            if result["status"] == "success":
                print(f"[Success] School and admin created: {result['admin_username']} / {result['admin_email']}")
            else:
                print(f"[Error] {result['message']}")
        elif choice == "3":
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
                    print("1. List Schools")
                    print("2. View Analytics")
                    print("3. View Audit Logs")
                    print("4. Logout")
                    role_choice = input("Select an option (1-4): ").strip()
                    if role_choice == "1":
                        schools = list_schools()
                        print("\nSchools:")
                        if not schools:
                            print("[Info] No schools found")
                        for s in schools:
                            print(f"- ID: {s['id']}, Name: {s['name']}, Grading: {s['grading_system']}")
                    elif role_choice == "2":
                        analytics = get_analytics()
                        print("\nAnalytics:")
                        if not analytics:
                            print("[Info] No schools found")
                        for a in analytics:
                            print(f"School: {a['name']} (ID: {a['school_id']}) | Students: {a['students']} | Teachers: {a['teachers']}")
                    elif role_choice == "3":
                        from services.audit_log_services import query_audit_logs
                        logs = query_audit_logs()
                        print("\nAudit Logs:")
                        if not logs:
                            print("[Info] No audit logs found")
                        for log in logs:
                            print(f"- {log['timestamp']}: User {log['user_id']} {log['action']} - {log['message']}")
                    elif role_choice == "4":
                        print("Logging out...")
                        break
                    else:
                        print("[Error] Invalid option")
                elif user.role == UserRole.admin:
                    admin_school = session.query(School).filter_by(admin_id=user.id).first()
                    if not admin_school:
                        print("[Error] No school found for this admin")
                        break
                    print(f"\n--- Admin Menu for {admin_school.name} (ID: {admin_school.id}) ---")
                    print("1. List Students")
                    print("2. Create Class")
                    print("3. Manage Courses")
                    print("4. Create Teacher")
                    print("5. Enroll Student")
                    print("6. Logout")
                    admin_choice = input("Select an option (1-6): ").strip()
                    if admin_choice == "1":
                        students = session.query(User).filter_by(school_id=admin_school.id, role=UserRole.student).all()
                        print(f"\nStudents in {admin_school.name}:")
                        if not students:
                            print("[Info] No students found")
                        for s in students:
                            print(f"- ID: {s.id}, Name: {s.full_name}, Email: {s.email}")
                    elif admin_choice == "2":
                        class_name = validate_non_empty(input("Class Name: "), "Class Name")
                        if not class_name:
                            continue
                        academic_year = validate_non_empty(input("Academic Year (e.g., 2025-2026): "), "Academic Year")
                        if not academic_year:
                            continue
                        description = input("Description (optional): ").strip() or None
                        success, msg, class_result = create_class(class_name, admin_school.id, academic_year, description)
                        if success:
                            print(f"[Success] Class created: ID {class_result['id']}, Name: {class_result['name']}")
                        else:
                            print(f"[Error] {msg}")
                    elif admin_choice == "3":
                        print("1. List Courses")
                        print("2. Create Course")
                        course_choice = input("Select (1-2): ").strip()
                        if course_choice == "1":
                            courses = get_courses(school_id=admin_school.id)
                            print(f"\nCourses in {admin_school.name}:")
                            if not courses:
                                print("[Info] No courses found")
                            for c in courses:
                                print(f"- ID: {c['id']}, Title: {c['title']}, Code: {c['code']}, Teacher ID: {c['teacher_id'] or 'None'}")
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
                            grading_type = validate_non_empty(input("Grading Type (e.g., Letter, Pass/Fail): "), "Grading Type")
                            if not grading_type:
                                continue
                            teacher_id = input("Teacher ID (optional): ").strip()
                            teacher_id_val = validate_int(teacher_id, "Teacher ID", min_val=1) if teacher_id else None
                            if teacher_id_val:
                                teacher = session.query(User).filter_by(id=teacher_id_val, role=UserRole.staff, school_id=admin_school.id).first()
                                if not teacher:
                                    print(f"[Error] Teacher ID {teacher_id_val} not found in school {admin_school.name}")
                                    continue
                            teacher_full_name = input("Teacher Full Name (optional, for new teacher): ").strip() or None
                            teacher_gender = validate_gender("Teacher Gender")
                            if not teacher_gender:
                                continue
                            teacher_dob = validate_date(input("Teacher DOB (YYYY-MM-DD, optional): "), "Teacher DOB")
                            success, msg, data = create_course(
                                title, code, credit_hours, grading_type, None, admin_school.initials,
                                teacher_id=teacher_id_val, teacher_full_name=teacher_full_name,
                                teacher_gender=teacher_gender, teacher_dob=teacher_dob, school_id=admin_school.id
                            )
                            if success:
                                print(f"[Success] Course created: ID {data['course_id']}, Title: {data['title']}")
                            else:
                                print(f"[Error] {msg}")
                        else:
                            print("[Error] Invalid option")
                    elif admin_choice == "4":
                        full_name = validate_non_empty(input("Teacher Full Name: "), "Teacher Full Name")
                        if not full_name:
                            continue
                        gender = validate_gender("Gender")
                        if not gender:
                            continue
                        date_of_birth = validate_date(input("Date of Birth (YYYY-MM-DD, optional): "), "Date of Birth")
                        teacher, password = create_teacher_account(full_name, admin_school.initials, gender, date_of_birth, admin_school.id)
                        if teacher:
                            print(f"[Success] Teacher created: ID {teacher.id}, Name: {teacher.full_name}, Username: {teacher.username}, Password: {password}")
                        else:
                            print("[Error] Failed to create teacher")
                    elif admin_choice == "5":
                        full_name = validate_non_empty(input("Student Full Name: "), "Student Full Name")
                        if not full_name:
                            continue
                        class_id = validate_int(input("Class ID: "), "Class ID", min_val=1)
                        if not class_id:
                            continue
                        class_obj = session.query(Class).filter_by(id=class_id, school_id=admin_school.id).first()
                        if not class_obj:
                            print(f"[Error] Class ID {class_id} not found in school {admin_school.name}")
                            continue
                        gender = validate_gender("Gender")
                        if not gender:
                            continue
                        date_of_birth = validate_date(input("Date of Birth (YYYY-MM-DD, optional): "), "Date of Birth")
                        ok, msg, student_info = enroll_student(
                            full_name=full_name,
                            school_initials=admin_school.initials,
                            class_id=class_id,
                            gender=gender,
                            date_of_birth=date_of_birth
                        )
                        if ok and student_info:
                            print(f"[Success] Student enrolled: ID {student_info.get('id')}, Name: {student_info.get('full_name')}, Username: {student_info.get('username')}")
                        elif not ok:
                            print(f"[Error] {msg}")
                        else:
                            print("[Error] Student enrollment failed")
                    elif admin_choice == "6":
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
                        from models.course import Course
                        course = session.query(Course).filter_by(id=course_id, teacher_id=user_id).first()
                        if not course:
                            print(f"[Error] Course ID {course_id} not assigned to you")
                            continue
                        value = validate_float(input("Grade Value (0-100): "), "Grade Value", min_val=0, max_val=100)
                        if not value:
                            continue
                        ok, msg = upload_grade(student_id, course_id, value, user_id)
                        if ok:
                            print("[Success] Grade uploaded")
                        else:
                            print(f"[Error] {msg}")
                    elif tch_choice == "2":
                        from services.course_services import get_courses_for_teacher
                        courses = get_courses_for_teacher(user_id)
                        print("\nMy Courses:")
                        if not courses:
                            print("[Info] No courses assigned")
                        for c in courses:
                            print(f"- ID: {c['id']}, Title: {c['title']}, Code: {c['code']}")
                    elif tch_choice == "3":
                        class_id = validate_int(input("Class ID: "), "Class ID", min_val=1)
                        if not class_id:
                            continue
                        class_obj = session.query(Class).filter_by(id=class_id).first()
                        if not class_obj:
                            print(f"[Error] Class ID {class_id} not found")
                            continue
                        students = get_students(class_id)
                        print("\nMy Students:")
                        if not students:
                            print("[Info] No students found")
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
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("[Error] Invalid option")
    session.close()

if __name__ == "__main__":
    main()