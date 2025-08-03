from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from models.grade import Grade
from database.db import Base
import enum

class Gender(enum.Enum):
    male = "Male"
    female = "Female"
    other = "Other"

class UserRole(enum.Enum):
    superuser = "superuser"  # Application owner
    admin = "admin"          # School admin
    staff = "staff"          # Teacher
    student = "student"      # Student

class UserStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"

class User(Base):
    __tablename__ = "users"  # Changed to plural for consistency with SQL conventions

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(256), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False, index=True)
    gender = Column(Enum(Gender), nullable=False)
    date_of_birth = Column(Date, nullable=False)  # Changed to Date for proper handling
    address = Column(String(256), nullable=True)
    phone = Column(String(32), unique=True, nullable=True)  # Added unique constraint
    status = Column(Enum(UserStatus), default=UserStatus.active, nullable=False)
    admission_year = Column(Integer, nullable=True)  # Changed to Integer for year
    graduation_year = Column(Integer, nullable=True)  # Changed to Integer for year
    profile_image = Column(String(256), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)

    __table_args__ = (
        # Enforce username uniqueness per school
        UniqueConstraint('username', 'school_id', name='uq_username_school'),
    )
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True, index=True)

    # Relationships
    # Admin manages one school (one-to-one, nullable for flexibility)
    admin_of_school = relationship(
        "School",
        back_populates="admin",
        uselist=False,
        primaryjoin="User.id==School.admin_id"
    )
    
    # Teachers or students belong to one school (one-to-many)
    # Use the correct back_populates: 'teachers' or 'students' in School, or remove if not needed
    school = relationship("School", foreign_keys=[school_id])
    
    # Students enrolled in classes via Enrollment model
    enrollments = relationship("Enrollment", back_populates="student")
    
    # Students enrolled in one class directly
    class_enrolled = relationship("Class", back_populates="students", foreign_keys=[class_id])
    
    # Teachers assigned to courses
    courses_as_teacher = relationship("Course", back_populates="teacher", foreign_keys="Course.teacher_id")
    
    # Grades received by students
    grades_received = relationship("Grade", foreign_keys="Grade.student_id", back_populates="student")
    # Grades given by teachers
    grades_given = relationship("Grade", foreign_keys="Grade.graded_by", back_populates="grader")

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"