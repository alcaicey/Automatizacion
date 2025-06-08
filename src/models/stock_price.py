from sqlalchemy import event, DDL

from . import db


class StockPrice(db.Model):
    __tablename__ = 'stock_prices'
    # Ensure each price record for a given symbol and timestamp is unique. This
    # also satisfies TimescaleDB's requirement for a constraint that includes
    # the time column.
    __table_args__ = ()

    symbol = db.Column(db.String(50), primary_key=True)
    timestamp = db.Column(db.DateTime, primary_key=True, nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    variation = db.Column(db.Float)

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'price': self.price,
            'variation': self.variation,
            'timestamp': (
                self.timestamp.isoformat() if self.timestamp else None
            ),
        }


@event.listens_for(StockPrice.__table__, 'after_create')
def create_timescale_hypertable(target, connection, **kw):
    if connection.dialect.name == "postgresql":
        connection.execute(DDL("CREATE EXTENSION IF NOT EXISTS timescaledb"))
        connection.execute(
            DDL(
                "SELECT create_hypertable('stock_prices', 'timestamp', "
                "if_not_exists => TRUE)"
            )
        )
