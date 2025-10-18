# App/api.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, datetime, time as dtime
from App.controllers import (
    schedule_shift, schedule_week, get_roster,
    clock_in, clock_out, weekly_report
)
from App.controllers.user import get_user  

api = Blueprint('api', __name__, url_prefix='/api')

def parse_date(s): return date.fromisoformat(s)
def parse_datetime(s): return datetime.fromisoformat(s)


def is_admin():
    """Check if current JWT user is admin."""
    user_id = get_jwt_identity()
    user = get_user(user_id)
    return user.isAdmin if user else False


# --- Admin: create one shift ---
@api.route('/admin/shifts', methods=['POST'])
@jwt_required() 
def api_create_shift():
    if not is_admin():
        return jsonify({"message": "Admin Access Required"}), 403
    data = request.get_json() or {}
    shift = schedule_shift(
        user_id=int(data['user_id']),
        work_date=parse_date(data['date']),
        start=_to_time(data['start']),
        end=_to_time(data['end']),
        role=data.get('role'),
        location=data.get('location'),
    )
    return jsonify(shift.get_json()), 201

# --- Admin: create a week's schedule for a user ---
@api.route('/admin/shifts/bulk', methods=['POST'])
@jwt_required()
def api_create_week():
    if not is_admin():
        return jsonify({"messsage": "Admin Access Required"}), 403

    data = request.get_json() or {}
    created = schedule_week(
        user_id=int(data['user_id']),
        week_start=parse_date(data['week_start']),
        daily_windows=data['daily_windows'],
        role=data.get('role'),
        location=data.get('location'),
    )
    return jsonify([s.get_json() for s in created]), 201

# --- Staff: combined roster ---
@api.route('/roster', methods=['GET'])
@jwt_required() 
def api_roster():
    start = parse_date(request.args.get('start'))
    end = parse_date(request.args.get('end'))
    return jsonify(get_roster(start, end)), 200

# --- Staff: time in/out ---
@api.route('/attendance/clock-in', methods=['POST'])
@jwt_required() 
def api_clock_in():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    if int(data['user_id']) != user_id:
        return jsonify({"message": "Cannot clock in for another user"}), 403
    att = clock_in(user_id, int(data['shift_id']))
    return jsonify(att.get_json()), 200

@api.route('/attendance/clock-out', methods=['POST'])
@jwt_required() 
def api_clock_out():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    if int(data['user_id']) != user_id:
        return jsonify({"message": "Cannot clock out for another user"}), 403
    att = clock_out(user_id, int(data['shift_id']))
    return jsonify(att.get_json()), 200

# --- Admin: weekly report ---
@api.route('/admin/reports/weekly', methods=['GET'])
@jwt_required() 
def api_weekly_report():
    if not is_admin():
        return jsonify({"message": "Admin access required"}), 403
    week_start = parse_date(request.args.get('week_start'))
    return jsonify(weekly_report(week_start)), 200

# helpers
def _to_time(s: str) -> dtime:
    return dtime.fromisoformat(s)
