# Student Result Management CLI Tool

A command-line Python application for managing student results with PostgreSQL database integration.

## Features

- **File Reading**: Import student data from CSV/TXT files
- **Database Integration**: Store and manage data in PostgreSQL
- **Grade Calculation**: Automatic grade assignment based on scores
- **Interactive CLI**: User-friendly command-line interface
- **Report Generation**: Export summary reports with statistics
- **Data Validation**: Input validation and error handling

## Prerequisites

- Python 3.6 or higher
- PostgreSQL database server
- pip (Python package installer)

## Installation

1. **Clone or download the project files**
   ```
   student-result-management/
   ├── main.py
   ├── database.py
   ├── utils.py
   ├── sample_data.csv
   ├── requirements.txt
   └── README.md
   ```

2. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**
   - Install PostgreSQL if not already installed
   - Create a database named `student_db`
   - Create a user with appropriate permissions
   - Note down your database credentials

4. **Configure database connection**
   Edit the database configuration in `database.py`:
   ```python
   self.config = {
       'host': 'localhost',
       'database': 'student_db',
       'user': 'your_username',
       'password': 'your_password',
       'port': '5432'
   }
   ```

## Usage

1. **Run the application**
   ```bash
   python main.py
   ```

2. **Menu Options**
   ```
   1. View all records
   2. View student by index number
   3. Update student score
   4. Export summary report to file
   5. Exit
   ```

3. **Loading Initial Data**
   - On first run, the system will offer to load data from `sample_data.csv`
   - You can also manually add records through the interface

## File Format

### CSV Format
```csv
IndexNumber,FullName,Course,Score
ST001,John Doe,Computer Science,85
ST002,Jane Smith,Mathematics,92
```

### TXT Format (comma or tab separated)
```
ST001,John Doe,Computer Science,85
ST002,Jane Smith,Mathematics,92
```

## Grading Scale

- **A**: 80-100 points
- **B**: 70-79 points
- **C**: 60-69 points
- **D**: 50-59 points
- **F**: 0-49 points

## Database Schema

```sql
CREATE TABLE student_results (
    id SERIAL PRIMARY KEY,
    index_number VARCHAR(10) NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    course TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    grade CHAR(1) NOT NULL
);
```

## Report Output

Summary reports are generated in the `reports/` directory with the following format:

```
STUDENT RESULT SUMMARY REPORT
==================================================
Generated on: 2025-07-14 10:30:00

BASIC STATISTICS
--------------------
Total Students: 30
Average Score: 79.5

GRADE DISTRIBUTION
--------------------
A:  8 students ( 26.7%)
B:  9 students ( 30.0%)
C:  7 students ( 23.3%)
D:  4 students ( 13.3%)
F:  2 students (  6.7%)

PERFORMANCE ANALYSIS
--------------------
Pass Rate: 93.3% (28 students)
Fail Rate: 6.7% (2 students)
```

## Error Handling

The application handles various error scenarios:
- Database connection failures
- File reading errors
- Invalid input validation
- Score range validation (0-100)
- Duplicate index numbers

## Testing

### Test Database Connection
```bash
python database.py
```

### Test Utility Functions
```bash
python utils.py
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running
   - Check database credentials in `database.py`
   - Verify database and user exist

2. **Module Import Error**
   - Install required packages: `pip install psycopg2-binary`
   - Ensure all files are in the same directory

3. **File Not Found**
   - Check file path and name
   - Ensure CSV file has proper headers
   - Verify file permissions

### PostgreSQL Setup Commands

```sql
-- Create database
CREATE DATABASE student_db;

-- Create user (optional)
CREATE USER student_user WITH PASSWORD 'your_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE student_db TO student_user;
```

## Project Structure

```
student-result-management/
├── main.py              # Main application entry point
├── database.py          # Database operations
├── utils.py            # Utility functions
├── sample_data.csv     # Sample student data
├── requirements.txt    # Dependencies
├── README.md          # Documentation
└── reports/           # Generated reports (created automatically)
```

## Contributing

This is a learning project demonstrating:
- Raw Python programming
- Database operations with PostgreSQL
- File I/O operations
- CLI application development
- Error handling and validation

## License

This project is for educational purposes and demonstrates fundamental programming concepts in Python.

## Version History

- **v1.0**: Initial release with core functionality
- Basic CRUD operations
- File import/export
- Grade calculation
- Report generation
