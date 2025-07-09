# --- INICIO DE LA CORRECCIÓN: Importar db desde extensions ---
from src.extensions import db
# --- FIN DE LA CORRECCIÓN ---

class Credential(db.Model):
    __tablename__ = 'credentials'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
        }