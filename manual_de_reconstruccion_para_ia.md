# Manual de Reconstrucción para IA

Este documento contiene las especificaciones técnicas completas y exhaustivas para reconstruir el proyecto de automatización financiera desde cero. Está diseñado para ser interpretado por un modelo de IA generativo.

---

## Sección 1: Setup y Configuración del Entorno

Esta sección detalla todas las dependencias, archivos de configuración y variables de entorno necesarias para ejecutar el proyecto.

### 1.1. Estructura de Directorios Principal

La IA debe generar la siguiente estructura de directorios en la raíz del proyecto:

```
/
|-- data/
|-- src/
|   |-- models/
|   |-- routes/
|   |   |-- api/
|   |-- scripts/
|   |-- static/
|   |-- templates/
|   |-- utils/
|-- tests/
|   |-- js/
|-- logs/
```

### 1.2. Dependencias del Backend (`requirements.txt`)

Crear un archivo `requirements.txt` en la raíz del proyecto con el siguiente contenido exacto:

```
aiofiles==24.1.0
annotated-types==0.7.0
anyio==4.9.0
bidict==0.23.1
blinker==1.9.0
certifi==2024.7.4
cffi==1.17.1
charset-normalizer==3.4.2
click==8.2.1
colorama==0.4.6
contourpy==1.3.2
cycler==0.12.1
distro==1.9.0
Flask==3.1.0
flask-cors==6.0.0
Flask-SocketIO==5.3.6
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.1
fonttools==4.58.4
gevent==24.2.1
gevent-websocket==0.10.1
git-filter-repo==2.47.0
greenlet==3.1.1
gunicorn==22.0.0
h11==0.16.0
h2==4.2.0
holidays==0.75
hpack==4.1.0
httpcore==1.0.9
httpx==0.28.1
Hypercorn==0.17.3
hyperframe==6.1.0
idna==3.10
iniconfig==2.1.0
itsdangerous==2.2.0
Jinja2==3.1.6
jiter==0.10.0
kiwisolver==1.4.8
MarkupSafe==3.0.2
matplotlib==3.10.3
MouseInfo==0.1.3
numpy==2.3.1
openai==1.90.0
packaging==25.0
pandas==2.2.2
pillow==10.4.0
playwright==1.53.0
playwright-stealth==2.0.0
pluggy==1.6.0
priority==2.0.0
psutil==5.9.8
psycopg2-binary==2.9.9
PyAutoGUI==0.9.54
pycparser==2.22
pydantic==2.11.7
pydantic_core==2.33.2
pydot==4.0.0
pyee==13.0.0
PyGetWindow==0.0.9
Pygments==2.19.1
PyMsgBox==1.0.9
pyparsing==3.2.3
pyperclip==1.9.0
PyRect==0.2.0
PyScreeze==1.0.1
pytest==8.4.0
pytest-flask==1.3.0
pytest-mock==3.14.0
pytest-playwright==0.5.0
pytest-xprocess==0.23.0
python-dateutil==2.9.0.post0
python-dotenv==1.0.1
python-engineio==4.12.2
python-socketio==5.13.0
pytweening==1.2.0
pytz==2025.2
pywin32==310
Quart==0.20.0
requests==2.32.3
setuptools==80.9.0
simple-websocket==1.1.0
six==1.17.0
sniffio==1.3.1
SQLAlchemy==2.0.31
sqlalchemy_schemadisplay==2.0
tqdm==4.67.1
typing-inspection==0.4.1
typing_extensions==4.14.0
tzdata==2025.2
urllib3==2.5.0
Werkzeug==3.1.3
wsproto==1.2.0
zope.event==5.0
zope.interface==6.4.post2
APScheduler==3.10.4
Flask-Login
```

### 1.3. Dependencias del Frontend (`package.json`)

Crear un archivo `package.json` en la raíz del proyecto con el siguiente contenido:

```json
{
  "name": "automatizacion",
  "version": "1.0.0",
  "description": "Aplicación web para visualizar datos de acciones de la Bolsa de Santiago.",
  "main": "index.js",
  "directories": {
    "test": "tests"
  },
  "scripts": {
    "test": "jest",
    "test:vite": "vitest"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "jest": "^30.0.4",
    "jest-environment-jsdom": "^30.0.4",
    "jquery": "^3.7.1",
    "jsdom": "^26.1.0",
    "vitest": "^2.0.2"
  }
}
```

### 1.4. Contenedor de Base de Datos (`docker-compose.yml`)

Crear un archivo `docker-compose.yml` en la raíz para definir el servicio de la base de datos TimescaleDB.

```yaml
services:
  db:
    image: timescale/timescaledb:latest-pg15
    container_name: bolsa_timescaledb
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=bolsa
    ports:
      - "5432:5432"
    volumes:
      - timescale_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d bolsa"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  timescale_data:
```

### 1.5. Variables de Entorno y Configuración

El sistema se configura a través de un archivo `src/config.py` y un archivo `.env` en la raíz.

**1.5.1. Archivo de Entorno (`.env`)**

Crear un archivo `.env` en la raíz del proyecto. Este archivo contendrá los secretos y configuraciones específicas del entorno.

```env
# Credenciales para el inicio de sesión en la web de la Bolsa de Santiago
BOLSA_USERNAME="TU_USUARIO_AQUI"
BOLSA_PASSWORD="TU_CONTRASENA_AQUI"

# URL de conexión a la base de datos.
# Si se usa el docker-compose.yml, esta URL es correcta.
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/bolsa"

# Puerto en el que correrá la aplicación Flask
FLASK_PORT=5000
```

**1.5.2. Archivo de Configuración (`src/config.py`)**

Crear un archivo `src/config.py` que cargará las variables de entorno y definirá constantes para la aplicación.

```python
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env si existe
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_SRC_DIR = os.path.join(BASE_DIR, 'src')

# Directorio de scripts de scraping
SCRIPTS_DIR = os.environ.get('BOLSA_SCRIPTS_DIR', os.path.join(PROJECT_SRC_DIR, 'scripts'))

# Carpeta para logs y archivos generados
LOGS_DIR = os.environ.get('BOLSA_LOGS_DIR', os.path.join(PROJECT_SRC_DIR, 'logs_bolsa'))
os.makedirs(LOGS_DIR, exist_ok=True)

# Archivo de estado de sesión de Playwright
STORAGE_STATE_PATH = os.path.join(LOGS_DIR, 'playwright_state.json')

# Credenciales de acceso (leídas desde el entorno)
USERNAME = os.environ.get('BOLSA_USERNAME')
PASSWORD = os.environ.get('BOLSA_PASSWORD')

# Puerto para el servidor Flask
PORT = int(os.environ.get('FLASK_PORT', 5000))

# URLs y selectores del bot
TARGET_DATA_PAGE_URL = 'https://www.bolsadesantiago.com/plus_acciones_precios'

API_PRIMARY_DATA_PATTERNS = [
    'api/RV_ResumenMercado/getAccionesPrecios',
    'api/Cuenta_Premium/getPremiumAccionesPrecios',
]

# Configuración de base de datos
DEFAULT_DB_URL = 'postgresql://postgres:postgres@localhost:5432/bolsa'
DATABASE_URL = os.environ.get('DATABASE_URL', DEFAULT_DB_URL)
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Selectores utilizados por pruebas para cerrar sesiones activas
MIS_CONEXIONES_TITLE_SELECTOR = "#mis-conexiones-title"
CERRAR_TODAS_SESIONES_SELECTOR = "#cerrar-sesiones"

# URLs y selectores para manejo de sesiones activas
ACTIVE_SESSIONS_URL_FRAGMENT = 'plus_dispositivos_conectados'
CLOSE_ALL_SESSIONS_BUTTON_SELECTOR = 'button[ng-click="deshabilitarSesionesUsuario()"]'
```

---

## Sección 2: Definición de la Base de Datos (Esquema Completo)

Esta sección define el esquema completo de la base de datos a través de los modelos de SQLAlchemy. La IA debe crear un archivo para cada modelo dentro de `src/models/`. Además, deberá crear un archivo `src/models/__init__.py` para importar todos los modelos y hacerlos accesibles.

### 2.1. `src/models/user.py`

```python
from src.extensions import db
from flask_login import UserMixin

# Se añade UserMixin para la integración con Flask-Login
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128)) # Para almacenar el hash de la contraseña

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
        }
```

### 2.2. `src/models/portfolio.py`

```python
from src.extensions import db

class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), nullable=False, index=True)
    quantity = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'purchase_price': self.purchase_price,
        }
```

### 2.3. `src/models/stock_price.py` (Tabla de TimescaleDB)

```python
from sqlalchemy import event, DDL
from src.extensions import db
from datetime import datetime, timezone

class StockPrice(db.Model):
    __tablename__ = 'stock_prices'
    # Clave primaria compuesta por símbolo y timestamp
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
            'timestamp': self.timestamp.strftime('%d/%m/%Y %H:%M:%S') if self.timestamp else None
        }

# Evento de SQLAlchemy para convertir la tabla a una Hypertable de TimescaleDB después de su creación
@event.listens_for(StockPrice.__table__, 'after_create')
def create_timescale_hypertable(target, connection, **kw):
    if connection.dialect.name == "postgresql":
        connection.execute(DDL("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
        connection.execute(
            DDL("SELECT create_hypertable('stock_prices', 'timestamp', if_not_exists => TRUE);")
        )
```

### 2.4. `src/models/stock_closing.py`

```python
from src.extensions import db
from datetime import date

class StockClosing(db.Model):
    __tablename__ = 'stock_closings'
    date = db.Column(db.Date, primary_key=True)
    nemo = db.Column(db.String(20), primary_key=True)
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
    
    __table_args__ = (db.PrimaryKeyConstraint('date', 'nemo'),)

    def to_dict(self):
        return {
            'fec_fij_cie': self.date.isoformat() if isinstance(self.date, date) else self.date,
            'nemo': self.nemo, 'monto_ant': self.previous_day_amount,
            'neg_ant': self.previous_day_trades, 'precio_cierre_ant': self.previous_day_close_price,
            'PERTENECE_IGPA': 1 if self.belongs_to_igpa else 0,
            'PERTENECE_IPSA': 1 if self.belongs_to_ipsa else 0,
            'PESO_IGPA': self.weight_igpa, 'PESO_IPSA': self.weight_ipsa,
            'razon_pre_uti': self.price_to_earnings_ratio, 'ren_actual': self.current_yield,
            'un_transadas_ant': self.previous_day_traded_units,
        }
```

### 2.5. `src/models/dividend.py`

```python
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
    num_acc_ant = db.Column(db.BigInteger)
    num_acc_der = db.Column(db.BigInteger)
    num_acc_nue = db.Column(db.BigInteger)
    pre_ant_vc = db.Column(db.Float)
    pre_ex_vc = db.Column(db.Float)
    
    __table_args__ = (
        db.UniqueConstraint('nemo', 'payment_date', 'description', name='uq_dividend'),
    )

    def to_dict(self):
        return {
            'id': self.id, 'nemo': self.nemo, 'descrip_vc': self.description,
            'fec_lim': self.limit_date.isoformat() if isinstance(self.limit_date, date) else self.limit_date,
            'fec_pago': self.payment_date.isoformat() if isinstance(self.payment_date, date) else self.payment_date,
            'moneda': self.currency, 'val_acc': self.value, 'num_acc_ant': self.num_acc_ant,
            'num_acc_der': self.num_acc_der, 'num_acc_nue': self.num_acc_nue,
            'pre_ant_vc': self.pre_ant_vc, 'pre_ex_vc': self.pre_ex_vc,
        }
```

### 2.6. `src/models/filtered_stock_history.py`

```python
from src.extensions import db
from datetime import datetime, timezone

class FilteredStockHistory(db.Model):
    __tablename__ = 'filtered_stock_history'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    symbol = db.Column(db.String(50), nullable=False, index=True)
    
    price = db.Column(db.Float)
    previous_price = db.Column(db.Float)
    price_difference = db.Column(db.Float)
    percent_change = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'price': self.price,
            'previous_price': self.previous_price,
            'price_difference': self.price_difference,
            'percent_change': self.percent_change,
        }
```

### 2.7. `src/models/anomalous_event.py`

```python
from src.extensions import db
from datetime import datetime, timezone

class AnomalousEvent(db.Model):
    __tablename__ = 'anomalous_events'

    id = db.Column(db.Integer, primary_key=True)
    nemo = db.Column(db.String(20), nullable=False, index=True)
    event_date = db.Column(db.Date, nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(100))
    price_change_pct = db.Column(db.Float, nullable=True)
    analysis_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'nemo': self.nemo,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'event_type': self.event_type,
            'description': self.description,
            'source': self.source,
            'price_change_pct': self.price_change_pct,
            'analysis_timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
        }
```

### 2.8. `src/models/advanced_kpi.py`

```python
from src.extensions import db
from datetime import datetime, timezone
from sqlalchemy.types import JSON

class AdvancedKPI(db.Model):
    __tablename__ = 'advanced_kpis'

    nemo = db.Column(db.String(20), primary_key=True)
    roe = db.Column(db.Float, nullable=True)
    debt_to_equity = db.Column(db.Float, nullable=True)
    beta = db.Column(db.Float, nullable=True)
    analyst_recommendation = db.Column(db.String(50), nullable=True)
    source = db.Column(db.Text, nullable=True)
    source_details = db.Column(JSON, nullable=True)
    calculation_details = db.Column(JSON, nullable=True)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'nemo': self.nemo,
            'roe': self.roe,
            'debt_to_equity': self.debt_to_equity,
            'beta': self.beta,
            'analyst_recommendation': self.analyst_recommendation,
            'source': self.source,
            'source_details': self.source_details,
            'calculation_details': self.calculation_details,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }
```

### 2.9. `src/models/alert.py`

```python
from src.extensions import db
from datetime import datetime

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), nullable=False, index=True)
    target_price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(10), nullable=False) # "above" or "below"
    status = db.Column(db.String(20), default='active', nullable=False, index=True) # active, triggered, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    triggered_at = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    user = db.relationship('User', backref=db.backref('alerts', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'target_price': self.target_price,
            'condition': self.condition,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'user_id': self.user_id
        }
```

### 2.10. `src/models/log_entry.py`

```python
from src.extensions import db
from datetime import datetime, timezone

class LogEntry(db.Model):
    __tablename__ = 'log_entries'
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)
    action = db.Column(db.String(50))
    stack = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'action': self.action,
            'stack': self.stack,
            'timestamp': self.timestamp.strftime('%d/%m/%Y %H:%M:%S') if self.timestamp else None,
        }
```

### 2.11. Modelos de Configuración y Utilidad

Estos son modelos más pequeños, principalmente para configuraciones.

**`src/models/kpi_selection.py`**
```python
from src.extensions import db

class KpiSelection(db.Model):
    __tablename__ = 'kpi_selections'
    nemo = db.Column(db.String(20), primary_key=True)
```

**`src/models/last_update.py`**
```python
from src.extensions import db
from datetime import datetime, timezone

class LastUpdate(db.Model):
    __tablename__ = 'last_update'
    id = db.Column(db.Integer, primary_key=True, default=1)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
```

**`src/models/prompt_config.py`**
```python
from src.extensions import db

class PromptConfig(db.Model):
    __tablename__ = 'prompt_configs'
    id = db.Column(db.String(50), primary_key=True)
    api_provider = db.Column(db.String(50), nullable=False)
    api_key = db.Column(db.String(255), nullable=False)
    prompt_template = db.Column(db.Text, nullable=False)
    model_name = db.Column(db.String(100), default='gpt-3.5-turbo')
```

**`src/models/column_preference.py` (y similares)**

Este patrón se usa para varios modelos de preferencias. La IA debe crear un archivo para cada uno, cambiando solo el `__tablename__`.

-   **`src/models/column_preference.py`**: `__tablename__ = 'column_preferences'`
-   **`src/models/portfolio_column_preference.py`**: `__tablename__ = 'portfolio_column_preferences'`
-   **`src/models/dividend_column_preference.py`**: `__tablename__ = 'dividend_column_preferences'`
-   **`src/models/closing_column_preference.py`**: `__tablename__ = 'closing_column_preferences'`

Contenido base para estos archivos:
```python
from src.extensions import db
from sqlalchemy.types import JSON

class ColumnPreference(db.Model): # El nombre de la clase cambia en cada archivo
    # El __tablename__ también cambia como se indica arriba
    __tablename__ = '...'
    id = db.Column(db.Integer, primary_key=True)
    # Se usa JSON para más flexibilidad
    columns = db.Column(JSON, nullable=False) 
```

### 2.12. Archivo de Inicialización de Modelos (`src/models/__init__.py`)

Crear este archivo para hacer que todos los modelos sean fácilmente importables.

```python
from .user import User
from .portfolio import Portfolio
from .stock_price import StockPrice
from .stock_closing import StockClosing
from .dividend import Dividend
from .filtered_stock_history import FilteredStockHistory
from .anomalous_event import AnomalousEvent
from .advanced_kpi import AdvancedKPI
from .alert import Alert
from .log_entry import LogEntry
from .kpi_selection import KpiSelection
from .last_update import LastUpdate
from .prompt_config import PromptConfig
from .column_preference import ColumnPreference
from .portfolio_column_preference import PortfolioColumnPreference
from .dividend_column_preference import DividendColumnPreference
from .closing_column_preference import ClosingColumnPreference

# Opcional: una lista __all__ para importaciones con *
__all__ = [
    'User', 'Portfolio', 'StockPrice', 'StockClosing', 'Dividend',
    'FilteredStockHistory', 'AnomalousEvent', 'AdvancedKPI', 'Alert',
    'LogEntry', 'KpiSelection', 'LastUpdate', 'PromptConfig', 'ColumnPreference',
    'PortfolioColumnPreference', 'DividendColumnPreference', 'ClosingColumnPreference'
]
```

---

## Sección 3: Implementación del Backend (Archivo por Archivo)

Esta sección define la lógica de negocio del backend, la API y la estructura general de la aplicación Flask. La IA debe generar los archivos en las rutas especificadas.

### 3.1. Inicialización de Extensiones (`src/extensions.py`)

Este archivo instancia las extensiones de Flask para que puedan ser importadas y utilizadas en toda la aplicación sin causar importaciones circulares.

```python
# src/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# Instancia de la base de datos. Se inicializará en main.py.
db = SQLAlchemy()

# Instancia de Socket.IO para comunicación en tiempo real.
socketio = SocketIO()
```

### 3.2. Punto de Entrada Principal (`src/main.py`)

Este es el corazón de la aplicación. Orquesta la creación de la app, la inicialización de extensiones, el inicio de procesos en segundo plano y el arranque del servidor.

**Lógica Clave a Implementar:**
1.  **Función `create_app`:** Sigue el patrón de "Application Factory" de Flask.
2.  **Loop de Eventos Asíncrono en Hilo Separado:**
    -   Se debe crear un `asyncio.new_event_loop()`.
    -   Este loop debe ejecutarse en un `threading.Thread` separado. Esto es **CRÍTICO** para que las operaciones asíncronas de Playwright no bloqueen el servidor web síncrono de Gevent.
    -   El loop se debe adjuntar al objeto `app` de Flask (ej. `app.bot_event_loop = bot_loop`) para que otras partes de la aplicación puedan enviar tareas a él.
3.  **Inicialización dentro del Contexto de la App:**
    -   `db.init_app(app)` y `socketio.init_app(app)` deben ser llamadas.
    -   Se debe llamar a `db.create_all()` para generar el esquema de la base de datos si no existe.
4.  **Servidor WSGI:** Utilizar `gevent.pywsgi.WSGIServer` con `WebSocketHandler` para soportar eficientemente WebSockets.
5.  **Manejo de Cierre (Graceful Shutdown):** Implementar un bloque `try...finally` para detener el loop de eventos del bot de forma segura cuando el servidor se apaga.

**Código de `src/main.py`:**

```python
# src/main.py
import asyncio
import logging
import threading
from flask import Flask, render_template, send_from_directory
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

from src import config
from src.extensions import db, socketio

# Importar todos los modelos para que SQLAlchemy los reconozca al crear las tablas
from src.models import *

# Importar Blueprints (se crearán en pasos posteriores)
# from src.routes.errors import errors_bp
# from src.routes.user import user_bp
# from src.routes.api import api_bp
# from src.routes.crud_api import crud_bp
# from src.routes.architecture import architecture_bp

# Configuración básica del logging
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] [%(name)s] %(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def create_app(config_module=config):
    """Fábrica de la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_object(config_module)
    return app

def main():
    """Punto de entrada principal que configura y corre la aplicación."""
    app = create_app()

    # Inicializar extensiones con la instancia de la app
    db.init_app(app)
    socketio.init_app(app, async_mode='gevent', cors_allowed_origins="*")

    # --- Hilo para el Loop de Eventos del Bot ---
    def run_bot_loop(loop):
        asyncio.set_event_loop(loop)
        logger.info("Iniciando el event loop del bot en un hilo de fondo...")
        loop.run_forever()

    bot_loop = asyncio.new_event_loop()
    app.bot_event_loop = bot_loop
    
    bot_thread = threading.Thread(target=run_bot_loop, args=(bot_loop,), daemon=True)
    bot_thread.start()
    logger.info("Hilo del bot de Playwright iniciado.")

    with app.app_context():
        # Crear todas las tablas de la base de datos
        db.create_all()

        # Mapear modelos para el CRUD genérico (opcional pero recomendado)
        app.model_map = {model.__tablename__: model for model in db.Model.__subclasses__() if hasattr(model, '__tablename__')}
        logger.info(f"Modelos mapeados para el CRUD: {list(app.model_map.keys())}")


    # --- Definición de Rutas Estáticas ---
    @app.route('/')
    def index(): return render_template('dashboard.html')
    @app.route('/dashboard')
    def dashboard(): return render_template('dashboard.html')
    @app.route('/historico')
    def historico(): return render_template('historico.html')
    @app.route('/indicadores')
    def indicadores(): return render_template('indicadores.html')
    @app.route('/logs')
    def logs(): return render_template('logs.html')
    @app.route('/mantenedores')
    def mantenedores(): return render_template('mantenedores.html')
    @app.route('/login')
    def login(): return render_template('login.html')

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(app.static_folder, 'favicon.svg')

    # --- Registro de Blueprints ---
    # La IA deberá descomentar y registrar estos a medida que los crea.
    # app.register_blueprint(errors_bp)
    # app.register_blueprint(user_bp)
    # app.register_blueprint(api_bp, url_prefix='/api')
    # app.register_blueprint(crud_bp, url_prefix='/api/crud')
    # app.register_blueprint(architecture_bp)

    port = app.config.get('PORT', 5000)
    http_server = WSGIServer(('0.0.0.0', port), app, handler_class=WebSocketHandler)
    logger.info(f"Servidor iniciado en http://localhost:{port}")
    
    try:
        http_server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Deteniendo el servidor...")
    finally:
        # Limpieza de recursos
        if bot_loop.is_running():
            bot_loop.call_soon_threadsafe(bot_loop.stop)
        bot_thread.join(timeout=5)
        logger.info("Servidor detenido y recursos limpiados.")

if __name__ == '__main__':
    main()
```

### 3.3. Estructura de la API REST (`src/routes/api/`)

La API se organiza en un `Blueprint` principal llamado `api_bp`. Cada conjunto de rutas relacionadas (bot, datos, etc.) se definirá en su propio archivo.

**3.3.1. Inicialización del Blueprint de la API (`src/routes/api/__init__.py`)**

Este archivo crea la instancia del Blueprint que será utilizada por todos los endpoints de la API.

```python
# src/routes/api/__init__.py
from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Importar las rutas al final para evitar importaciones circulares
from . import bot_routes, config_routes, data_routes, drainer_routes, portfolio_routes, system_routes
```

**3.3.2. Rutas de Control del Bot (`src/routes/api/bot_routes.py`)**

Este es el archivo más crítico para las operaciones de fondo. Define los endpoints que inician las tareas de scraping y procesamiento de datos.

**Patrón de Diseño Clave para la IA:**
Todos los endpoints `POST` en este archivo deben seguir este patrón de ejecución para tareas de larga duración:
1.  Recibir la petición HTTP.
2.  Responder inmediatamente con un código `202 Accepted` y un mensaje de "proceso iniciado".
3.  Iniciar un nuevo `threading.Thread` para ejecutar la lógica principal.
4.  Dentro del hilo, obtener el loop de eventos de asyncio (`current_app.bot_event_loop`).
5.  Usar `asyncio.run_coroutine_threadsafe()` para ejecutar la corrutina de negocio (ej. el scraper) en el loop de eventos del bot.
6.  Esperar a que la corrutina termine usando `future.result()`.
7.  Al finalizar (ya sea con éxito o con error), usar `socketio.emit()` para enviar una notificación al cliente con los resultados.

**Código de `src/routes/api/bot_routes.py`:**

```python
# src/routes/api/bot_routes.py
import asyncio
import logging
import threading
from flask import jsonify, current_app

from src.routes.api import api_bp
from src.scripts.bolsa_service import run_bolsa_bot, is_bot_running
from src.scripts import dividend_service, closing_service, ai_financial_service
from src.extensions import socketio, db
from src.models import KpiSelection

logger = logging.getLogger(__name__)

@api_bp.route("/bot-status", methods=["GET"])
def bot_status():
    """
    Endpoint: GET /api/bot-status
    Descripción: Devuelve el estado actual del bot (si está ocupado o no).
    Respuesta (200 OK):
        { "is_running": <boolean> }
    """
    return jsonify({"is_running": is_bot_running()})


@api_bp.route("/stocks/update", methods=["POST"])
def update_stocks():
    """
    Endpoint: POST /api/stocks/update
    Descripción: Inicia el proceso principal de scraping de precios de acciones.
    Respuesta (202 Accepted):
        { "success": true, "message": "Proceso de actualización de acciones iniciado." }
    Notificación Socket.IO al finalizar: 'update_complete' con los resultados.
    """
    if is_bot_running():
        return jsonify({"success": False, "message": "Ya hay una actualización en curso."}), 409

    def task_in_thread(app):
        loop = app.bot_event_loop
        if not loop or not loop.is_running():
            logger.error("El loop de eventos del bot no está disponible.")
            return

        future = asyncio.run_coroutine_threadsafe(run_bolsa_bot(app=app), loop)
        try:
            future.result(timeout=400)  # Timeout de ~6.5 minutos
        except Exception as e:
            logger.error(f"Error en la tarea de actualización de acciones: {e}", exc_info=True)
            socketio.emit('update_error', {'error': str(e)})

    threading.Thread(target=task_in_thread, args=(current_app._get_current_object(),), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de acciones iniciado."}), 202


@api_bp.route("/dividends/update", methods=["POST"])
def update_dividends():
    """
    Endpoint: POST /api/dividends/update
    Descripción: Inicia la actualización de los datos de dividendos.
    Respuesta (202 Accepted):
        { "success": true, "message": "Proceso de actualización de dividendos iniciado." }
    Notificación Socket.IO al finalizar: 'dividend_update_complete' con los resultados.
    """
    def task_in_thread(app):
        result = {}
        try:
            loop = app.bot_event_loop
            future = asyncio.run_coroutine_threadsafe(dividend_service.compare_and_update_dividends(), loop)
            with app.app_context():
                 result = future.result(timeout=120)
        except Exception as e:
            logger.error(f"Error en la actualización de dividendos: {e}", exc_info=True)
            result = {"error": str(e)}
        finally:
            socketio.emit('dividend_update_complete', result)

    threading.Thread(target=task_in_thread, args=(current_app._get_current_object(),), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de dividendos iniciado."}), 202

@api_bp.route("/closing/update", methods=["POST"])
def update_closing_data():
    """
    Endpoint: POST /api/closing/update
    Descripción: Inicia la actualización de los datos de cierre diario.
    Respuesta (202 Accepted):
        { "success": true, "message": "Proceso de actualización de Cierre Bursátil iniciado." }
    Notificación Socket.IO al finalizar: 'closing_update_complete' con los resultados.
    """
    def task_in_thread(app):
        result = {}
        try:
            loop = app.bot_event_loop
            future = asyncio.run_coroutine_threadsafe(closing_service.update_stock_closings(), loop)
            with app.app_context():
                result = future.result(timeout=120)
        except Exception as e:
            logger.error(f"Error en la actualización de Cierre Bursátil: {e}", exc_info=True)
            result = {"error": str(e)}
        finally:
            socketio.emit('closing_update_complete', result)

    threading.Thread(target=task_in_thread, args=(current_app._get_current_object(),), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de Cierre Bursátil iniciado."}), 202

@api_bp.route("/kpis/update", methods=["POST"])
def update_advanced_kpis():
    """
    Endpoint: POST /api/kpis/update
    Descripción: Lanza un análisis con IA para obtener KPIs avanzados de las acciones seleccionadas.
    Respuesta (202 Accepted):
        { "success": true, "message": "Proceso de actualización de KPIs iniciado..." }
    Notificación Socket.IO durante el proceso: 'kpi_update_progress'
    Notificación Socket.IO al finalizar: 'kpi_update_complete'
    """
    def task_in_thread(app):
        with app.app_context():
            try:
                loop = app.bot_event_loop
                nemos = [s.nemo for s in KpiSelection.query.all()]
                if not nemos:
                    socketio.emit('kpi_update_complete', {'message': 'No hay acciones seleccionadas.'})
                    return

                socketio.emit('kpi_update_progress', {'status': 'info', 'message': f'Iniciando análisis de IA para {len(nemos)} acciones...'})
                
                # Definir la tarea asíncrona a ejecutar
                async def fetch_and_save_kpis():
                    tasks = [ai_financial_service.get_advanced_kpis(nemo) for nemo in nemos]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Filtrar resultados y guardar en DB
                    with app.app_context():
                         # La lógica de upsert de los KPIs se debe implementar aquí
                         pass

                future = asyncio.run_coroutine_threadsafe(fetch_and_save_kpis(), loop)
                future.result(timeout=600)
                socketio.emit('kpi_update_complete', {'message': 'Actualización de KPIs completada.'})

            except Exception as e:
                logger.error(f"Error en la actualización de KPIs: {e}", exc_info=True)
                socketio.emit('kpi_update_complete', {'error': str(e)})

    threading.Thread(target=task_in_thread, args=(current_app._get_current_object(),), daemon=True).start()
    return jsonify({"success": True, "message": "Proceso de actualización de KPIs iniciado."}), 202
```

**3.3.3. Rutas de Consulta de Datos (`src/routes/api/data_routes.py`)**

Este archivo contiene los endpoints `GET` que el frontend utiliza para poblar todas sus vistas con datos de la base de datos.

**Código y Contratos de API de `src/routes/api/data_routes.py`:**

```python
# src/routes/api/data_routes.py
import logging
from flask import jsonify, request, current_app
from sqlalchemy import func

from . import api_bp
from src.utils.db_io import get_latest_data
from src.extensions import db
from src.models import StockPrice, Dividend, StockClosing, AdvancedKPI, KpiSelection, FilteredStockHistory

logger = logging.getLogger(__name__)

@api_bp.route('/all_stock_symbols', methods=['GET'])
def get_all_stock_symbols():
    """
    Endpoint: GET /api/all_stock_symbols
    Descripción: Devuelve una lista plana de todos los símbolos (nemos) de acciones únicos disponibles.
    Respuesta (200 OK):
        ["NEMO1", "NEMO2", "NEMO3", ...]
    """
    symbols = [s[0] for s in db.session.query(StockPrice.symbol).distinct().all()]
    return jsonify(symbols)

@api_bp.route("/stocks", methods=["GET"])
def get_stocks():
    """
    Endpoint: GET /api/stocks
    Descripción: Devuelve los datos más recientes de precios de acciones.
                 Utiliza la función de fallback a JSON si la base de datos falla.
    Respuesta (200 OK):
        {
            "stocks": [ { "NEMO": "...", "PRECIO_CIERRE": "...", ... } ],
            "last_update": "dd/mm/YYYY HH:MM:SS"
        }
    """
    return jsonify(get_latest_data())

@api_bp.route("/dividends", methods=["GET"])
def get_dividends():
    """
    Endpoint: GET /api/dividends
    Descripción: Devuelve una lista de dividendos, con opción de filtrar.
    Parámetros de Query:
        - is_ipsa (opcional): 'true' para filtrar solo acciones del IPSA.
        - search_text (opcional): texto para buscar en el nemo o descripción.
    Respuesta (200 OK):
        [ { "id": ..., "nemo": ..., "payment_date": ..., "value": ..., "is_ipsa": <boolean> }, ... ]
    """
    query = db.session.query(Dividend) # La lógica de join/filtro se añade aquí
    # ... (implementar la lógica de filtrado completa como en el original) ...
    dividends = query.all()
    # ... (implementar el enriquecimiento con 'is_ipsa') ...
    return jsonify([d.to_dict() for d in dividends])

@api_bp.route("/closing", methods=["GET"])
def get_closing_data():
    """
    Endpoint: GET /api/closing
    Descripción: Devuelve los datos del último cierre bursátil.
    Respuesta (200 OK):
        [ { "fec_fij_cie": ..., "nemo": ..., "precio_cierre_ant": ... }, ... ]
    """
    latest_date = db.session.query(func.max(StockClosing.date)).scalar()
    if not latest_date:
        return jsonify([])
    closings = StockClosing.query.filter_by(date=latest_date).all()
    return jsonify([c.to_dict() for c in closings])

@api_bp.route("/kpis", methods=["GET"])
def get_all_kpis():
    """
    Endpoint: GET /api/kpis
    Descripción: Combina los datos del último cierre con los KPIs avanzados
                 para las acciones seleccionadas por el usuario.
    Respuesta (200 OK):
        [
            {
                "nemo": "...", "precio_cierre_ant": ..., "roe": ...,
                "debt_to_equity": ..., "beta": ..., "riesgo": "...", ...
            }, ...
        ]
    """
    # ... (implementar la lógica de join entre StockClosing y AdvancedKPI) ...
    # La IA debe reconstruir esta lógica basándose en los modelos y el propósito.
    return jsonify([]) # Placeholder

@api_bp.route("/dashboard/chart-data", methods=["GET"])
def get_dashboard_chart_data():
    """
    Endpoint: GET /api/dashboard/chart-data
    Descripción: Devuelve datos de series temporales para un conjunto de acciones
                 y una métrica específica, listos para ser usados en gráficos.
    Parámetros de Query:
        - stock[]: Uno o más símbolos de acciones.
        - metric: 'price', 'price_difference', 'percent_change'.
        - start_date, end_date: 'YYYY-MM-DD'.
        - granularity: 'hour', 'day', 'week'.
    Respuesta (200 OK):
        {
            "NEMO1": [ {"x": "ISO_DATETIME", "y": <float>}, ... ],
            "NEMO2": [ {"x": "ISO_DATETIME", "y": <float>}, ... ]
        }
    """
    # ... (implementar la lógica de agregación con date_trunc) ...
    return jsonify({}) # Placeholder
```

**3.3.4. Rutas de Gestión y Configuración**

Este conjunto de archivos proporciona endpoints para que el usuario gestione su portafolio, configure las vistas de la aplicación y ejecute análisis específicos. Son, en su mayoría, operaciones CRUD síncronas.

**`src/routes/api/portfolio_routes.py`**

```python
# src/routes/api/portfolio_routes.py
from flask import jsonify, request
from . import api_bp
from src.extensions import db
from src.models import Portfolio, KpiSelection

@api_bp.route("/portfolio", methods=["GET", "POST"])
def portfolio_handler():
    """
    Endpoint: GET, POST /api/portfolio
    Descripción: Obtiene o añade un activo al portafolio del usuario.
    - GET: Devuelve todos los activos.
        - Respuesta (200 OK): [ { "id": ..., "symbol": ..., "quantity": ..., "purchase_price": ... }, ... ]
    - POST: Añade un nuevo activo.
        - Request Body: { "symbol": "...", "quantity": <float>, "purchase_price": <float> }
        - Respuesta (201 Created): { "id": ..., "symbol": ..., ... }
        - Respuesta (400 Bad Request): { "error": "Datos de portafolio inválidos." }
    """
    if request.method == 'GET':
        holdings = Portfolio.query.order_by(Portfolio.symbol).all()
        return jsonify([h.to_dict() for h in holdings])
    
    if request.method == 'POST':
        data = request.get_json()
        # ... (implementar lógica de creación y manejo de errores) ...
        return jsonify({}), 201

@api_bp.route("/portfolio/<int:holding_id>", methods=["DELETE"])
def delete_from_portfolio(holding_id):
    """
    Endpoint: DELETE /api/portfolio/<holding_id>
    Descripción: Elimina un activo del portafolio.
    Respuesta (204 No Content): (Sin cuerpo)
    Respuesta (404 Not Found): { "error": "Registro no encontrado..." }
    """
    # ... (implementar lógica de borrado) ...
    return '', 204

@api_bp.route("/kpis/selection", methods=["GET", "POST"])
def handle_kpi_selection():
    """
    Endpoint: GET, POST /api/kpis/selection
    Descripción: Obtiene o actualiza la lista de acciones seleccionadas para análisis de KPI.
    - GET: Devuelve todas las acciones disponibles y si están seleccionadas.
        - Respuesta (200 OK): [ { "nemo": "...", "is_selected": <boolean> }, ... ]
    - POST: Reemplaza la selección actual con una nueva.
        - Request Body: { "nemos": ["NEMO1", "NEMO2", ...] }
        - Respuesta (200 OK): { "success": true, "message": "..." }
    """
    # ... (implementar lógica GET y POST) ...
    return jsonify({})
```

**`src/routes/api/config_routes.py`**

```python
# src/routes/api/config_routes.py
from flask import jsonify, request
import json
from . import api_bp
from src.extensions import db
from src.models import ColumnPreference, StockFilter # y otros modelos de preferencia

@api_bp.route("/columns", methods=["GET", "POST"])
def handle_columns():
    """
    Endpoint: GET, POST /api/columns
    Descripción: Gestiona las columnas visibles para la tabla principal de acciones.
    - GET: Devuelve todas las columnas posibles y las que están visibles actualmente.
        - Respuesta (200 OK): { "all_columns": [...], "visible_columns": [...] }
    - POST: Guarda la nueva selección de columnas visibles.
        - Request Body: { "columns": ["col1", "col2", ...] }
        - Respuesta (200 OK): { "success": true }
    """
    # La IA debe implementar un endpoint similar para cada tipo de preferencia de columna:
    # /api/portfolio/columns, /api/dividends/columns, /api/closing/columns, /api/kpis/columns
    # ... (implementar lógica GET y POST) ...
    return jsonify({})

@api_bp.route("/filters", methods=["GET", "POST"])
def handle_filters():
    """
    Endpoint: GET, POST /api/filters
    Descripción: Gestiona el filtro de acciones a ser procesadas por el bot.
    - GET: Devuelve la configuración de filtro actual.
        - Respuesta (200 OK): { "codes": [...], "all": <boolean> }
    - POST: Guarda la nueva configuración de filtro.
        - Request Body: { "codes": ["NEMO1", ...], "all": <boolean> }
        - Respuesta (200 OK): { "success": true }
    """
    # ... (implementar lógica GET y POST) ...
    return jsonify({})

@api_bp.route("/kpi-prompt", methods=["GET", "POST"])
def handle_kpi_prompt():
    """
    Endpoint: GET, POST /api/kpi-prompt
    Descripción: Gestiona la plantilla de prompt para la IA de KPIs.
    - GET: Devuelve el prompt actual.
        - Respuesta (200 OK): { "prompt": "..." }
    - POST: Actualiza el prompt.
        - Request Body: { "prompt": "..." }
        - Respuesta (200 OK): { "success": true }
    """
    # ... (implementar lógica GET y POST) ...
    return jsonify({})
```

**`src/routes/api/drainer_routes.py`**

```python
# src/routes/api/drainer_routes.py
import threading
from flask import jsonify, current_app
from . import api_bp
from src.scripts.drainer_service import run_drainer_analysis
from src.models import AnomalousEvent

@api_bp.route("/drainers/events", methods=["GET"])
def get_drainer_events():
    """
    Endpoint: GET /api/drainers/events
    Descripción: Devuelve todos los eventos anómalos (picos de volumen) detectados.
    Respuesta (200 OK):
        [ { "id": ..., "nemo": ..., "event_date": ..., "description": ... }, ... ]
    """
    events = AnomalousEvent.query.order_by(AnomalousEvent.event_date.desc()).all()
    return jsonify([event.to_dict() for event in events])

@api_bp.route("/drainers/analyze", methods=["POST"])
def trigger_drainer_analysis():
    """
    Endpoint: POST /api/drainers/analyze
    Descripción: Inicia el análisis de picos de volumen en segundo plano.
                 Sigue el patrón de "tarea en hilo" pero no necesita el loop de asyncio.
    Respuesta (202 Accepted):
        { "message": "El análisis... ha comenzado." }
    Notificación Socket.IO al finalizar: 'drainer_complete'
    """
    def analysis_task(app):
        with app.app_context():
            run_drainer_analysis()
            # Al finalizar, notificar al cliente.
            from src.extensions import socketio
            socketio.emit('drainer_complete', {'message': 'Análisis de drainers finalizado.'})

    thread = threading.Thread(target=analysis_task, args=(current_app._get_current_object(),), daemon=True)
    thread.start()
    
    return jsonify({"message": "El análisis de adelantamientos ha comenzado."}), 202
```

### 3.4. Lógica de Negocio y Scrapers (`src/scripts/`)

Esta sección detalla el "cerebro" de la aplicación: los scripts que interactúan con Playwright para realizar el web scraping. La IA debe ser instruida para seguir esta lógica algorítmica de forma precisa.

**3.4.1. Orquestador Principal (`src/scripts/bolsa_service.py`)**

Este archivo contiene la corrutina principal `run_bolsa_bot`, que coordina todo el proceso.

**Lógica Algorítmica de `run_bolsa_bot`:**
La IA debe implementar una corrutina `async def run_bolsa_bot(app)` que siga estos pasos:

1.  **Implementar un Lock Asíncrono**:
    -   Definir un `_bot_running_lock = asyncio.Lock()` a nivel de módulo.
    -   Al inicio de la función, intentar adquirir el lock con un timeout corto (ej. `asyncio.wait_for(_bot_running_lock.acquire(), timeout=0.1)`). Si falla, significa que el bot ya está en ejecución, por lo que debe registrar un mensaje y retornar inmediatamente.
2.  **Envolver en `try...finally`**: Todo el cuerpo de la función debe estar dentro de un bloque `try...finally` para asegurar que el lock se libere (`_bot_running_lock.release()`) al final, sin importar si hubo éxito o error.
3.  **Obtener Página de Playwright**:
    -   Llamar a una función `get_page()` (que se definirá en `bot_page_manager.py`) para obtener la instancia de la página del navegador.
4.  **Chequeo de Salud de la Sesión**:
    -   Llamar a una corrutina `perform_session_health_check(page, username, password)`.
    -   Esta corrutina debe:
        a. Navegar a la página principal del sitio.
        b. Comprobar si un elemento específico del perfil de usuario es visible.
        c. Si no es visible, llamar a la corrutina `auto_login()` (que se definirá en `bot_login.py`).
        d. Una vez la sesión está asegurada, navegar explícitamente a la URL de la página de datos (`TARGET_DATA_PAGE_URL` de `config.py`).
5.  **Bucle de Captura con Reintentos**:
    -   Iniciar un bucle `for` con un máximo de 3 intentos.
    -   Dentro del bucle:
        a. Llamar a una corrutina `_attempt_data_capture(page)`.
        b. Esta corrutina `_attempt_data_capture` es clave:
            i. Crea una tarea (`asyncio.create_task`) para escuchar el tráfico de red y capturar la respuesta de la API interna que contiene los datos de precios. La URL a interceptar está en `config.API_PRIMARY_DATA_PATTERNS`.
            ii. Crea otra tarea para extraer la hora del mercado desde un elemento en la UI.
            iii. Dispara una recarga de la página con `page.reload()`.
            iv. Usa `asyncio.gather` para esperar a que ambas tareas finalicen y retornen los datos capturados.
        c. Si ambos datos (hora y precios) fueron capturados con éxito, salir del bucle.
        d. Si falla, esperar un tiempo (`asyncio.sleep`) antes del siguiente intento.
6.  **Validación de Datos**:
    -   Verificar que los datos de precios recibidos no estén vacíos y tengan la estructura esperada.
7.  **Almacenamiento en Base de Datos**:
    -   Obtener el contexto de la aplicación Flask (`with app.app_context():`).
    -   Llamar a una función `store_prices_in_db(raw_data, market_time)` (que se definirá en `db_io.py`) para guardar los datos en la tabla `StockPrice`.
    -   Llamar a `save_filtered_comparison_history()` para guardar los datos para el histórico.
8.  **Notificación al Frontend**:
    -   Si todo el proceso fue exitoso, emitir un evento de Socket.IO `socketio.emit('update_complete', ...)`
    -   En caso de cualquier excepción durante el proceso, capturarla, registrar el error y emitir un evento `socketio.emit('bot_error', ...)`.

**`src/scripts/bot_login.py` y `src/scripts/bot_data_capture.py`**
La IA debe crear estos archivos con las corrutinas de bajo nivel que son llamadas por `bolsa_service`.
-   **`auto_login`**: debe contener la lógica para encontrar los campos de usuario y contraseña en la página, llenarlos con las credenciales del `config.py`, y hacer clic en el botón de inicio de sesión, con manejo de errores si el login falla.
-   **`capture_premium_data_via_network`**: debe usar `page.on('response', ...)` de Playwright para interceptar las respuestas de la red, encontrar la que coincide con los patrones de la API, y devolver su contenido JSON.
-   **`capture_market_time`**: debe usar `page.locator(...).inner_text()` para encontrar el elemento que contiene la hora y extraerla.

**3.4.2. Interacción con la Base de Datos (`src/utils/db_io.py`)**

Este archivo contiene las funciones que el `bolsa_service` usa para comunicarse con la base de datos.

**Lógica de `store_prices_in_db`:**
1.  Recibe la lista de diccionarios de acciones y el timestamp del mercado.
2.  Itera sobre cada diccionario.
3.  Para cada uno, crea una instancia del modelo `StockPrice`.
4.  Utiliza `db.session.merge(stock_price_instance)` para realizar un "upsert": si ya existe una fila con esa clave primaria (símbolo y timestamp), la actualiza; si no, la inserta.
5.  Finaliza con `db.session.commit()`.

**Lógica de `get_latest_data` (con fallback a JSON):**
1.  **Bloque `try`**:
    -   Realiza una consulta a la tabla `StockPrice` para obtener los datos con el timestamp más reciente.
2.  **Bloque `except`**:
    -   Si la consulta falla, registra el error.
    -   Busca en el directorio de logs (`config.LOGS_DIR`) el último archivo JSON de precios guardado.
    -   Lee y devuelve el contenido de ese archivo JSON.
3.  **Respaldo en JSON**: La IA debe asegurarse de que, después de cada captura de red exitosa en `bolsa_service`, los datos crudos se guarden en un archivo `precios_YYYY-MM-DD_HH-MM-SS.json` en el directorio de logs.

### 3.5. Programador de Tareas en Segundo Plano (`src/utils/scheduler.py`)

Este archivo es responsable de ejecutar el bot de scraping de forma periódica y desatendida.

**Lógica Algorítmica:**
1.  **Control del Hilo**:
    -   Definir variables globales para el hilo (`update_thread = None`) y un lock (`stop_event = threading.Event()`) para detenerlo de forma segura.
2.  **Función `update_data_periodically`**:
    -   Esta función se ejecutará en el hilo de fondo.
    -   Debe contener un bucle `while not stop_event.is_set():`.
    -   Dentro del bucle:
        a. Calcular un tiempo de espera aleatorio en segundos (ej. entre 15 y 45 minutos).
        b. Usar `stop_event.wait(timeout=...)` en lugar de `time.sleep()`. Esto permite que el hilo se detenga casi inmediatamente si se solicita, en lugar de tener que esperar a que termine el largo período de sueño.
        c. Si el `wait` no fue interrumpido, obtener la `app` y su `bot_event_loop`.
        d. Crear una corrutina para ejecutar el bot: `task = run_bolsa_bot(app)`.
        e. Enviar la tarea al loop de eventos del bot usando `asyncio.run_coroutine_threadsafe(task, bot_loop)`.
3.  **Funciones `start_periodic_updates` y `stop_periodic_updates`**:
    -   `start`: Debe verificar que no haya un hilo ya corriendo, luego crear e iniciar una nueva instancia de `threading.Thread` apuntando a `update_data_periodically`.
    -   `stop`: Debe establecer el `stop_event` (`stop_event.set()`) y esperar a que el hilo termine con `update_thread.join()`.

**Integración con `main.py`:**
La IA debe ser instruida para añadir el siguiente código en `src/main.py` después de que el hilo del bot se haya iniciado, para que el scheduler comience a funcionar automáticamente al arrancar la aplicación.

```python
# En src/main.py, dentro de la función main()

from src.utils import scheduler

# ... después de bot_thread.start() ...
scheduler.start_periodic_updates(app=app)
logger.info("Scheduler de actualizaciones periódicas iniciado.")

# Y en el bloque `finally` del cierre del servidor:
# ... antes de la limpieza del bot_loop ...
scheduler.stop_periodic_updates()
logger.info("Scheduler de actualizaciones periódicas detenido.")
```

**Código de `src/utils/scheduler.py`:**

```python
# src/utils/scheduler.py
import threading
import time
import random
import logging
import asyncio

from src.scripts.bolsa_service import run_bolsa_bot

logger = logging.getLogger(__name__)

update_thread = None
stop_event = threading.Event()

def update_data_periodically(app, min_minutes=15, max_minutes=45):
    """
    Función que se ejecuta en un hilo para actualizar datos periódicamente.
    """
    global stop_event
    logger.info("Hilo del scheduler iniciado.")
    while not stop_event.is_set():
        try:
            wait_seconds = random.randint(min_minutes * 60, max_minutes * 60)
            logger.info(f"Scheduler: Próxima actualización automática en {wait_seconds / 60:.1f} minutos.")
            
            # Usar wait() permite una detención más rápida
            if stop_event.wait(timeout=wait_seconds):
                break # Salir si el evento de detención fue activado

            logger.info("Scheduler: Despertando para ejecutar actualización automática.")
            
            bot_loop = app.bot_event_loop
            if bot_loop and bot_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(run_bolsa_bot(app), bot_loop)
                future.result(timeout=420) # Darle un timeout de 7 minutos
            else:
                logger.warning("Scheduler: El loop de eventos del bot no está corriendo, se omite la actualización.")

        except Exception as e:
            logger.error(f"Error en el ciclo de actualización del scheduler: {e}", exc_info=True)
            # Esperar antes de reintentar para no entrar en un bucle de errores rápidos
            time.sleep(60)
    
    logger.info("Hilo del scheduler detenido.")


def start_periodic_updates(app, min_minutes=15, max_minutes=45):
    """Inicia el hilo de actualización periódica si no está ya corriendo."""
    global update_thread, stop_event
    if update_thread is None or not update_thread.is_alive():
        stop_event.clear()
        update_thread = threading.Thread(
            target=update_data_periodically,
            args=(app, min_minutes, max_minutes),
            daemon=True
        )
        update_thread.start()
        return True
    return False

def stop_periodic_updates():
    """Detiene el hilo de actualización periódica."""
    global update_thread, stop_event
    if update_thread and update_thread.is_alive():
        stop_event.set()
        update_thread.join(timeout=10) # Esperar a que el hilo termine
        update_thread = None
        logger.info("El hilo de actualización periódica ha sido detenido.")
        return True
    return False
```

---

## Sección 4: Implementación del Frontend

Esta sección define la estructura de las plantillas HTML y la lógica de JavaScript del lado del cliente.

### 4.1. Plantilla Base (`src/templates/base.html`)

Esta es la plantilla principal de la que heredarán todas las demás. Define el layout general, la cabecera (`<head>`) y los scripts comunes.

**Lógica Clave a Implementar:**
1.  **Cargar desde CDN**: Incluir Bootstrap (CSS y JS), jQuery, DataTables y Font Awesome desde sus respectivas CDNs.
2.  **Bloques Jinja2**: Definir los bloques `{% block title %}`, `{% block head %}`, `{% block content %}` y `{% block scripts %}` para que las plantillas hijas puedan inyectar su contenido.
3.  **Navbar y Overlay**: Incluir un `_navbar.html` y un overlay de carga global.
4.  **Cargar `theme.js`**: Incluir el script para manejar el tema claro/oscuro.

```html
<!DOCTYPE html>
<html lang="es" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Bolsa App{% endblock %}</title>
    <!-- Dependencias CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/datatables.net-bs5/1.13.6/dataTables.bootstrap5.min.css">
    <link rel="icon" href="{{ url_for('static', filename='favicon.svg') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    {% block head %}{% endblock %}
</head>
<body>
    <div id="loading-overlay" class="loading-overlay">
        <div class="spinner-border text-primary" role="status"></div>
        <p id="loadingMessage" class="mt-3">Cargando...</p>
    </div>

    {% include '_navbar.html' %} {# La IA deberá crear un navbar básico #}

    <main class="container-fluid py-4">
        {% block content %}{% endblock %}
    </main>

    <!-- Dependencias JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.0/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/datatables.net/1.13.6/jquery.dataTables.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/datatables.net-bs5/1.13.6/dataTables.bootstrap5.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.0/socket.io.js"></script>
    
    <script src="{{ url_for('static', filename='theme.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### 4.2. Página del Dashboard (`src/templates/dashboard.html` y `src/static/dashboard.js`)

Esta es la página principal de la aplicación. Utiliza GridStack.js para un layout de widgets dinámico.

**4.2.1. Estructura HTML del Dashboard (`dashboard.html`)**

1.  **Heredar de `base.html`**.
2.  **Cargar Dependencias Adicionales**: En el bloque `head`, cargar Chart.js, su adaptador de fecha, y el CSS de GridStack.js.
3.  **Layout de GridStack**: En el bloque `content`, definir un contenedor principal con la clase `.grid-stack`.
4.  **Plantillas de Widgets**: Para cada widget (Portafolio, Noticias, Controles, etc.), definir su estructura HTML dentro de una etiqueta `<template>` con un `id` único (ej. `<template id="portfolioTemplate">`). El JavaScript usará estas plantillas.

**4.2.2. Lógica del Dashboard (`dashboard.js`)**

La IA debe crear un único archivo `dashboard.js` que maneje toda la lógica de esta página.

**Lógica Algorítmica de `dashboard.js`:**
1.  **Inicialización Principal**: Envolver toda la lógica en un `document.addEventListener('DOMContentLoaded', () => { ... });`.
2.  **Inicializar Socket.IO**: Conectar al servidor con `const socket = io();`.
3.  **Inicializar GridStack**:
    -   `const grid = GridStack.init();`
    -   Añadir listeners para eventos de `added`, `removed`, `change` para poder guardar el layout del usuario en `localStorage`.
4.  **Cargar Layout Guardado**:
    -   Al iniciar, comprobar si hay un layout guardado en `localStorage`.
    -   Si existe, cargarlo usando `grid.load(savedLayout)`. Si no, cargar un layout por defecto añadiendo los widgets iniciales.
5.  **Lógica de "Añadir Widget"**:
    -   Al hacer clic en el botón "Añadir Widget", obtener el `id` del widget desde la plantilla correspondiente y usar `grid.addWidget()` con el contenido clonado del `<template>`.
6.  **Lógica para Cada Widget**:
    -   **Gráficos (Chart.js)**:
        a. Obtener los elementos del formulario (símbolo, fechas, etc.) y el `<canvas>`.
        b. Al hacer clic en el botón "Graficar", construir la URL de la API (`/api/dashboard/chart-data` o similar) con los parámetros del formulario.
        c. Hacer un `fetch` a esa URL.
        d. Recibir el JSON y transformarlo al formato que espera Chart.js (`datasets`).
        e. Destruir el gráfico anterior si existe (`chart.destroy()`) y crear una nueva instancia de `Chart` con los nuevos datos.
    -   **Tablas (DataTables)**:
        a. Obtener el elemento `<table>`.
        b. Inicializarlo con `$('#myTable').DataTable({ ... })`.
        c. Para poblar la tabla, hacer un `fetch` a la API correspondiente (ej. `/api/portfolio/view`).
        d. Usar `table.clear().rows.add(data).draw()` para actualizar los datos.
7.  **Manejo de Eventos de Socket.IO**:
    -   Implementar listeners `socket.on('event_name', (data) => { ... })` para cada evento relevante (`update_complete`, `bot_error`, `kpi_update_progress`, etc.).
    -   Dentro de estos listeners, actualizar la UI correspondiente: mostrar una notificación, refrescar los datos de una tabla, actualizar un badge de estado, etc. 