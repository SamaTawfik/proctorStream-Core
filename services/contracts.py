from typing import Any, Dict
from pydantic import BaseModel, Field


class EventV1(BaseModel):
    """
    Unified Data Contract (event.v1) as defined in the SRS specifications.
    """
    session_id: str = Field(..., description="Unique identifier for the exam session")
    ts_ms: int = Field(..., description="Timestamp in milliseconds")
    channel: str = Field(..., description="Channel name: presence, identity, attention, environment, audio")
    detector: str = Field(..., description="Name of the detector or AI model generating the event")
    event_type: str = Field(..., description="Event classification type, e.g., FACE_PRESENT, MULTI_FACE")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score bounded between 0.0 and 1.0")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Additional context data like bounding boxes or transcript")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess-12345",
                "ts_ms": 1700000000000,
                "channel": "presence",
                "detector": "yolov8_face",
                "event_type": "FACE_PRESENT",
                "confidence": 0.98,
                "payload": {"bbox": [100, 150, 200, 250]}
            }
        }