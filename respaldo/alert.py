from .user import User
from src.extensions import db
from datetime import datetime

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), nullable=False, index=True)
    target_price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(10), nullable=False) # "above" or "below"
    status = db.Column(db.String(20), default='active', nullable=False, index=True) # active, triggered, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    triggered_at = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Opcional por ahora

    user = db.relationship('User', backref=db.backref('alerts', lazy=True))

    def __init__(self, symbol, target_price, condition, user_id=None):
        self.symbol = symbol
        self.target_price = target_price
        self.condition = condition
        self.user_id = user_id

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'target_price': self.target_price,
            'condition': self.condition,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'user_id': self.user_id
        }