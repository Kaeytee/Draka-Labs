from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base
from models.user import User
from models.school import School
from models.course import Course
from models.enrollment import Enrollment

class Class(Base):
    """
    SQLAlchemy model for the classes table.

    Represents a class in a school, with optional relationships to enrolled students,
    school, courses, and enrollments.

    Attributes:
        id (int): Primary key for the class.
        name (str): Name of the class (e.g., "Math 101").
        school_id (int): ID of the school the class belongs to.
        description (str): Optional description of the class (max 256 characters).
        academic_year (str): Academic year (e.g., "2024-2025").
        school (relationship): Relationship to the School model.
        students (relationship): Students enrolled via User.class_id.
        courses (relationship): Courses associated with the class.
        enrollments (relationship): Enrollments linking students to the class.

    Notes:
        - Uses User.class_id for direct student enrollment (one-to-many).
        - Uses Enrollment table for additional enrollment management (many-to-many).
        - Ensure indexes on school_id and class_id for performance.
        - Profile images are included in student data via get_classes.
    """
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    description = Column(String(256), nullable=True)
    academic_year = Column(String(16), nullable=False)
    level = Column(String(16), nullable=True)  # e.g., 100, 200, 300, 400
    department = Column(String(128), nullable=True)

    school = relationship("School", back_populates="classes")
    students = relationship(
        "User",
        back_populates="class_enrolled",
        foreign_keys=[User.class_id]
    )
    courses = relationship("Course", back_populates="class_")
    enrollments = relationship("Enrollment", back_populates="class_")

    def __repr__(self):
        return f"<Class(name={self.name}, year={self.academic_year})>"