"""
Student Result Management CLI Tool
Main application entry point
"""

import sys
from database import DatabaseManager
from utils import FileReader, ReportGenerator, validate_score, validate_index


def display_menu():
    """Display the main menu options"""
    print("\n" + "="*50)
    print("   STUDENT RESULT MANAGEMENT SYSTEM")
    print("="*50)
    print("1. View all records")
    print("2. View student by index number")
    print("3. Update student score")
    print("4. Export summary report to file")
    print("5. Exit")
    print("="*50)


def get_user_choice():
    """Get and validate user menu choice"""
    try:
        choice = input("Enter your choice (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            return int(choice)
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")
            return None
    except KeyboardInterrupt:
        print("\n\nExiting application...")
        sys.exit(0)


def view_all_records(db_manager):
    """Display all student records"""
    try:
        records = db_manager.get_all_students()
        if not records:
            print("\nNo records found in the database.")
            return
        
        print(f"\n{'Index':<10} {'Name':<25} {'Course':<20} {'Score':<8} {'Grade':<5}")
        print("-" * 70)
        
        for record in records:
            print(f"{record[1]:<10} {record[2]:<25} {record[3]:<20} {record[4]:<8} {record[5]:<5}")
            
        print(f"\nTotal records: {len(records)}")
        
    except Exception as e:
        print(f"Error retrieving records: {e}")


def view_student_by_index(db_manager):
    """View a specific student by index number"""
    try:
        index_number = input("Enter student index number: ").strip().upper()
        
        if not validate_index(index_number):
            print("Invalid index number format.")
            return
            
        student = db_manager.get_student_by_index(index_number)
        
        if student:
            print(f"\nStudent Details:")
            print(f"Index Number: {student[1]}")
            print(f"Full Name: {student[2]}")
            print(f"Course: {student[3]}")
            print(f"Score: {student[4]}")
            print(f"Grade: {student[5]}")
        else:
            print(f"No student found with index number: {index_number}")
            
    except Exception as e:
        print(f"Error searching for student: {e}")


def update_student_score(db_manager):
    """Update a student's score and recalculate grade"""
    try:
        index_number = input("Enter student index number: ").strip().upper()
        
        if not validate_index(index_number):
            print("Invalid index number format.")
            return
            
        # Check if student exists
        student = db_manager.get_student_by_index(index_number)
        if not student:
            print(f"No student found with index number: {index_number}")
            return
            
        print(f"Current score for {student[2]}: {student[4]}")
        
        try:
            new_score = int(input("Enter new score (0-100): "))
            
            if not validate_score(new_score):
                print("Score must be between 0 and 100.")
                return
                
            # Confirm update
            confirm = input(f"Update score to {new_score}? (y/n): ").strip().lower()
            if confirm == 'y':
                success = db_manager.update_student_score(index_number, new_score)
                if success:
                    print("Score updated successfully!")
                else:
                    print("Failed to update score.")
            else:
                print("Update cancelled.")
                
        except ValueError:
            print("Invalid score. Please enter a number.")
            
    except Exception as e:
        print(f"Error updating student score: {e}")


def export_summary_report(db_manager):
    """Export summary report to file"""
    try:
        report_generator = ReportGenerator(db_manager)
        filename = report_generator.generate_summary_report()
        
        if filename:
            print(f"\nSummary report exported successfully to: {filename}")
        else:
            print("Failed to generate summary report.")
            
    except Exception as e:
        print(f"Error generating report: {e}")


def load_initial_data(db_manager):
    """Load initial data from file if database is empty"""
    try:
        # Check if database has any records
        records = db_manager.get_all_students()
        if records:
            print(f"Database contains {len(records)} existing records.")
            return
            
        # Ask user if they want to load data from file
        load_data = input("Database is empty. Load data from file? (y/n): ").strip().lower()
        if load_data != 'y':
            return
            
        filename = input("Enter filename (or press Enter for 'sample_data.csv'): ").strip()
        if not filename:
            filename = "sample_data.csv"
            
        file_reader = FileReader()
        students = file_reader.read_student_data(filename)
        
        if students:
            print(f"Loading {len(students)} records into database...")
            success_count = 0
            
            for student in students:
                if db_manager.insert_student(student):
                    success_count += 1
                    
            print(f"Successfully loaded {success_count} out of {len(students)} records.")
        else:
            print("No valid data found in file.")
            
    except FileNotFoundError:
        print(f"File '{filename}' not found. You can add records manually or create the file.")
    except Exception as e:
        print(f"Error loading initial data: {e}")


def main():
    """Main application function"""
    print("Initializing Student Result Management System...")
    
    # Initialize database connection
    try:
        db_manager = DatabaseManager()
        if not db_manager.connect():
            print("Failed to connect to database. Exiting...")
            sys.exit(1)
            
        # Create table if it doesn't exist
        db_manager.create_table()
        print("Database connection established successfully.")
        
        # Load initial data if needed
        load_initial_data(db_manager)
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        sys.exit(1)
    
    # Main application loop
    try:
        while True:
            display_menu()
            choice = get_user_choice()
            
            if choice is None:
                continue
                
            if choice == 1:
                view_all_records(db_manager)
            elif choice == 2:
                view_student_by_index(db_manager)
            elif choice == 3:
                update_student_score(db_manager)
            elif choice == 4:
                export_summary_report(db_manager)
            elif choice == 5:
                print("\nThank you for using Student Result Management System!")
                break
                
            input("\nPress Enter to continue...")
            
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Close database connection
        if 'db_manager' in locals():
            db_manager.close()
        print("Database connection closed. Goodbye!")


if __name__ == "__main__":
    main()
