import os
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "proctor-videos"

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def init_minio():
    """إنشاء الـ Bucket تلقائياً لو مش موجود"""
    try:
        if not client.bucket_exists(BUCKET_NAME):
            client.make_bucket(BUCKET_NAME)
            print(f"Bucket '{BUCKET_NAME}' created successfully.")
    except Exception as e:
        print(f"Error initializing MinIO: {e}")

def upload_file_bytes(object_name: str, data: bytes, content_type: str = "video/mp4"):
    """رفع الملفات كمصفوفة بايتبس إلى MinIO"""
    import io
    init_minio()
    client.put_object(
        BUCKET_NAME,
        object_name,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type
    )
    return f"{MINIO_ENDPOINT}/{BUCKET_NAME}/{object_name}"