
from sqlalchemy import Column, Integer, Text, String, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base
from models.user import UserRole



class School(Base):
	__tablename__ = "schools"

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String(128), unique=True, nullable=False)
	initials = Column(String(16), nullable=False, index=True)
	grading_system = Column(Text, nullable=False)  # Store as JSON string
	phone = Column(String(32), nullable=False)
	email = Column(String(256), nullable=True)
	address = Column(String(256), nullable=True)
	admin_id = Column(Integer, ForeignKey("user.id"), nullable=False, unique=True)

	# Relationships
	admin = relationship("User", back_populates="admin_of_school", uselist=False, foreign_keys=[admin_id])
	classes = relationship("Class", back_populates="school")
	# Use string-based expressions for UserRole to avoid NameError during model initialization
	teachers = relationship("User", back_populates="school", primaryjoin="and_(School.id==User.school_id, User.role=='teacher')")
	students = relationship("User", back_populates="school", primaryjoin="and_(School.id==User.school_id, User.role=='student')")

	def __repr__(self):
		return f"<School(name={self.name}, initials={self.initials})>"

	def update_grading_system(self, new_grading_system_json):
		"""
		Update the grading system for this school.
		"""
		self.grading_system = new_grading_system_json