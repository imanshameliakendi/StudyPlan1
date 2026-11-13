from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.admin import router as admin_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.availability import router as availability_router
from backend.api.routes.calendar import router as calendar_router
from backend.api.routes.courses import router as courses_router
from backend.api.routes.dashboard import router as dashboard_router
from backend.api.routes.planner import router as planner_router
from backend.api.routes.sessions import router as sessions_router
from backend.api.routes.uploads import router as uploads_router
from backend.config import settings
from backend.database import Base, ensure_database_ready, engine
from backend.services.bootstrap import ensure_admin_exists

app = FastAPI(title="StudyPlan", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(courses_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(calendar_router, prefix="/api")
app.include_router(availability_router, prefix="/api")
app.include_router(planner_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")

ensure_database_ready()
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
ensure_admin_exists()


@app.on_event("startup")
def startup_event():
    ensure_database_ready()
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    ensure_admin_exists()


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
