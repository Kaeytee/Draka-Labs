from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, index=True)
    description = Column(String(256), nullable=True)
    academic_year = Column(String(16), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    class_teacher_id = Column(Integer, ForeignKey("user.id"), nullable=True)

    # Relationships
    school = relationship("School", back_populates="classes")
    class_teacher = relationship("User", back_populates="classes_as_teacher", foreign_keys=[class_teacher_id])
    students = relationship("User", back_populates="class_enrolled", foreign_keys="User.class_id")
    courses = relationship("Course", back_populates="class_")

    def __repr__(self):
        return f"<Class(name={self.name}, year={self.academic_year})>"