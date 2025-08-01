"""
Utility functions for Student Result Management System
Includes file operations, grade calculation, and validation functions
"""

import csv
import os
from datetime import datetime


def calculate_grade(score):
    """Calculate letter grade based on numeric score"""
    try:
        score = int(score)
        if score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
    except (ValueError, TypeError):
        return 'F'


def validate_score(score):
    """Validate that score is within acceptable range (0-100)"""
    try:
        score = int(score)
        return 0 <= score <= 100
    except (ValueError, TypeError):
        return False


def validate_index(index_number):
    """Validate index number format"""
    if not index_number or len(index_number.strip()) == 0:
        return False
    
    # Basic validation - adjust pattern as needed
    index_number = index_number.strip().upper()
    return len(index_number) >= 3 and len(index_number) <= 10


class FileReader:
    """Handles reading student data from files"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.txt']
    
    def read_student_data(self, filename):
        """Read student data from CSV or TXT file"""
        try:
            if not os.path.exists(filename):
                raise FileNotFoundError(f"File '{filename}' not found")
            
            students = []
            file_extension = os.path.splitext(filename)[1].lower()
            
            if file_extension == '.csv':
                students = self._read_csv_file(filename)
            elif file_extension == '.txt':
                students = self._read_txt_file(filename)
            else:
                print(f"Unsupported file format: {file_extension}")
                return []
            
            # Validate and clean data
            valid_students = []
            for i, student in enumerate(students, 1):
                if self._validate_student_data(student, i):
                    valid_students.append(student)
            
            return valid_students
            
        except Exception as e:
            print(f"Error reading file '{filename}': {e}")
            return []
    
    def _read_csv_file(self, filename):
        """Read data from CSV file"""
        students = []
        
        with open(filename, 'r', newline='', encoding='utf-8') as file:
            # Try to detect if file has headers
            sample = file.read(1024)
            file.seek(0)
            
            sniffer = csv.Sniffer()
            has_header = sniffer.has_header(sample)
            
            reader = csv.reader(file)
            
            # Skip header if present
            if has_header:
                next(reader)
            
            for row_num, row in enumerate(reader, 1):
                if len(row) >= 4:
                    try:
                        index_number = row[0].strip().upper()
                        full_name = row[1].strip()
                        course = row[2].strip()
                        score = int(row[3].strip())
                        
                        students.append((index_number, full_name, course, score))
                    except (ValueError, IndexError) as e:
                        print(f"Error processing row {row_num}: {e}")
                        continue
                else:
                    print(f"Row {row_num}: Insufficient data (expected 4 columns, got {len(row)})")
        
        return students
    
    def _read_txt_file(self, filename):
        """Read data from TXT file (comma-separated or tab-separated)"""
        students = []
        
        with open(filename, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line or line.startswith('#'):  # Skip empty lines and comments
                    continue
                
                # Try comma-separated first, then tab-separated
                parts = line.split(',')
                if len(parts) < 4:
                    parts = line.split('\t')
                
                if len(parts) >= 4:
                    try:
                        index_number = parts[0].strip().upper()
                        full_name = parts[1].strip()
                        course = parts[2].strip()
                        score = int(parts[3].strip())
                        
                        students.append((index_number, full_name, course, score))
                    except (ValueError, IndexError) as e:
                        print(f"Error processing line {line_num}: {e}")
                        continue
                else:
                    print(f"Line {line_num}: Insufficient data (expected 4 fields)")
        
        return students
    
    def _validate_student_data(self, student_data, row_num):
        """Validate individual student record"""
        try:
            index_number, full_name, course, score = student_data
            
            # Validate index number
            if not validate_index(index_number):
                print(f"Row {row_num}: Invalid index number '{index_number}'")
                return False
            
            # Validate full name
            if not full_name or len(full_name.strip()) < 2:
                print(f"Row {row_num}: Invalid full name '{full_name}'")
                return False
            
            # Validate course
            if not course or len(course.strip()) < 2:
                print(f"Row {row_num}: Invalid course '{course}'")
                return False
            
            # Validate score
            if not validate_score(score):
                print(f"Row {row_num}: Invalid score '{score}' (must be 0-100)")
                return False
            
            return True
            
        except Exception as e:
            print(f"Row {row_num}: Validation error - {e}")
            return False


class ReportGenerator:
    """Handles generation of summary reports"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.reports_dir = "reports"
    
    def generate_summary_report(self):
        """Generate and save summary report to file"""
        try:
            # Create reports directory if it doesn't exist
            if not os.path.exists(self.reports_dir):
                os.makedirs(self.reports_dir)
            
            # Get data from database
            total_students = self.db_manager.get_total_students()
            grade_distribution = self.db_manager.get_grade_distribution()
            average_score = self.db_manager.get_average_score()
            all_students = self.db_manager.get_all_students()
            
            # Generate report content
            report_content = self._format_report(total_students, grade_distribution, average_score, all_students)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.reports_dir, f"summary_report_{timestamp}.txt")
            
            # Write report to file
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(report_content)
            
            return filename
            
        except Exception as e:
            print(f"Error generating report: {e}")
            return None
    
    def _format_report(self, total_students, grade_distribution, average_score, all_students):
        """Format the report content"""
        report = []
        report.append("STUDENT RESULT SUMMARY REPORT")
        report.append("=" * 50)
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Basic statistics
        report.append("BASIC STATISTICS")
        report.append("-" * 20)
        report.append(f"Total Students: {total_students}")
        report.append(f"Average Score: {average_score}")
        report.append("")
        
        # Student list with names and grades
        report.append("STUDENT LIST")
        report.append("-" * 40)
        report.append(f"{'Index':<10} {'Name':<25} {'Grade':<5}")
        report.append("-" * 40)
        
        for student in all_students:
            # student format: (id, index_number, full_name, course, score, grade)
            index_num = student[1]
            name = student[2]
            grade = student[5]
            report.append(f"{index_num:<10} {name:<25} {grade:<5}")
        
        report.append("")
        
        # Grade distribution
        report.append("GRADE DISTRIBUTION")
        report.append("-" * 20)
        
        # Ensure all grades are represented
        all_grades = ['A', 'B', 'C', 'D', 'F']
        for grade in all_grades:
            count = grade_distribution.get(grade, 0)
            percentage = (count / total_students * 100) if total_students > 0 else 0
            report.append(f"{grade}: {count:3d} students ({percentage:5.1f}%)")
        
        report.append("")
        
        # Performance analysis
        report.append("PERFORMANCE ANALYSIS")
        report.append("-" * 20)
        
        passing_grades = ['A', 'B', 'C', 'D']
        passing_count = sum(grade_distribution.get(grade, 0) for grade in passing_grades)
        failing_count = grade_distribution.get('F', 0)
        
        if total_students > 0:
            pass_rate = (passing_count / total_students) * 100
            fail_rate = (failing_count / total_students) * 100
            
            report.append(f"Pass Rate: {pass_rate:.1f}% ({passing_count} students)")
            report.append(f"Fail Rate: {fail_rate:.1f}% ({failing_count} students)")
        
        report.append("")
        report.append("=" * 50)
        report.append("End of Report")
        
        return "\n".join(report)


def create_sample_data_file():
    """Create a sample data file for testing"""
    sample_data = [
        ["IndexNumber", "FullName", "Course", "Score"],
        ["ST001", "John Doe", "Computer Science", "85"],
        ["ST002", "Jane Smith", "Mathematics", "92"],
        ["ST003", "Bob Johnson", "Physics", "78"],
        ["ST004", "Alice Brown", "Chemistry", "67"],
        ["ST005", "Charlie Wilson", "Biology", "89"],
        ["ST006", "Diana Davis", "Computer Science", "95"],
        ["ST007", "Eve Miller", "Mathematics", "72"],
        ["ST008", "Frank Garcia", "Physics", "81"],
        ["ST009", "Grace Lee", "Chemistry", "58"],
        ["ST010", "Henry Wang", "Biology", "74"],
        ["ST011", "Ivy Chen", "Computer Science", "88"],
        ["ST012", "Jack Taylor", "Mathematics", "76"],
        ["ST013", "Kelly Anderson", "Physics", "83"],
        ["ST014", "Leo Martinez", "Chemistry", "91"],
        ["ST015", "Maya Patel", "Biology", "79"],
        ["ST016", "Noah Kim", "Computer Science", "87"],
        ["ST017", "Olivia Thompson", "Mathematics", "94"],
        ["ST018", "Paul Rodriguez", "Physics", "65"],
        ["ST019", "Quinn O'Connor", "Chemistry", "82"],
        ["ST020", "Ruby Williams", "Biology", "77"]
    ]
    
    try:
        with open("sample_data.csv", "w", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(sample_data)
        print("Sample data file 'sample_data.csv' created successfully.")
        return True
    except Exception as e:
        print(f"Error creating sample data file: {e}")
        return False


def format_student_display(students):
    """Format student data for display"""
    if not students:
        return "No students to display."
    
    output = []
    output.append(f"{'Index':<10} {'Name':<25} {'Course':<20} {'Score':<8} {'Grade':<5}")
    output.append("-" * 70)
    
    for student in students:
        if len(student) >= 4:
            index_num, name, course, score = student[:4]
            grade = calculate_grade(score)
            output.append(f"{index_num:<10} {name:<25} {course:<20} {score:<8} {grade:<5}")
    
    return "\n".join(output)


# Test functions
def test_grade_calculation():
    """Test the grade calculation function"""
    test_scores = [95, 85, 75, 65, 55, 45, 100, 0]
    expected_grades = ['A', 'A', 'B', 'C', 'D', 'F', 'A', 'F']
    
    print("Testing grade calculation:")
    for score, expected in zip(test_scores, expected_grades):
        calculated = calculate_grade(score)
        status = "✓" if calculated == expected else "✗"
        print(f"Score {score}: Expected {expected}, Got {calculated} {status}")


def test_file_operations():
    """Test file reading operations"""
    print("Testing file operations:")
    
    # Create sample file if it doesn't exist
    if not os.path.exists("sample_data.csv"):
        create_sample_data_file()
    
    # Test file reading
    file_reader = FileReader()
    students = file_reader.read_student_data("sample_data.csv")
    
    print(f"Successfully read {len(students)} student records.")
    if students:
        print("Sample records:")
        for i, student in enumerate(students[:3]):  # Show first 3 records
            print(f"  {i+1}. {student}")


if __name__ == "__main__":
    # Run tests when module is executed directly
    print("Running utility function tests...\n")
    test_grade_calculation()
    print()
    test_file_operations()
