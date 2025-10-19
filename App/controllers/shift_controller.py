from datetime import datetime, date, timedelta, time as dtime

from App.models import Shift, Attendance
from App.database import db 


def schedule_shift(user_id: int, work_date: date, start: dtime, end: dtime, role=None, location=None):
    existing = Shift.query.filter_by(
        user_id=user_id,
        work_date=work_date,
        start_time=start,
        end_time=end
    ).first()
    if existing:
        if role is not None:
            existing.role = role
        if location is not None:
            existing.location = location
        db.session.commit()
        return existing

    shift = Shift(
        user_id=user_id,
        work_date=work_date,
        start_time=start,
        end_time=end,
        role=role,
        location=location
    )
    db.session.add(shift)
    db.session.commit()

    att = Attendance.query.filter_by(shift_id=shift.id, user_id=user_id).first()
    if not att:
        db.session.add(Attendance(shift_id=shift.id, user_id=user_id))
        db.session.commit()

    return shift