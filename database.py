"""
Database operations for Student Result Management System
Handles PostgreSQL connection and CRUD operations
"""

import psycopg2
from psycopg2 import sql
from utils import calculate_grade


class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""
    
    def __init__(self):
        """Initialize database configuration"""
        # Database configuration - modify these settings for your environment
        self.config = {
            'host': 'localhost',
            'database': 'student_db',
            'user': 'postgres',  # Change to your PostgreSQL username
            'password': 'password',  # Change to your PostgreSQL password
            'port': '5432'
        }
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establish connection to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.config)
            self.cursor = self.connection.cursor()
            print("Connected to PostgreSQL database successfully.")
            return True
        except psycopg2.Error as e:
            print(f"Error connecting to PostgreSQL database: {e}")
            print("Please check your database configuration and ensure PostgreSQL is running.")
            return False
    
    def create_table(self):
        """Create the student_results table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS student_results (
            id SERIAL PRIMARY KEY,
            index_number VARCHAR(10) NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            course TEXT NOT NULL,
            score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
            grade CHAR(1) NOT NULL
        );
        """
        
        try:
            self.cursor.execute(create_table_query)
            self.connection.commit()
            print("Table 'student_results' ready.")
            return True
        except psycopg2.Error as e:
            print(f"Error creating table: {e}")
            return False
    
    def insert_student(self, student_data):
        """Insert a new student record into the database"""
        try:
            index_number, full_name, course, score = student_data
            grade = calculate_grade(score)
            
            insert_query = """
            INSERT INTO student_results (index_number, full_name, course, score, grade)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            self.cursor.execute(insert_query, (index_number, full_name, course, score, grade))
            self.connection.commit()
            return True
            
        except psycopg2.IntegrityError as e:
            print(f"Student with index {index_number} already exists.")
            self.connection.rollback()
            return False
        except psycopg2.Error as e:
            print(f"Error inserting student record: {e}")
            self.connection.rollback()
            return False
    
    def get_all_students(self):
        """Retrieve all student records from the database"""
        try:
            select_query = """
            SELECT id, index_number, full_name, course, score, grade
            FROM student_results
            ORDER BY index_number
            """
            
            self.cursor.execute(select_query)
            return self.cursor.fetchall()
            
        except psycopg2.Error as e:
            print(f"Error retrieving student records: {e}")
            return []
    
    def get_student_by_index(self, index_number):
        """Retrieve a specific student by index number"""
        try:
            select_query = """
            SELECT id, index_number, full_name, course, score, grade
            FROM student_results
            WHERE index_number = %s
            """
            
            self.cursor.execute(select_query, (index_number,))
            return self.cursor.fetchone()
            
        except psycopg2.Error as e:
            print(f"Error retrieving student record: {e}")
            return None
    
    def update_student_score(self, index_number, new_score):
        """Update a student's score and recalculate grade"""
        try:
            new_grade = calculate_grade(new_score)
            
            update_query = """
            UPDATE student_results
            SET score = %s, grade = %s
            WHERE index_number = %s
            """
            
            self.cursor.execute(update_query, (new_score, new_grade, index_number))
            self.connection.commit()
            
            if self.cursor.rowcount > 0:
                return True
            else:
                print(f"No student found with index number: {index_number}")
                return False
                
        except psycopg2.Error as e:
            print(f"Error updating student score: {e}")
            self.connection.rollback()
            return False
    
    def get_grade_distribution(self):
        """Get grade distribution statistics"""
        try:
            distribution_query = """
            SELECT grade, COUNT(*) as count
            FROM student_results
            GROUP BY grade
            ORDER BY grade
            """
            
            self.cursor.execute(distribution_query)
            results = self.cursor.fetchall()
            
            # Convert to dictionary
            distribution = {}
            for grade, count in results:
                distribution[grade] = count
                
            return distribution
            
        except psycopg2.Error as e:
            print(f"Error getting grade distribution: {e}")
            return {}
    
    def get_total_students(self):
        """Get total number of students in the database"""
        try:
            count_query = "SELECT COUNT(*) FROM student_results"
            self.cursor.execute(count_query)
            result = self.cursor.fetchone()
            return result[0] if result else 0
            
        except psycopg2.Error as e:
            print(f"Error getting total student count: {e}")
            return 0
    
    def get_average_score(self):
        """Get average score of all students"""
        try:
            avg_query = "SELECT AVG(score) FROM student_results"
            self.cursor.execute(avg_query)
            result = self.cursor.fetchone()
            return round(result[0], 2) if result and result[0] else 0
            
        except psycopg2.Error as e:
            print(f"Error getting average score: {e}")
            return 0
    
    def close(self):
        """Close database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            print("Database connection closed.")
        except psycopg2.Error as e:
            print(f"Error closing database connection: {e}")


# Database configuration helper function
def get_database_config():
    """Helper function to get database configuration from user"""
    print("\nDatabase Configuration Required:")
    print("Please provide your PostgreSQL database details:")
    
    config = {}
    config['host'] = input("Host (default: localhost): ").strip() or 'localhost'
    config['database'] = input("Database name (default: student_db): ").strip() or 'student_db'
    config['user'] = input("Username (default: postgres): ").strip() or 'postgres'
    config['password'] = input("Password: ").strip()
    config['port'] = input("Port (default: 5432): ").strip() or '5432'
    
    return config


def test_database_connection():
    """Test database connection with sample operations"""
    db = DatabaseManager()
    
    if db.connect():
        print("Connection test successful!")
        db.create_table()
        
        # Test inserting sample data
        sample_student = ("TEST001", "Test Student", "Computer Science", 85)
        if db.insert_student(sample_student):
            print("Sample insert successful!")
            
            # Test retrieval
            student = db.get_student_by_index("TEST001")
            if student:
                print(f"Sample retrieval successful: {student}")
                
        db.close()
    else:
        print("Connection test failed!")


if __name__ == "__main__":
    # Run database connection test
    test_database_connection()
