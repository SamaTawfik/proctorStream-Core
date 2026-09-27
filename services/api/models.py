from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from services.api.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="student")  # student / proctor / admin
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("ExamSession", back_populates="student")

class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending / active / completed
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="sessions")