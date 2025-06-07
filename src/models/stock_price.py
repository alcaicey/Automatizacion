from datetime import datetime
from sqlalchemy import event, DDL

from . import db

class StockPrice(db.Model):
    __tablename__ = 'stock_prices'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    variation = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'price': self.price,
            'variation': self.variation,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


@event.listens_for(StockPrice.__table__, 'after_create')
def create_timescale_hypertable(target, connection, **kw):
    if connection.dialect.name == "postgresql":
        connection.execute(DDL("CREATE EXTENSION IF NOT EXISTS timescaledb"))
        connection.execute(
            DDL(
                "SELECT create_hypertable('stock_prices', 'timestamp', if_not_exists => TRUE)"
            )
        )
