from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models import AvailabilityException, User, WeeklyAvailability
from backend.schemas import (
    AvailabilityExceptionCreate,
    AvailabilityExceptionOut,
    WeeklyAvailabilityCreate,
    WeeklyAvailabilityOut,
)
from backend.security import get_current_user, get_db

router = APIRouter(tags=["availability"])


@router.get("/availability", response_model=list[WeeklyAvailabilityOut])
def list_availability(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(WeeklyAvailability).filter(WeeklyAvailability.user_id == current_user.id).order_by(WeeklyAvailability.day_of_week).all()


@router.post("/availability", response_model=WeeklyAvailabilityOut)
def create_availability(payload: WeeklyAvailabilityCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = WeeklyAvailability(user_id=current_user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/availability/{item_id}")
def delete_availability(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(WeeklyAvailability).filter(WeeklyAvailability.id == item_id, WeeklyAvailability.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Availability record not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.get("/availability/exceptions", response_model=list[AvailabilityExceptionOut])
def list_exceptions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(AvailabilityException)
        .filter(AvailabilityException.user_id == current_user.id)
        .order_by(AvailabilityException.offline_date)
        .all()
    )


@router.post("/availability/exceptions", response_model=AvailabilityExceptionOut)
def create_exception(payload: AvailabilityExceptionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = AvailabilityException(user_id=current_user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/availability/exceptions/{exception_id}")
def delete_exception(exception_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(AvailabilityException).filter(
        AvailabilityException.id == exception_id,
        AvailabilityException.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Availability exception not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
