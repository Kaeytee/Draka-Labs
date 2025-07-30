from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.db import Base
from datetime import datetime


class Enrollment(Base):
	__tabelname__ = "enrollment"

	id= Column(Integer, primary_key=True, index=True)
	student_id= Column(Integer, ForeignKey("user.id"), nullable=False)
	class_id=Column(Integer, ForeignKey("class.id"), nullable=False)
	enrolled_at=Column(DateTime, default=datetime.utcnow)


	##Relationship
	student= relationship("User", back_populates="enrollments")
	class_ = relationship("Class", back_populates="enrollments")