from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base




class Course(Base):
	"""
	SQLAlchemy model for the courses table.

	Represents a course in a class, associated with a teacher and class.

	Attributes:
		id (int): Primary key for the course.
		title (str): Course title (e.g., "Algebra").
		code (str): Course code (e.g., "MATH101").
		credit_hours (int): Number of credit hours.
		grading_type (str): Type of grading system (e.g., "default").
		class_id (int): ID of the associated class.
		teacher_id (int): ID of the assigned teacher.
		class_ (relationship): Relationship to the Class model.

	Notes:
		- Ensure indexes on class_id and teacher_id for performance.
		- Student profile images are included via class_.students in get_courses.
	"""
	__tablename__ = "courses"
	id = Column(Integer, primary_key=True)
	title = Column(String, nullable=False)
	code = Column(String, nullable=False)
	credit_hours = Column(Integer, nullable=False)
	grading_type = Column(String, nullable=False)
	class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
	teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

	# Relationships
	class_ = relationship("Class", back_populates="courses")
	teacher = relationship("User", back_populates="courses_as_teacher")
	grades = relationship("Grade", back_populates="course")

	def __repr__(self):
		return f"<Course(title={self.title}, code={self.code})>"