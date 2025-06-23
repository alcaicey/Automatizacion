import os
from flask import Flask
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# --- Importar todo lo necesario ---
from src.config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from src.extensions import db
# Importar TODOS los modelos para que SQLAlchemy los conozca
from src.models import (
    User, StockPrice, Credential, ColumnPreference, StockFilter, LastUpdate, 
    LogEntry, Alert, Portfolio, FilteredStockHistory, Dividend, DividendColumnPreference
)

# Configuración mínima de la app Flask para acceder a la DB
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
db.init_app(app)

def create_all_tables():
    """Crea todas las tablas definidas en los modelos si no existen."""
    with app.app_context():
        print("Creando todas las tablas...")
        db.create_all()
        print("✅ ¡Tablas creadas exitosamente (o ya existían)!")

if __name__ == "__main__":
    create_all_tables()