# src/models/filtered_stock_history.py

from src.extensions import db
from datetime import datetime, timezone

class FilteredStockHistory(db.Model):
    __tablename__ = 'filtered_stock_history'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    symbol = db.Column(db.String(50), nullable=False, index=True)
    
    price = db.Column(db.Float)
    previous_price = db.Column(db.Float)
    price_difference = db.Column(db.Float)
    percent_change = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'price': self.price,
            'previous_price': self.previous_price,
            'price_difference': self.price_difference,
            'percent_change': self.percent_change,
        }