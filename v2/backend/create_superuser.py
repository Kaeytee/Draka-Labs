"""
Script to create a superuser (application owner) for the School Management System.
This script is intended for use by the system owner only and should NOT be exposed via any API or normal CLI route.
"""
import sys
import getpass
from database.db import SessionLocal
from models.user import Gender
from services.accounts import register_superuser

def validate_non_empty(value, prompt):
    if not value.strip():
        print(f"[Error] {prompt} cannot be empty")
        return None
    return value.strip()

def validate_gender(gender, prompt="Gender"):
    valid_genders = [g.value for g in Gender]
    if gender.lower() not in valid_genders:
        print(f"[Error] {prompt} must be one of: {', '.join(valid_genders)}")
        return None
    return gender.lower()

def main():
    print("\n=== Superuser Creation Script ===\n")
    session = SessionLocal()

    # Keep prompting until valid input is given for each field
    while True:
        full_name = validate_non_empty(input("Full Name: "), "Full Name")
        if full_name:
            break
    while True:
        phone = validate_non_empty(input("Phone: "), "Phone")
        if phone:
            break
    while True:
        email = validate_non_empty(input("Email: "), "Email")
        if email:
            break
    while True:
        gender = validate_gender(input(f"Gender ({', '.join([g.value for g in Gender])}): "), "Gender")
        if gender:
            break
    while True:
        password = getpass.getpass("Password: ")
        if password:
            break
        print("[Error] Password cannot be empty")

    result = register_superuser(full_name, phone, email, gender, password)
    if result["status"] == "success":
        print(f"[Success] Superuser created: {result['username']} / {result['email']}")
    else:
        print(f"[Error] {result['message']}")
    session.close()

if __name__ == "__main__":
    main()
