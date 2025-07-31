from services.audit_log_services import log_audit

from database.db import SessionLocal
from models.user import User, UserRole
from models.school import School
import random
import string
import hashlib
import json
from config import DEFAULT_GRADING_SYSTEM

def generate_initials(school_name):
	"""
	Generate initials from the school name.
	Example: 'University of Ghana' -> 'UG'
	"""
	return ''.join(word[0].upper() for word in school_name.split() if word[0].isalpha())


def generate_school_id(school_name, length=8):
	"""
	Generate a unique school ID using school initials and a random numeric suffix.
	Example: 'University of Ghana' -> 'UG123456'
	- school_name: The full name of the school.
	- length: Number of random digits to append (default: 6).
	Returns: A string like 'UG123456'
	"""
	initials = generate_initials(school_name)
	random_digits="".join(random.choices(string.digits, k=length))
	return f"{initials}{random_digits}"


def generate_username(full_name):
	"""
	Generate a username based on the full name.
	- 'Austin Bediako' -> 'abediako'
	- 'Austin Tsibuah Bediako' -> 'atbediako'
	- 'John Michael Doe' -> 'jmdoe'
	"""
	names = full_name.strip().split()
	if len(names) < 2:
		return names[0].lower() if names else "user"
	elif len(names) ==2:
		return names[0][0].lower() + names[1].lower()
	else:
		#use the first letter of first and second names+ full last name
		return f"{names[0][0].lower()}.{names[1][0].lower()}.{names[2].lower()}"
	
def generate_unique_username_email(db, base_username, initials, role):
	"""
	Ensure username and email are unique in the database 
	Email Format: {username}_initials_{role}@schoolsystem.com
	"""
	username = base_username
	suffix= 1





	#ensure there is uniqueness in the username 
	while db.query(User).filter_by(username=username).first():
		username = f"{base_username}_{suffix}"
		suffix += 1
	#Email Pattern 
	if role =="student":
		email= f"{username}@st.{initials.lower()}.schoolsystem.com"
	else:
		email=f"{username}@{initials.lower()}.schoolsystem.com"

	#ensure unique email

	while db.query(User).filter_by(email=email).first():
		if role=="student":
			email = f"{username}{suffix}@st.{initials.lower()}.schoolsystem.com"
		else:
			email = f"{username}{suffix}@{initials.lower()}.schoolsystem.com"
		suffix += 1

	return username, email



def generate_password(initials, user_id):
	"""
	
	Generate password based on school initials and user ID.
	Example: UG+!+12345
	
	"""
	return f"{initials.upper()}+!+{user_id}"

# def generate_email_and_password(role, initials, user_id):
# 	"""
# 	Generate email and password based on user role and school
# 	initials.
# 	"""

# 	if role== "admin":
# 		email = f"{role}.{initials}@schoolsys.edu.gh.com"
# 	elif role=="teacher":
# 		email = f"{role}.{initials}@schoolsys.edu.gh.com"
# 	elif role=="student":
# 		email = f"{role}.{initials}@st.schoolsys.edu.gh.com"


def register_school_admin(school_name, full_name, phone, email, gender, grading_system):
	"""
	Register a new school and its admin 
	Only Schools register directly; all other users are auto generated
	"""
	db = SessionLocal()
	try:
		initials = generate_initials(school_name)
		# Generate a unique school ID
		school_id = generate_school_id(school_name)
		base_username = generate_username(full_name)
		admin_username, admin_email = generate_unique_username_email(db, base_username, initials, "admin")
		# Generate a password for the admin user
		password = generate_password(initials, school_id)
		hashed_password = hashlib.sha256(password.encode()).hexdigest()

		# Use default grading system if not provided
		if not grading_system:
			grading_system = DEFAULT_GRADING_SYSTEM
		# Store as JSON string
		grading_system_json = json.dumps(grading_system)

		# Check for duplicate school name
		if db.query(School).filter_by(name=school_name).first():
			return {
				"status": "error",
				"message": f"School name '{school_name}' already exists."
			}

		# Create the admin user
		from models.user import Gender
		admin_user = User(
			username=admin_username,
			full_name=full_name,
			hashed_password=hashed_password,
			email=admin_email,
			role=UserRole.admin,
			gender=Gender[gender.lower()] if isinstance(gender, str) else gender
		)
		db.add(admin_user)
		db.commit()
		db.refresh(admin_user)

		# Audit log for admin registration
		log_audit(admin_user.id, "register_school_admin", f"Admin {admin_username} registered school {school_name}")

		# Create the school model instance here
		school = School(
			name=school_name,
			initials=initials,
			admin_id=admin_user.id,
			grading_system=grading_system_json,
			phone=phone,
			email=email
		)
		db.add(school)
		db.commit()
		db.refresh(school)

		# Audit log for school registration
		log_audit(admin_user.id, "register_school", f"School {school_name} registered by admin {admin_username}")

		return {
			"status": "success",
			"message": "School and admin registered successfully.",
			"admin_username": admin_username,
			"admin_email": admin_email,
			"password": password
		}
	except Exception as e:
		db.rollback()
		# Handle duplicate key error for school name
		if "duplicate key value violates unique constraint" in str(e) and "schools_name_key" in str(e):
			return {
				"status": "error",
				"message": f"School name '{school_name}' already exists."
			}
		return {
			"status": "error",
			"message": str(e)
		}
	finally:
		db.close()

def create_student_account(db, full_name, school_initials, gender):
	"""
	Auto-generate a student account (Called by microservices not user )
	"""
	base_username = generate_username(full_name)
	username, email = generate_unique_username_email(db, base_username, school_initials, "student")
	password = generate_password(school_initials, username)
	hashed_password = hashlib.sha256(password.encode()).hexdigest()

	#Create the student db
	student = User(
		username=username,
		full_name=full_name,
		gender=gender,
		hashed_password=hashed_password,
		email=email,
		role=UserRole.student
	)
	db.add(student)
	db.commit()
	db.refresh(student)
	# Audit log for student account creation
	log_audit(student.id, "create_student_account", f"Student {username} created for {full_name}")
	return student, password

def create_teacher_account(db, full_name, school_initials):
	""""
	Auto generate a teacher account (called by microservice , not user )
	"""
	base_username=generate_username(full_name)
	username,email = generate_unique_username_email(db, base_username, school_initials, "teacher")
	user_id= "".join(random.choices(string.digits, k=6))
	password= generate_password(school_initials, user_id)
	hashed_password= hashlib.sha256(password.encode()).hexdigest()

	# create teacher db 



	teacher = User(
		username=username,
		full_name=full_name,
		hashed_password=hashed_password,
		email=email,
		role=UserRole.staff
	)