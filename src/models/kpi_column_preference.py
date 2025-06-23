# src/models/kpi_column_preference.py
from src.extensions import db

class KpiColumnPreference(db.Model):
    __tablename__ = 'kpi_column_preferences'
    id = db.Column(db.Integer, primary_key=True, default=1)
    columns_json = db.Column(db.Text, nullable=False)