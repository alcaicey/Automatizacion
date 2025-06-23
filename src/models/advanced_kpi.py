# src/models/advanced_kpi.py
from src.extensions import db
from datetime import datetime, timezone

class AdvancedKPI(db.Model):
    __tablename__ = 'advanced_kpis'

    nemo = db.Column(db.String(20), primary_key=True)
    roe = db.Column(db.Float, nullable=True)
    debt_to_equity = db.Column(db.Float, nullable=True)
    beta = db.Column(db.Float, nullable=True)
    analyst_recommendation = db.Column(db.String(50), nullable=True)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'nemo': self.nemo,
            'roe': self.roe,
            'debt_to_equity': self.debt_to_equity,
            'beta': self.beta,
            'analyst_recommendation': self.analyst_recommendation,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }