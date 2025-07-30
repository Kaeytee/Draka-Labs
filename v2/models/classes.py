from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base
from models.user import User

class Class(Base):
    __tablename__ = "classes"  # Use plural to avoid reserved keyword issues

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, index=True)
    description = Column(String(256), nullable=True)
    academic_year = Column(String(16), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    # --- Relationships ---

    # Link to the owning school
    school = relationship("School", back_populates="classes")

    # All students enrolled in this class
    # foreign_keys must be a list of columns, not a string
    students = relationship(
        "User",
        back_populates="class_enrolled",
        foreign_keys=[User.class_id]
    )

    # All courses attached to this class
    courses = relationship("Course", back_populates="class_")

    # All enrollment records for this class
    enrollments = relationship("Enrollment", back_populates="class_")

    def __repr__(self):
        return f"<Class(name={self.name}, year={self.academic_year})>"

# --- IMPORTANT ---
# In related models, ensure the following:
# - In School: classes = relationship("Class", back_populates="school")
# - In User: class_enrolled = relationship("Class", back_populates="students", foreign_keys=[User.class_id])
# - In Course: class_ = relationship("Class", back_populates="courses")
# - In Enrollment: class_ = relationship("Class", back_populates="enrollments")