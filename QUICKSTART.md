# Quick Start Guide - Student Result Management CLI Tool

## 🚀 Quick Setup (5 minutes)

### Prerequisites Check
- ✅ Python 3.6+ installed
- ✅ PostgreSQL database server running
- ✅ Basic database knowledge

### Step 1: Install Dependencies
```bash
pip install psycopg2-binary
```

### Step 2: Database Setup
Create a PostgreSQL database:
```sql
CREATE DATABASE student_db;
```

### Step 3: Run Setup Script
```bash
python setup.py
```
The setup script will:
- Configure database connection
- Create necessary tables
- Generate sample data
- Test the system

### Step 4: Run Application
```bash
python main.py
```

## 📝 Basic Usage

### Menu Options
1. **View all records** - Display all students
2. **View student by index** - Search specific student
3. **Update student score** - Modify scores and grades
4. **Export summary report** - Generate statistics
5. **Exit** - Close application

### Sample Data Format
Create `your_data.csv`:
```csv
IndexNumber,FullName,Course,Score
ST001,John Doe,Computer Science,85
ST002,Jane Smith,Mathematics,92
```

## 🔧 Manual Database Configuration

If setup script doesn't work, manually edit `database.py`:

```python
self.config = {
    'host': 'localhost',        # Your PostgreSQL host
    'database': 'student_db',   # Your database name
    'user': 'your_username',    # Your PostgreSQL username
    'password': 'your_password',# Your PostgreSQL password
    'port': '5432'             # Your PostgreSQL port
}
```

## 🧪 Testing

Test individual components:

```bash
# Test database connection
python database.py

# Test utility functions
python utils.py

# Full system test
python setup.py
```

## 📊 Grade Scale
- **A**: 80-100 points
- **B**: 70-79 points  
- **C**: 60-69 points
- **D**: 50-59 points
- **F**: 0-49 points

## 🆘 Troubleshooting

### Common Issues:

**"Connection refused"**
- Start PostgreSQL service
- Check if database exists
- Verify port 5432 is open

**"Module not found"**
```bash
pip install psycopg2-binary
```

**"Permission denied"**
- Grant database permissions:
```sql
GRANT ALL PRIVILEGES ON DATABASE student_db TO your_user;
```

**"File not found"**
- Ensure all files are in same directory
- Check file permissions
- Use absolute paths if needed

## 📁 Project Files
```
student-result-management/
├── main.py           # 🚀 Start here
├── database.py       # 💾 Database operations
├── utils.py         # 🛠️ Utility functions
├── setup.py         # ⚙️ Configuration helper
├── sample_data.csv  # 📄 Test data
├── requirements.txt # 📦 Dependencies
└── README.md       # 📖 Full documentation
```

## ⚡ One-Line Commands

```bash
# Complete setup and run
pip install psycopg2-binary && python setup.py && python main.py

# Create sample data and run
python -c "from utils import create_sample_data_file; create_sample_data_file()" && python main.py
```

## 💡 Pro Tips

1. **Backup data**: Export reports before making changes
2. **Batch import**: Use CSV files for multiple students
3. **Check logs**: Read error messages carefully
4. **Test first**: Use sample data before real data
5. **Regular exports**: Generate reports periodically

## 🎯 Next Steps

After basic setup:
1. Import your real student data
2. Customize grading scale in `utils.py`
3. Modify report format in `ReportGenerator`
4. Add data validation rules
5. Implement additional features

---

**Need help?** Check the full README.md or run `python setup.py` for guided configuration.
