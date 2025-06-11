from datetime import datetime
from . import db

class LogEntry(db.Model):
    __tablename__ = 'log_entries'
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)
    action = db.Column(db.String(50))
    stack = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'action': self.action,
            'stack': self.stack,
            'timestamp': self.timestamp.strftime('%d/%m/%Y %H:%M:%S') if self.timestamp else None,
        }
