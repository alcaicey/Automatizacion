# src/models/dividend.py

from src.extensions import db
from datetime import date

class Dividend(db.Model):
    __tablename__ = 'dividends'

    id = db.Column(db.Integer, primary_key=True)
    nemo = db.Column(db.String(20), nullable=False, index=True)
    description = db.Column(db.String(255))
    limit_date = db.Column(db.Date, nullable=False)
    payment_date = db.Column(db.Date, nullable=False, index=True)
    currency = db.Column(db.String(10))
    value = db.Column(db.Float, nullable=False)
    
    # --- CAMPOS NUEVOS ---
    num_acc_ant = db.Column(db.BigInteger)
    num_acc_der = db.Column(db.BigInteger)
    num_acc_nue = db.Column(db.BigInteger)
    pre_ant_vc = db.Column(db.Float)
    pre_ex_vc = db.Column(db.Float)
    
    # Restricción para evitar duplicados exactos
    __table_args__ = (
        db.UniqueConstraint('nemo', 'payment_date', 'description', name='uq_dividend'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'nemo': self.nemo,
            'descrip_vc': self.description, # Mantenemos los nombres originales para el frontend
            'fec_lim': self.limit_date.isoformat() if isinstance(self.limit_date, date) else self.limit_date,
            'fec_pago': self.payment_date.isoformat() if isinstance(self.payment_date, date) else self.payment_date,
            'moneda': self.currency,
            'val_acc': self.value,
            'num_acc_ant': self.num_acc_ant,
            'num_acc_der': self.num_acc_der,
            'num_acc_nue': self.num_acc_nue,
            'pre_ant_vc': self.pre_ant_vc,
            'pre_ex_vc': self.pre_ex_vc,
        }