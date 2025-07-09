from src.extensions import db

class BotSetting(db.Model):
    """
    Almacena configuraciones generales del bot en formato clave-valor.
    """
    __tablename__ = 'bot_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<BotSetting {self.key}={self.value}>' 