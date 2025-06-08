from . import db

class StockFilter(db.Model):
    __tablename__ = 'stock_filters'
    id = db.Column(db.Integer, primary_key=True)
    codes_json = db.Column(db.Text, nullable=True)
    all = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'codes': self.codes_json,
            'all': self.all,
        }
