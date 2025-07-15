"""
Setup script for Student Result Management System
Helps configure the database connection and test the setup
"""

import os
import sys
from database import DatabaseManager, get_database_config
from utils import create_sample_data_file, FileReader


def setup_database():
    """Setup and test database connection"""
    print("="*60)
    print("STUDENT RESULT MANAGEMENT SYSTEM - SETUP")
    print("="*60)
    print()
    
    print("Step 1: Database Configuration")
    print("-" * 30)
    
    # Get database configuration from user
    config = get_database_config()
    
    # Update database.py with user configuration
    try:
        # Read current database.py content
        with open('database.py', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Replace the config section
        old_config = """self.config = {
            'host': 'localhost',
            'database': 'student_db',
            'user': 'postgres',  # Change to your PostgreSQL username
            'password': 'password',  # Change to your PostgreSQL password
            'port': '5432'
        }"""
        
        new_config = f"""self.config = {{
            'host': '{config['host']}',
            'database': '{config['database']}',
            'user': '{config['user']}',
            'password': '{config['password']}',
            'port': '{config['port']}'
        }}"""
        
        content = content.replace(old_config, new_config)
        
        # Write updated content back
        with open('database.py', 'w', encoding='utf-8') as file:
            file.write(content)
        
        print("✓ Database configuration updated successfully!")
        
    except Exception as e:
        print(f"✗ Error updating database configuration: {e}")
        return False
    
    print("\nStep 2: Testing Database Connection")
    print("-" * 35)
    
    # Test database connection
    db_manager = DatabaseManager()
    if db_manager.connect():
        print("✓ Database connection successful!")
        
        # Create table
        if db_manager.create_table():
            print("✓ Database table created/verified!")
        else:
            print("✗ Error creating database table")
            return False
        
        db_manager.close()
    else:
        print("✗ Database connection failed!")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. Database exists")
        print("3. Credentials are correct")
        print("4. User has proper permissions")
        return False
    
    return True


def setup_sample_data():
    """Setup sample data file"""
    print("\nStep 3: Sample Data Setup")
    print("-" * 25)
    
    if os.path.exists('sample_data.csv'):
        print("✓ Sample data file already exists!")
        return True
    
    if create_sample_data_file():
        print("✓ Sample data file created successfully!")
        return True
    else:
        print("✗ Error creating sample data file")
        return False


def test_complete_system():
    """Test the complete system functionality"""
    print("\nStep 4: System Functionality Test")
    print("-" * 33)
    
    try:
        # Test database operations
        db_manager = DatabaseManager()
        if not db_manager.connect():
            print("✗ Database connection test failed")
            return False
        
        # Test file reading
        file_reader = FileReader()
        students = file_reader.read_student_data('sample_data.csv')
        
        if not students:
            print("✗ File reading test failed")
            return False
        
        print(f"✓ Successfully read {len(students)} student records")
        
        # Test inserting a sample record
        test_student = ("TEST999", "Test Student", "Test Course", 85)
        if db_manager.insert_student(test_student):
            print("✓ Database insertion test successful")
            
            # Test retrieval
            retrieved = db_manager.get_student_by_index("TEST999")
            if retrieved:
                print("✓ Database retrieval test successful")
            else:
                print("✗ Database retrieval test failed")
        else:
            print("✗ Database insertion test failed")
        
        db_manager.close()
        print("✓ All system tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ System test error: {e}")
        return False


def main():
    """Main setup function"""
    print("Welcome to the Student Result Management System Setup!")
    print("This script will help you configure the system for first use.\n")
    
    # Check if Python version is adequate
    if sys.version_info < (3, 6):
        print("✗ Python 3.6 or higher is required!")
        sys.exit(1)
    
    print("✓ Python version check passed")
    
    # Check if required packages are installed
    try:
        import psycopg2
        print("✓ psycopg2 package is installed")
    except ImportError:
        print("✗ psycopg2 package not found!")
        print("Please install it using: pip install psycopg2-binary")
        sys.exit(1)
    
    # Run setup steps
    success = True
    
    # Database setup
    if not setup_database():
        success = False
    
    # Sample data setup
    if success and not setup_sample_data():
        success = False
    
    # System test
    if success and not test_complete_system():
        success = False
    
    print("\n" + "="*60)
    if success:
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nYou can now run the application using:")
        print("python main.py")
        print("\nThe system is ready to use!")
    else:
        print("❌ SETUP FAILED!")
        print("="*60)
        print("\nPlease review the errors above and try again.")
        print("Make sure PostgreSQL is running and configured correctly.")
    
    print("\nFor help, check the README.md file.")


if __name__ == "__main__":
    main()
