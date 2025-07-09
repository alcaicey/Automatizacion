# src/models/kpi_selection.py
from src.extensions import db

class KpiSelection(db.Model):
    __tablename__ = 'kpi_selections'
    nemo = db.Column(db.String(20), primary_key=True)

    def to_dict(self):
        return {'nemo': self.nemo}