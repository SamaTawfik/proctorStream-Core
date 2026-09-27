import os
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from services.api.database import get_db
import services.api.models as models

app = FastAPI(title="ProctorStream API", version="1.0.0")

# --- Schemas (Pydantic models للتحقق من البيانات) ---

class UserCreate(BaseModel):
    email: str
    full_name: str
    role: str = "student"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True

class ExamSessionCreate(BaseModel):
    student_id: int
    title: str

class ExamSessionResponse(BaseModel):
    id: int
    student_id: int
    title: str
    status: str

    class Config:
        from_attributes = True

# --- Endpoints ---

@app.get("/")
def root():
    return {"message": "ProctorStream API is running"}

# 1. إنشاء مستخدم جديد
@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = models.User(
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 2. جلب جميع المستخدمين
@app.get("/users/", response_model=List[UserResponse])
def read_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

# 3. إنشاء جلسة امتحان
@app.post("/sessions/", response_model=ExamSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session: ExamSessionCreate, db: Session = Depends(get_db)):
    student = db.query(models.User).filter(models.User.id == session.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    new_session = models.ExamSession(
        student_id=session.student_id,
        title=session.title
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session