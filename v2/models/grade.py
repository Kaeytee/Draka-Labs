from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.db import Base
from datetime import datetime

class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    graded_by = Column(Integer, ForeignKey("user.id"), nullable=False)  # Teacher who graded

    # Relationships
    student = relationship("User", foreign_keys=[student_id], back_populates="grades_received")
    course = relationship("Course", back_populates="grades")
    grader = relationship("User", foreign_keys=[graded_by], back_populates="grades_given")

    def __repr__(self):
        return f"<Grade(student_id={self.student_id}, course_id={self.course_id}, value={self.value})>"