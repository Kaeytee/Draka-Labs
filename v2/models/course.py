from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class Course(Base):
	__tablename__ = "courses"

	id = Column(Integer, primary_key=True, index=True)
	title = Column(String(128), nullable=False)
	code = Column(String(32), unique=True, nullable=False)
	credit_hours = Column(Integer, nullable=False)
	class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
	teacher_id = Column(Integer, ForeignKey("user.id"), nullable=False)


	# Relationships

	class_ = relationship("Class", back_populates="courses")
	teacher = relationship("User", back_populates="courses_as_teacher")

	def __repr__(self):
		return f"<Course(title={self.title}, code={self.code})>"