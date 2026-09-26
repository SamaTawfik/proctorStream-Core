import os
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ProctorStream Ingestion API",
    version="1.0.0",
    description="API Gateway for receiving student media streams and monitoring events."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary directory to store received chunks before pipeline processing
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "service": "proctorstream-api",
        "version": "1.0.0"
    }


@app.post("/api/v1/stream/upload", status_code=status.HTTP_201_CREATED)
async def upload_video_chunk(
    session_id: str = Form(...),
    chunk_index: int = Form(...),
    file: UploadFile = File(...)
):
    """
    Receives short video chunks (e.g. 5-second WebM files) from the proctoring frontend.
    """
    try:
        # Generate clean local filename
        filename = f"{session_id}_chunk_{chunk_index}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save chunk to disk
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return {
            "status": "success",
            "message": "Chunk uploaded successfully",
            "session_id": session_id,
            "chunk_index": chunk_index,
            "bytes_received": len(content)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process video chunk: {str(e)}"
        )