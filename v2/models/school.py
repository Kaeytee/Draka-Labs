from sqlalchemy import Column, Integer,Text, String, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class school(Base):
	__tablename__ = "schools"

	id= Column(Integer, primary_key=True, index=True)
	name=Column(String(128),unique=True, nullable=False)
	initials= Column(String(16), nullabale=False, index=True)
	grading_system= Column(Text, nullable=False)
	phone= Column(String(32), nullable=False)
	email=Column(String(256), nullable=True)
	address= Column(String(256), nullable=True)



##Relationships
	# admin = relationship("User", back_populates="school", uselist=False, foreign_keys="User.school_id")
	# teachers = relationship("User", back_populates="school", foreign_keys="User.school_id")
	# students = relationship("User", back_populates="school", foreign_keys="User.school_id")
	
	# def __repr__(self):
	# 	return f"<School(name={self.name}, initials={self.initials})>"
	# def __str__(self):
	# 	return f"{self.name} ({self.initials})"

    # One school has one admin (User with role='admin')
	admin_id= Column(Integer, ForeignKey("user.id"), nullable=False)
	admin = relationship("User", back_populates="school", uselist=False, foreign_keys=[admin_id])

	classes = relationship("Class", back_populates="school")
	#One School has many teachers (Users with role="teacher")
	teachers= relationship("User", back_populates="school", primaryjoin="and_(School.id==User.school_id, User.role==UserRole.teacher)")

	#One School has many students (Users with role="student")
	students= relationship("User", back_populates="school", primaryjoin="and_(School.id==User.school_id, User.role==UserRole.student)")


##more relationship for classes and course 

	def __repr__(self):
		return f"<School(name={self.name}, initials={self.initials})>"

	def __str__(self):
		return f"{self.name} ({self.initials})"