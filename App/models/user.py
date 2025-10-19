from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username =  db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    isAdmin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<User id={self.id} username={self.username!r} admin={self.isAdmin}>"

    def __init__(self, username, password, isAdmin):
        self.username = username
        self.set_password(password)
        self.isAdmin = isAdmin

    def get_json(self):
        return{
            'id': self.id,
            'username': self.username,
            'isAdmin': self.isAdmin
        }

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def is_authenticated_admin(self):
        return self.isAdmin





#original code (move to models/shift.py)

class Shift(db.Model):
    __tablename__ = 'shifts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    work_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    role = db.Column(db.String(50))     
    location = db.Column(db.String(100))  

    user = db.relationship('User', backref=db.backref('shifts', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'work_date', 'start_time', 'end_time', name='uq_user_shift_window'),
    )

    def __repr__(self):
        return (f"<Shift id={self.id} user_id={self.user_id} "
                f"date={self.work_date} {self.start_time}-{self.end_time} "
                f"role={self.role!r} loc={self.location!r}>")
    
    def duration_hours(self):
        dt_start = datetime.combine(self.work_date, self.start_time)
        dt_end   = datetime.combine(self.work_date, self.end_time)
        return max((dt_end - dt_start).total_seconds() / 3600.0, 0)

    def get_json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'date': self.work_date.isoformat(),
            'start': self.start_time.strftime('%H:%M'),
            'end': self.end_time.strftime('%H:%M'),
            'role': self.role,
            'location': self.location
        }