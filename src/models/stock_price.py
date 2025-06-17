from sqlalchemy import event, DDL
from src.extensions import db
from datetime import datetime

class StockPrice(db.Model):
    __tablename__ = 'stock_prices'
    # Claves primarias compuestas
    symbol = db.Column(db.String(50), primary_key=True)
    timestamp = db.Column(db.DateTime, primary_key=True, default=datetime.utcnow, index=True)

    # Columnas de datos principales (traducidas de JSON)
    price = db.Column(db.Float) # PRECIO_CIERRE
    variation = db.Column(db.Float) # VARIACION
    
    # --- INICIO DE LA CORRECCIÓN: Añadir todas las columnas del JSON ---
    buy_price = db.Column(db.Float) # PRECIO_COMPRA
    sell_price = db.Column(db.Float) # PRECIO_VENTA
    amount = db.Column(db.BigInteger) # MONTO
    traded_units = db.Column(db.BigInteger) # UN_TRANSADAS
    currency = db.Column(db.String(10)) # MONEDA
    isin = db.Column(db.String(50)) # ISIN
    green_bond = db.Column(db.String(5)) # BONO_VERDE
    # --- FIN DE LA CORRECCIÓN ---

    __table_args__ = (
        db.PrimaryKeyConstraint('symbol', 'timestamp'),
        {},
    )

    def to_dict(self):
        """
        Devuelve el objeto como un diccionario, usando los nombres de clave del JSON original.
        """
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
            # El timestamp no está en el JSON original por fila, pero lo añadimos para consistencia
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

@event.listens_for(StockPrice.__table__, 'after_create')
def create_timescale_hypertable(target, connection, **kw):
    if connection.dialect.name == "postgresql":
        connection.execute(DDL("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
        connection.execute(
            DDL("SELECT create_hypertable('stock_prices', 'timestamp', if_not_exists => TRUE);")
        )