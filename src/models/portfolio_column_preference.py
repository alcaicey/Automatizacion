# src/models/portfolio_column_preference.py
from src.extensions import db

class PortfolioColumnPreference(db.Model):
    __tablename__ = 'portfolio_column_preferences'
    id = db.Column(db.Integer, primary_key=True, default=1)
    columns_json = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'columns': self.columns_json,
        }