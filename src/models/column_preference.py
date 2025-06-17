from src.extensions import db

class ColumnPreference(db.Model):
    __tablename__ = 'column_preferences'
    id = db.Column(db.Integer, primary_key=True)
    columns_json = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'columns': self.columns_json,
        }