from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ProctorStream Ingestion API",
    version="1.0.0",
    description="API Gateway for receiving student media streams and monitoring events."
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify API server readiness.
    """
    return {
        "status": "healthy",
        "service": "proctorstream-api",
        "version": "1.0.0"
    }