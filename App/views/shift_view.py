from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date, time as dtime
from App.controllers import schedule_shift, get_roster
from App.models import Shift, User
from App.database import db

shift_views = Blueprint('shift_views', __name__, template_folder='../templates')


@shift_views.route('/shifts', methods=['GET'])
@login_required
def view_shifts():
    """Display all shifts for the current user or all users (if admin)."""
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query
    query = Shift.query
    
    # Filter by user if specified or if not admin
    if user_id:
        query = query.filter_by(user_id=user_id)
    elif hasattr(current_user, 'is_admin') and not current_user.is_admin:
        query = query.filter_by(user_id=current_user.id)
    
    # Filter by date range
    if start_date:
        query = query.filter(Shift.work_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Shift.work_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    shifts = query.order_by(Shift.work_date.desc(), Shift.start_time.desc()).all()
    users = User.query.all() if hasattr(current_user, 'is_admin') and current_user.is_admin else None
    
    return render_template('shifts.html', shifts=shifts, users=users)


@shift_views.route('/shifts/roster', methods=['GET'])
@login_required
def view_roster():
    """Display combined roster for all staff using the controller's get_roster function."""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Default to current week if not specified
    if not start_date_str or not end_date_str:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())  # Monday
        end_date = start_date + timedelta(days=6)  # Sunday
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # Use the controller's get_roster function
    roster = get_roster(start_date, end_date)
    
    return render_template('roster.html', roster=roster, start_date=start_date, end_date=end_date)


@shift_views.route('/shifts/create', methods=['GET', 'POST'])
@login_required
def create_shift():
    """Create a new shift."""
    if request.method == 'GET':
        users = User.query.all() if hasattr(current_user, 'is_admin') and current_user.is_admin else None
        return render_template('create_shift.html', users=users)
    
    # POST request
    try:
        user_id = request.form.get('user_id', type=int)
        
        # Only admins can create shifts for others
        if hasattr(current_user, 'is_admin') and not current_user.is_admin and user_id != current_user.id:
            flash('You can only create shifts for yourself.', 'error')
            return redirect(url_for('shift_views.create_shift'))
        
        work_date = datetime.strptime(request.form['work_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
        end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
        role = request.form.get('role')
        location = request.form.get('location')
        
        # Use the controller's schedule_shift function
        shift = schedule_shift(
            user_id=user_id or current_user.id,
            work_date=work_date,
            start=start_time,
            end=end_time,
            role=role,
            location=location
        )
        
        flash(f'Shift scheduled successfully for {work_date}', 'success')
        return redirect(url_for('shift_views.view_shifts'))
        
    except ValueError as e:
        flash(f'Invalid date or time format: {str(e)}', 'error')
        return redirect(url_for('shift_views.create_shift'))
    except Exception as e:
        flash(f'Error creating shift: {str(e)}', 'error')
        return redirect(url_for('shift_views.create_shift'))


@shift_views.route('/shifts/<int:shift_id>', methods=['GET'])
@login_required
def view_shift(shift_id):
    """View a specific shift."""
    shift = Shift.query.get_or_404(shift_id)
    
    # Check permissions
    if hasattr(current_user, 'is_admin') and not current_user.is_admin and shift.user_id != current_user.id:
        flash('You do not have permission to view this shift.', 'error')
        return redirect(url_for('shift_views.view_shifts'))
    
    return render_template('view_shift.html', shift=shift)


@shift_views.route('/shifts/<int:shift_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_shift(shift_id):
    """Edit an existing shift."""
    shift = Shift.query.get_or_404(shift_id)
    
    # Check permissions
    if hasattr(current_user, 'is_admin') and not current_user.is_admin and shift.user_id != current_user.id:
        flash('You do not have permission to edit this shift.', 'error')
        return redirect(url_for('shift_views.view_shifts'))
    
    if request.method == 'GET':
        return render_template('edit_shift.html', shift=shift)
    
    # POST request
    try:
        shift.work_date = datetime.strptime(request.form['work_date'], '%Y-%m-%d').date()
        shift.start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
        shift.end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
        shift.role = request.form.get('role')
        shift.location = request.form.get('location')
        
        db.session.commit()
        flash('Shift updated successfully', 'success')
        return redirect(url_for('shift_views.view_shift', shift_id=shift.id))
        
    except ValueError as e:
        flash(f'Invalid date or time format: {str(e)}', 'error')
        return redirect(url_for('shift_views.edit_shift', shift_id=shift_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating shift: {str(e)}', 'error')
        return redirect(url_for('shift_views.edit_shift', shift_id=shift_id))


@shift_views.route('/shifts/<int:shift_id>/delete', methods=['POST'])
@login_required
def delete_shift(shift_id):
    """Delete a shift."""
    shift = Shift.query.get_or_404(shift_id)
    
    # Check permissions
    if hasattr(current_user, 'is_admin') and not current_user.is_admin and shift.user_id != current_user.id:
        flash('You do not have permission to delete this shift.', 'error')
        return redirect(url_for('shift_views.view_shifts'))
    
    try:
        db.session.delete(shift)
        db.session.commit()
        flash('Shift deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting shift: {str(e)}', 'error')
    
    return redirect(url_for('shift_views.view_shifts'))


# API Routes for JSON responses
@shift_views.route('/api/shifts', methods=['GET'])
@login_required
def get_shifts_json():
    """Return shifts as JSON - similar to CLI roster command."""
    user_id = request.args.get('user_id', type=int)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if not start_date_str or not end_date_str:
        return jsonify({'error': 'start_date and end_date required'}), 400
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # Use controller's get_roster function
    roster = get_roster(start_date, end_date)
    
    # Filter by user if specified
    if user_id:
        user = User.query.get(user_id)
        if user:
            roster = [r for r in roster if r.get('username') == user.username]
    elif hasattr(current_user, 'is_admin') and not current_user.is_admin:
        roster = [r for r in roster if r.get('username') == current_user.username]
    
    return jsonify({'shifts': roster})


@shift_views.route('/api/shifts/create', methods=['POST'])
@login_required
def create_shift_json():
    """Create a shift via JSON API."""
    data = request.get_json()
    
    try:
        user_id = data.get('user_id', current_user.id)
        
        if hasattr(current_user, 'is_admin') and not current_user.is_admin and user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        work_date = datetime.strptime(data['work_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        # Use controller's schedule_shift function
        shift = schedule_shift(
            user_id=user_id,
            work_date=work_date,
            start=start_time,
            end=end_time,
            role=data.get('role'),
            location=data.get('location')
        )
        
        return jsonify(shift.get_json()), 201
        
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': f'Invalid date/time format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shift_views.route('/api/shifts/<int:shift_id>/update', methods=['POST'])
@login_required
def update_shift_json(shift_id):
    """Update a shift via JSON API."""
    shift = Shift.query.get_or_404(shift_id)
    
    if hasattr(current_user, 'is_admin') and not current_user.is_admin and shift.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    try:
        if 'work_date' in data:
            shift.work_date = datetime.strptime(data['work_date'], '%Y-%m-%d').date()
        if 'start_time' in data:
            shift.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        if 'end_time' in data:
            shift.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        if 'role' in data:
            shift.role = data['role']
        if 'location' in data:
            shift.location = data['location']
        
        db.session.commit()
        return jsonify(shift.get_json())
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid date/time format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@shift_views.route('/api/shifts/<int:shift_id>/delete', methods=['POST'])
@login_required
def delete_shift_json(shift_id):
    """Delete a shift via JSON API."""
    shift = Shift.query.get_or_404(shift_id)
    
    if hasattr(current_user, 'is_admin') and not current_user.is_admin and shift.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        db.session.delete(shift)
        db.session.commit()
        return jsonify({'message': 'Shift deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500