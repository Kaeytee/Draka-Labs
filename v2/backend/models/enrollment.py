from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from database.db import Base
from datetime import datetime


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(32), default="active")
    semester = Column(String(16), nullable=True)

    # Relationships
    student = relationship("User", back_populates="enrollments")
    class_ = relationship("Class", back_populates="enrollments")