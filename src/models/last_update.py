from src.extensions import db
from datetime import datetime, timezone

class LastUpdate(db.Model):
    __tablename__ = 'last_update'
    id = db.Column(db.Integer, primary_key=True, default=1)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp
        }