import os
import redis.asyncio as aioredis
from typing import List
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    File,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from services.api.database import get_db
import services.api.models as models
from services.storage.minio_client import upload_file_bytes

app = FastAPI(title="ProctorStream API", version="1.0.0")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


# --- Schemas (Pydantic models for request validation) ---

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


# --- HTTP Endpoints ---

@app.get("/")
def root():
    return {"message": "ProctorStream API is running"}


# 1. Create new user
@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# 2. Get all users
@app.get("/users/", response_model=List[UserResponse])
def read_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


# 3. Create exam session
@app.post("/sessions/", response_model=ExamSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session: ExamSessionCreate, db: Session = Depends(get_db)):
    student = db.query(models.User).filter(models.User.id == session.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    new_session = models.ExamSession(
        student_id=session.student_id,
        title=session.title,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


# 4. Upload exam video chunk to MinIO
@app.post("/sessions/{session_id}/upload-video")
def upload_session_video(session_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    session = db.query(models.ExamSession).filter(models.ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")

    video_bytes = file.file.read()
    object_name = f"session_{session_id}/{file.filename}"

    try:
        file_url = upload_file_bytes(object_name, video_bytes, content_type=file.content_type or "video/mp4")
        return {
            "status": "success",
            "session_id": session_id,
            "filename": file.filename,
            "storage_url": file_url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to MinIO: {str(e)}")


# --- WebSocket Streaming Endpoint ---

@app.websocket("/ws/stream/{session_id}")
async def video_stream(websocket: WebSocket, session_id: int):
    """
    Receives video frames via WebSocket and publishes them to Redis channel.
    """
    await websocket.accept()
    print(f"Client connected to session stream: {session_id}")
    
    # Connect to Redis
    try:
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=False)
    except Exception as err:
        print(f"Failed to connect to Redis: {err}")
        await websocket.close(code=1011)
        return

    try:
        while True:
            data = await websocket.receive_bytes()

            # Publish frame bytes directly to Redis channel for this session
            channel_name = f"session_stream:{session_id}"
            await redis_client.publish(channel_name, data)

            await websocket.send_json({
                "status": "published_to_redis",
                "session_id": session_id,
                "bytes_received": len(data),
            })

    except WebSocketDisconnect:
        print(f"Client disconnected from session stream: {session_id}")
    except Exception as e:
        print(f"WebSocket error in session {session_id}: {e}")
    finally:
        await redis_client.close()