import os
import asyncio
import redis.asyncio as aioredis
import numpy as np
import cv2

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

async def process_frame(frame_bytes: bytes):
    """
    Decodes raw frame bytes into an OpenCV image and checks frame dimensions.
    """
    # Convert raw bytes to numpy array
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        print("Failed to decode frame")
        return

    height, width, channels = frame.shape
    print(f"[AI Worker] Frame received & decoded: Resolution {width}x{height}")
    
    # Here AI Models (MediaPipe / OpenCV / Face Detection) will be added next.

async def start_worker(session_id: int):
    """
    Listens to Redis Pub/Sub channel for a specific exam session.
    """
    redis_client = aioredis.from_url(REDIS_URL)
    pubsub = redis_client.pubsub()
    channel_name = f"session_stream:{session_id}"

    await pubsub.subscribe(channel_name)
    print(f"[*] AI Worker listening on channel: {channel_name}...")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                frame_data = message["data"]
                await process_frame(frame_data)
    except Exception as e:
        print(f"Error in worker: {e}")
    finally:
        await pubsub.unsubscribe(channel_name)
        await redis_client.close()

if __name__ == "__main__":
    # Test worker for session_id = 1
    asyncio.run(start_worker(session_id=1))