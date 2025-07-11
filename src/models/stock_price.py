from sqlalchemy import event, DDL
from src.extensions import db
from datetime import datetime, timezone

class StockPrice(db.Model):
    __tablename__ = 'stock_prices'
    symbol = db.Column(db.String(50), primary_key=True)
    timestamp = db.Column(db.DateTime, primary_key=True, default=lambda: datetime.now(timezone.utc), index=True)
    price = db.Column(db.Float)
    variation = db.Column(db.Float)
    buy_price = db.Column(db.Float)
    sell_price = db.Column(db.Float)
    amount = db.Column(db.BigInteger)
    traded_units = db.Column(db.BigInteger)
    currency = db.Column(db.String(10))
    isin = db.Column(db.String(50))
    green_bond = db.Column(db.String(5))

    __table_args__ = (
        db.PrimaryKeyConstraint('symbol', 'timestamp'),
        {},
    )

    def to_dict(self):
        """
        Devuelve el objeto como un diccionario, usando los nombres de clave del JSON original
        y formateando el timestamp.
        """
        formatted_timestamp = self.timestamp.strftime('%d/%m/%Y %H:%M:%S') if self.timestamp else None

        return {
            'NEMO': self.symbol,
            'PRECIO_CIERRE': self.price,
            'VARIACION': self.variation,
            'PRECIO_COMPRA': self.buy_price,
            'PRECIO_VENTA': self.sell_price,
            'MONTO': self.amount,
            'UN_TRANSADAS': self.traded_units,
            'MONEDA': self.currency,
            'ISIN': self.isin,
            'BONO_VERDE': self.green_bond,
            'timestamp': formatted_timestamp
        }

@event.listens_for(StockPrice.__table__, 'after_create')
def create_timescale_hypertable(target, connection, **kw):
    if connection.dialect.name == "postgresql":
        try:
            # La extensión debe estar preinstalada en la base de datos.
            # Esta llamada asegura que está habilitada para la conexión actual.
            connection.execute(DDL("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
            # Convierte la tabla en una hypertable
            connection.execute(
                DDL("SELECT create_hypertable('stock_prices', 'timestamp', if_not_exists => TRUE);")
            )
        except Exception as e:
            # Esto puede fallar si el usuario de la DB no tiene permisos de superusuario
            # o si la extensión no está instalada. Lo registramos como una advertencia.
            print(f"ADVERTENCIA: No se pudo crear/configurar la hypertable de TimescaleDB. Error: {e}")