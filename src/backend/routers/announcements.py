"""
Announcements management endpoints

Public: GET /announcements -> list active announcements
Management (require teacher_username): POST/PUT/DELETE for create/update/delete
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from fastapi import Body
from ..database import (
    list_announcements,
    create_announcement,
    update_announcement,
    delete_announcement,
    get_announcement,
    teachers_collection,
)

from datetime import datetime

router = APIRouter(prefix="/announcements", tags=["announcements"])


def _require_teacher(teacher_username: Optional[str]):
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    return teacher


@router.get("", response_model=Dict[str, Any])
def get_public_announcements():
    """Return active (non-expired) announcements"""
    items = list_announcements(include_expired=False)
    return {item["id"]: item for item in items}


@router.post("", response_model=Dict[str, Any])
def create_new_announcement(message: str, expires_at: Optional[datetime] = None, start_date: Optional[datetime] = None, teacher_username: Optional[str] = Query(None)):
    """Create a new announcement (requires authentication)"""
    _require_teacher(teacher_username)
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    if not expires_at:
        raise HTTPException(status_code=400, detail="expires_at is required")

    ann_id = create_announcement(message=message, expires_at=expires_at, start_date=start_date)
    return {"id": ann_id}


@router.put("/{announcement_id}")
def update_existing_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None), payload: Dict[str, Any] = Body(...)):
    """Update an announcement (requires authentication). Accepts JSON body with optional fields: message, expires_at, start_date"""
    _require_teacher(teacher_username)
    message = payload.get("message")
    expires_at = payload.get("expires_at")
    start_date = payload.get("start_date")

    if not any([message is not None, expires_at is not None, start_date is not None]):
        raise HTTPException(status_code=400, detail="No fields to update")

    ok = update_announcement(announcement_id, message=message, expires_at=expires_at, start_date=start_date)
    if not ok:
        raise HTTPException(status_code=404, detail="Announcement not found or not modified")
    return {"ok": True}


@router.delete("/{announcement_id}")
def delete_existing_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None)):
    _require_teacher(teacher_username)
    ok = delete_announcement(announcement_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"ok": True}
