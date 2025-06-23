# src/models/stock_closing.py
from src.extensions import db
from datetime import date

class StockClosing(db.Model):
    __tablename__ = 'stock_closings'

    # Clave primaria compuesta para asegurar un registro por día por nemo
    date = db.Column(db.Date, primary_key=True)
    nemo = db.Column(db.String(20), primary_key=True)

    # Resto de los campos
    previous_day_amount = db.Column(db.Float)
    previous_day_trades = db.Column(db.Integer)
    previous_day_close_price = db.Column(db.Float)
    belongs_to_igpa = db.Column(db.Boolean)
    belongs_to_ipsa = db.Column(db.Boolean)
    weight_igpa = db.Column(db.Float)
    weight_ipsa = db.Column(db.Float)
    price_to_earnings_ratio = db.Column(db.Float)
    current_yield = db.Column(db.Float)
    previous_day_traded_units = db.Column(db.BigInteger)
    
    __table_args__ = (
        db.PrimaryKeyConstraint('date', 'nemo'),
        {},
    )

    def to_dict(self):
        """Convierte el objeto a un diccionario, manteniendo los nombres de clave de la API."""
        return {
            'fec_fij_cie': self.date.isoformat() if isinstance(self.date, date) else self.date,
            'nemo': self.nemo,
            'monto_ant': self.previous_day_amount,
            'neg_ant': self.previous_day_trades,
            'precio_cierre_ant': self.previous_day_close_price,
            'PERTENECE_IGPA': 1 if self.belongs_to_igpa else 0,
            'PERTENECE_IPSA': 1 if self.belongs_to_ipsa else 0,
            'PESO_IGPA': self.weight_igpa,
            'PESO_IPSA': self.weight_ipsa,
            'razon_pre_uti': self.price_to_earnings_ratio,
            'ren_actual': self.current_yield,
            'un_transadas_ant': self.previous_day_traded_units,
        }