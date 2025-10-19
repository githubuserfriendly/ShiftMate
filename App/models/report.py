from App.database import db
from datetime import datetime

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_shifts = db.Column(db.Integer, nullable=False, default=0)
    total_hours = db.Column(db.Float, nullable=False, default=0.0)
    attendance_rate = db.Column(db.Float, nullable=False, default=0.0)  # percentage
    overtime_hours = db.Column(db.Float, nullable=False, default=0.0)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Optional: who generated it (admin user)
    generated_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"<Report {self.start_date} - {self.end_date}>"