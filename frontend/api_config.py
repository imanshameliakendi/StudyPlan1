import os


LOCAL_BACKEND_URL = "http://localhost:8000"


def get_backend_url() -> str:
    return os.getenv("BACKEND_BASE_URL", LOCAL_BACKEND_URL).rstrip("/")
