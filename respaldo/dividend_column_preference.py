# src/models/dividend_column_preference.py
from src.extensions import db

class DividendColumnPreference(db.Model):
    __tablename__ = 'dividend_column_preferences'
    id = db.Column(db.Integer, primary_key=True, default=1)
    columns_json = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'columns': self.columns_json,
        }