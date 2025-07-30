from sqlalchemy import Column, Integer, String, Enum , ForeignKey
from database.db import Base
from sqlalchemy.orm import relationship
import enum 
class Gender(enum.Enum):
    male = "Male"
    female = "Female"
    other = "Other"
class UserRole(enum.Enum):
	student="student"
	staff="staff"
	admin="admin"
	


class User(Base):
	__tablename__="user"

	id=Column(Integer, primary_key=True, index=True)
	username=Column(String, unique=True, index=True)
	full_name=Column(String, nullable=False)
	hashed_password=Column(String, nullable=False)
	email=Column(String, unique=True, index=True)
	role=Column(Enum(UserRole), nullable=False)
	gender = Column(Enum(Gender), nullable=False)
#Relationships


   # Each user (if admin) is admin of one school
	admin_of_school = relationship("School", back_populates="admin", uselist=False, foreign_keys='School.admin_id')

    # Each user (teacher or student) belongs to one school
	school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
	school = relationship("School", back_populates="teachers", foreign_keys=[school_id])
	enrollments = relationship("Enrollment", back_populates="student")
	#classes relationships 
	class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
	class_enrolled = relationship("Class", back_populates="students", foreign_keys=[class_id])
	
	#courses relationship
	courses_as_teacher = relationship("Course", back_populates="teacher", foreign_keys='Course.teacher_id')
	
	#Grade
	grades_received = relationship("Grade", foreign_keys="[Grade.student_id]", back_populates="student")
	grades_given = relationship("Grade", foreign_keys="[Grade.graded_by]", back_populates="grader")
	
	
	
	def __repr__(self):
		return f"<User(username={self.username}, role={self.role})>"