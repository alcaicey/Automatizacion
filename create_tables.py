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
    """Crea todas las tablas y, opcionalmente, inserta datos de prueba."""
    with app.app_context():
        print("Creando todas las tablas...")
        db.create_all()
        print("✅ ¡Tablas creadas exitosamente (o ya existían)!")

        # Opcional: Insertar datos de prueba si la tabla de portfolio está vacía
        if not Portfolio.query.first():
            print("La tabla 'portfolio' está vacía. Insertando datos de prueba...")
            dummy_data = [
                Portfolio(symbol='CENCOSUD', quantity=100, purchase_price=3000.0),
                Portfolio(symbol='FALABELLA', quantity=200, purchase_price=2500.0)
            ]
            db.session.bulk_save_objects(dummy_data)
            db.session.commit()
            print("✅ Datos de prueba insertados en 'portfolio'.")

if __name__ == "__main__":
    create_all_tables()