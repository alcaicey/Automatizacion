# src/models/anomalous_event.py
from src.extensions import db
from datetime import datetime, timezone

class AnomalousEvent(db.Model):
    __tablename__ = 'anomalous_events'

    id = db.Column(db.Integer, primary_key=True)
    nemo = db.Column(db.String(20), nullable=False, index=True)
    event_date = db.Column(db.Date, nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False) # 'Volume Spike', 'Insider Purchase', 'Sentiment Shift', etc.
    description = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(100)) # 'Internal Volume Analysis', 'Simulated CMF Scraper', etc.
    price_change_pct = db.Column(db.Float, nullable=True) # % de cambio de precio post-evento
    analysis_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'nemo': self.nemo,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'event_type': self.event_type,
            'description': self.description,
            'source': self.source,
            'price_change_pct': self.price_change_pct,
            'analysis_timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
        }