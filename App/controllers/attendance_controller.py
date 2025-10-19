from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from App.database import db
from App.models import Attendance, Shift, User


# ---------- helpers ----------

def _require_user(user_id: int) -> User:
    user = db.session.get(User, user_id)
    if not user:
        raise ValueError("User not found.")
    return user

def _require_shift(shift_id: int) -> Shift:
    shift = db.session.get(Shift, shift_id)
    if not shift:
        raise ValueError("Shift not found.")
    return shift

def _get_attendance(user_id: int, shift_id: int) -> Optional[Attendance]:
    return Attendance.query.filter_by(user_id=user_id, shift_id=shift_id).first()

def _require_attendance(user_id: int, shift_id: int) -> Attendance:
    att = _get_attendance(user_id, shift_id)
    if not att:
        raise ValueError("Attendance record not found for this user/shift.")
    return att


# ---------- CRUD / queries ----------

def ensure_attendance_record(user_id: int, shift_id: int, *, approved: Optional[bool] = None) -> Attendance:
    """
    Idempotently create (or update) the Attendance record for a user+shift.
    This is usually called when a shift is created or when a user first interacts with it.
    """
    _require_user(user_id)
    _require_shift(shift_id)

    att = _get_attendance(user_id, shift_id)
    if att:
        if approved is not None:
            att.approved = approved
            db.session.commit()
        return att

    att = Attendance(user_id=user_id, shift_id=shift_id, approved=bool(approved) if approved is not None else False)
    db.session.add(att)
    db.session.commit()
    return att

def get_attendance(attendance_id: int) -> Optional[Attendance]:
    return db.session.get(Attendance, attendance_id)

def get_attendance_for_user(user_id: int) -> List[Attendance]:
    _require_user(user_id)
    return Attendance.query.filter_by(user_id=user_id).all()

def get_attendance_for_shift(shift_id: int) -> List[Attendance]:
    _require_shift(shift_id)
    return Attendance.query.filter_by(shift_id=shift_id).all()

def delete_attendance(attendance_id: int) -> bool:
    att = get_attendance(attendance_id)
    if not att:
        return False
    db.session.delete(att)
    db.session.commit()
    return True


# ---------- clock actions ----------

def clock_in(user_id: int, shift_id: int, when: Optional[datetime] = None) -> Attendance:
    """
    Set time_in if not already set. Returns Attendance (idempotent).
    """
    when = when or datetime.now()
    _require_user(user_id)
    _require_shift(shift_id)

    att = ensure_attendance_record(user_id, shift_id)
    if att.time_in:        # idempotent: do nothing if already clocked in
        return att

    # Optional: guard against early/late windows here if you want business rules.
    att.time_in = when
    db.session.commit()
    return att

def clock_out(user_id: int, shift_id: int, when: Optional[datetime] = None) -> Attendance:
    """
    Set time_out if time_in exists and time_out not set. Returns Attendance.
    """
    when = when or datetime.now()
    _require_user(user_id)
    _require_shift(shift_id)

    att = _require_attendance(user_id, shift_id)
    if not att.time_in:
        raise ValueError("Cannot clock out before clocking in.")
    if att.time_out:       # idempotent: do nothing if already clocked out
        return att

    if when < att.time_in:
        raise ValueError("Clock-out time cannot be earlier than clock-in time.")

    att.time_out = when
    db.session.commit()
    return att


# ---------- approval workflow (optional but useful for reports) ----------

def approve_attendance(user_id: int, shift_id: int) -> Attendance:
    att = _require_attendance(user_id, shift_id)
    att.approved = True
    db.session.commit()
    return att

def unapprove_attendance(user_id: int, shift_id: int) -> Attendance:
    att = _require_attendance(user_id, shift_id)
    att.approved = False
    db.session.commit()
    return att


# ---------- JSON helpers (handy for views) ----------

def attendance_to_json(att: Attendance) -> dict:
    """
    Safe, small serializer for controllers/tests (views may call model.get_json()).
    """
    return {
        "id": att.id,
        "user_id": att.user_id,
        "shift_id": att.shift_id,
        "time_in": att.time_in.isoformat() if att.time_in else None,
        "time_out": att.time_out.isoformat() if att.time_out else None,
        "approved": bool(att.approved),
        "hours_worked": round(att.hours_worked(), 2) if hasattr(att, "hours_worked") else None,
    }
