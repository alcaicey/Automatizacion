# src/models/portfolio.py

from src.extensions import db

class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), nullable=False, index=True)
    quantity = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)

    def __init__(self, symbol, quantity, purchase_price):
        self.symbol = symbol
        self.quantity = quantity
        self.purchase_price = purchase_price

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'purchase_price': self.purchase_price,
        }