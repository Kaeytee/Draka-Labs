from sqlalchemy import Column, Integer, String, DateTime, Text
from database.db import Base
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # Can be null for system actions
    action = Column(String(128), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AuditLog(user_id={self.user_id}, action={self.action}, timestamp={self.timestamp})>"
