import re
from datetime import datetime, time
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}$")


def _validate_email(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("Email must be a string")
    normalized = value.strip().lower()
    if not _EMAIL_RE.fullmatch(normalized):
        raise ValueError("Invalid email address")
    return normalized


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    created_at: datetime


class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    importance: int = Field(default=1, ge=1, le=10)
    exam_date: Optional[datetime] = None
    description: Optional[str] = None
    total_workload_hours: int = Field(default=0, ge=0)


class CourseUpdate(CourseCreate):
    pass


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    importance: int
    exam_date: Optional[datetime]
    description: Optional[str]
    total_workload_hours: int
    is_archived: bool
    file_name: Optional[str]
    file_type: Optional[str]


class ChapterCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    workload_hours: int = Field(default=0, ge=0)
    study_minutes: int = Field(default=0, ge=0)
    display_order: int = Field(default=0, ge=0)
    parent_id: Optional[int] = None


class ChapterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    parent_id: Optional[int]
    title: str
    description: Optional[str]
    workload_hours: int
    study_minutes: int
    display_order: int
    completed_hours: int


class WeeklyAvailabilityCreate(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: str
    end_time: str

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        try:
            return time.fromisoformat(value).strftime("%H:%M")
        except (TypeError, ValueError) as exc:
            raise ValueError("Time must use HH:MM format") from exc

    @model_validator(mode="after")
    def validate_range(self) -> "WeeklyAvailabilityCreate":
        if time.fromisoformat(self.end_time) <= time.fromisoformat(self.start_time):
            raise ValueError("End time must be later than start time")
        return self


class WeeklyAvailabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    day_of_week: int
    start_time: str
    end_time: str


class AvailabilityExceptionCreate(BaseModel):
    offline_date: datetime
    start_time: str
    end_time: str
    reason: Optional[str] = None

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        try:
            return time.fromisoformat(value).strftime("%H:%M")
        except (TypeError, ValueError) as exc:
            raise ValueError("Time must use HH:MM format") from exc

    @model_validator(mode="after")
    def validate_range(self) -> "AvailabilityExceptionCreate":
        if time.fromisoformat(self.end_time) <= time.fromisoformat(self.start_time):
            raise ValueError("End time must be later than start time")
        return self


class AvailabilityExceptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    offline_date: datetime
    start_time: str
    end_time: str
    reason: Optional[str]


class PlanSession(BaseModel):
    course_id: int
    chapter_id: Optional[int]
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    status: str = "planned"


class PlanResponse(BaseModel):
    sessions: List[PlanSession]
    warnings: List[str] = []
    status: str = "ok"


class StudySessionOut(BaseModel):
    id: int
    course_id: int
    course_name: str
    chapter_id: Optional[int]
    start_time: datetime
    end_time: datetime
    status: str
    completion_note: Optional[str]
    completed_at: Optional[datetime]


class SessionComplete(BaseModel):
    completion_note: Optional[str] = Field(default=None, max_length=2000)


class AdminUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    created_at: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    detail: Optional[str]
    created_at: datetime
