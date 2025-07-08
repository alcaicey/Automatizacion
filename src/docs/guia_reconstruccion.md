# Guía Técnica de Reconstrucción del Proyecto

Este documento proporciona instrucciones técnicas detalladas para que un desarrollador (o una IA avanzada) pueda recrear el proyecto de monitoreo financiero desde cero.

---

## 1. Configuración del Entorno y Dependencias

### 1.1. Prerrequisitos del Sistema

-   **Python**: Versión 3.11 o superior.
-   **Node.js**: Necesario para gestionar las dependencias de testing del frontend.
-   **Docker y Docker Compose**: Para ejecutar la base de datos PostgreSQL/TimescaleDB en un contenedor.
-   **Git**: Para el control de versiones.

### 1.2. Dependencias del Backend (Python)

Crea un archivo `requirements.txt` en la raíz del proyecto con el siguiente contenido. Estas dependencias incluyen Flask, SQLAlchemy, Playwright, Socket.IO y las librerías de análisis de datos.

```txt
# Contenido de requirements.txt
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
```

### 1.3. Dependencias del Frontend (Node.js)

El frontend no tiene dependencias de producción. Las siguientes son para el entorno de desarrollo y pruebas. Crea un archivo `package.json`:

```json
{
  "name": "automatizacion-rebuild",
  "version": "1.0.0",
  "description": "Reconstrucción del proyecto de automatización financiera.",
  "main": "index.js",
  "scripts": {
    "test": "jest",
    "test:vite": "vitest"
  },
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

### 1.4. Base de Datos (Docker)

La base de datos se gestiona con Docker. Crea un archivo `docker-compose.yml`:

```yaml
version: '3.8'
services:
  db:
    image: timescale/timescaledb:latest-pg14
    container_name: bolsa-timescaledb
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: bolsa
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
```

### 1.5. Configuración del Entorno (Variables)

El proyecto requiere un archivo `.env` en la raíz para las variables de entorno:

```
# .env
BOLSA_USERNAME="tu_usuario_de_bolsa_santiago"
BOLSA_PASSWORD="tu_contraseña_de_bolsa_santiago"
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/bolsa"
FLASK_PORT=5000
```

### 1.6. Pasos de Instalación

1.  **Clonar Repositorio**: `git clone <url_del_repositorio>`
2.  **Entorno Virtual de Python**:
    ```bash
    python -m venv venv
    # En Windows: venv\Scripts\activate
    # En Linux/macOS: source venv/bin/activate
    ```
3.  **Instalar Dependencias de Python**: `pip install -r requirements.txt`
4.  **Instalar Navegadores de Playwright**:
    ```bash
    playwright install
    playwright install-deps
    ```
5.  **Instalar Dependencias de Node.js**: `npm install`
6.  **Iniciar Base de Datos**: `docker-compose up -d db`
7.  **Crear Tablas de la Base de Datos**: Se necesitará un script `create_tables.py` (se detallará más adelante) para ejecutar: `python create_tables.py`
8.  **Ejecutar la Aplicación**: `python src/main.py`

---
*Este es el final de la primera sección. Continuaré con la estructura del proyecto y el desglose de cada archivo.*

---

## 2. Estructura del Proyecto y Componentes Clave

La aplicación sigue una estructura modular estándar para proyectos Flask, separando la lógica, los datos y las vistas.

### 2.1. Estructura de Directorios

```
/
├── src/
│   ├── models/         # Define las tablas de la base de datos (SQLAlchemy).
│   ├── routes/         # Define los endpoints de la API y las rutas web (Blueprints).
│   ├── scripts/        # Lógica de negocio principal (bot, análisis, etc.).
│   ├── static/         # Archivos del frontend (JS, CSS, imágenes).
│   ├── templates/      # Plantillas HTML (Jinja2).
│   ├── utils/          # Funciones de ayuda y utilidades compartidas.
│   ├── config.py       # Configuración central de la aplicación.
│   ├── extensions.py   # Instancias de extensiones de Flask (db, socketio).
│   └── main.py         # Punto de entrada de la aplicación.
├── tests/              # Pruebas unitarias y de integración.
├── .env                # Archivo de variables de entorno (no versionado).
├── create_tables.py    # Script para inicializar la base de datos.
├── docker-compose.yml  # Configuración del contenedor de la base de datos.
├── package.json        # Dependencias de desarrollo del frontend.
└── requirements.txt    # Dependencias de Python del backend.
```

### 2.2. Componentes Principales del Backend

#### `src/main.py` - El Orquestador

Este es el punto de entrada que inicia la aplicación. Sus responsabilidades son:
1.  **Crear la App Flask**: Utiliza una función `create_app` para configurar la aplicación desde `config.py`.
2.  **Inicializar Extensiones**: Llama a `db.init_app(app)` y `socketio.init_app(app)`.
3.  **Gestionar el Hilo del Bot**:
    -   Crea un `asyncio.new_event_loop()` que se ejecutará en un hilo (`threading.Thread`) separado.
    -   **Importante**: Esto es para evitar que el bot asíncrono de Playwright bloquee el servidor web de Flask/Eventlet. El loop del bot se almacena en `app.bot_event_loop` para que otras partes de la aplicación puedan enviarle tareas.
4.  **Mapeo de Modelos para CRUD**: Itera sobre todos los modelos de SQLAlchemy y los registra en un diccionario `app.model_map`. Esto permite que una API de CRUD genérica funcione para cualquier tabla.
5.  **Registrar Rutas (Blueprints)**: Importa y registra todos los blueprints de `src/routes`, asignando prefijos de URL (ej. `/api`).
6.  **Iniciar el Servidor**: Utiliza `socketio.run(app, ...)` que por debajo usa `eventlet`, una configuración robusta y apta para producción que soporta WebSockets.

#### `src/config.py` - Configuración Centralizada

Este archivo carga las variables del archivo `.env` y define las configuraciones que la aplicación utilizará.
-   **Credenciales**: Carga `BOLSA_USERNAME` y `BOLSA_PASSWORD`.
-   **Base de Datos**: Define `SQLALCHEMY_DATABASE_URI`.
-   **URLs y Selectores del Bot**: Contiene constantes importantes como `TARGET_DATA_PAGE_URL` y los patrones de las APIs a interceptar (`API_PRIMARY_DATA_PATTERNS`). Esto centraliza los "números mágicos" del bot en un solo lugar.

#### `src/extensions.py` - Instancias Globales

Este archivo es clave para evitar importaciones circulares.
-   Define las instancias de las extensiones de Flask **sin asociarlas a una aplicación**.
  ```python
  # src/extensions.py
  from flask_sqlalchemy import SQLAlchemy
  from flask_socketio import SocketIO

  db = SQLAlchemy()
  socketio = SocketIO()
  ```
-   Cualquier archivo que necesite interactuar con la base de datos o Socket.IO puede importar `db` o `socketio` directamente desde aquí, en lugar de desde `main.py`. La vinculación con la app se hace en `main.py` con `db.init_app(app)`.

#### `create_tables.py` - Inicializador de la Base de Datos

Es un script simple que se ejecuta manualmente para crear el esquema de la base de datos.
-   Importa todos los modelos de `src/models`.
-   Crea una instancia mínima de la app Flask para establecer el contexto de la aplicación.
-   Llama a `db.create_all()` para que SQLAlchemy genere todas las tablas que no existan.

---

## 3. Capa de Datos: Modelos SQLAlchemy

Esta sección detalla todos los modelos de datos que la aplicación utiliza. Deben ser creados dentro del directorio `src/models/`.

### 3.1. `__init__.py` - Exposición de Modelos

Este archivo es crucial para que el resto de la aplicación pueda acceder a los modelos de forma sencilla y para definir qué se importa con `from src.models import *`.

```python
# src/models/__init__.py
from .user import User
from .stock_price import StockPrice
# ... (importar todos los demás modelos de la misma manera)
from .anomalous_event import AnomalousEvent

__all__ = [
    "User", "StockPrice", "Credential", "ColumnPreference", "StockFilter",
    "LastUpdate", "LogEntry", "Alert", "Portfolio", "FilteredStockHistory",
    "Dividend", "DividendColumnPreference", "StockClosing", "ClosingColumnPreference",
    "AdvancedKPI", "KpiSelection", "PromptConfig", "KpiColumnPreference",
    "PortfolioColumnPreference", "AnomalousEvent"
]
```

### 3.2. Modelos Principales de Datos

#### `stock_price.py`
Almacena los precios de las acciones en tiempo real. Es el modelo más importante para los datos de series temporales.

```python
# src/models/stock_price.py
from sqlalchemy import event, DDL
from src.extensions import db
from datetime import datetime, timezone

class StockPrice(db.Model):
    __tablename__ = 'stock_prices'
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
    __table_args__ = (db.PrimaryKeyConstraint('symbol', 'timestamp'), {})

# Evento para convertir la tabla a una Hypertable de TimescaleDB después de su creación
@event.listens_for(StockPrice.__table__, 'after_create')
def create_timescale_hypertable(target, connection, **kw):
    if connection.dialect.name == "postgresql":
        connection.execute(DDL("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
        connection.execute(DDL("SELECT create_hypertable('stock_prices', 'timestamp', if_not_exists => TRUE);"))
```

#### `stock_closing.py`
Guarda los datos del cierre bursátil del día anterior.

```python
# src/models/stock_closing.py
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
    __table_args__ = (db.PrimaryKeyConstraint('date', 'nemo'), {},)
```

#### `dividend.py`
Almacena la información de los dividendos.

```python
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
    # ... otras columnas ...
    __table_args__ = (db.UniqueConstraint('nemo', 'payment_date', 'description', name='uq_dividend'),)
```

### 3.3. Modelos de Análisis y Configuraciones

#### `anomalous_event.py`
Para los resultados del análisis de eventos anómalos.

```python
# src/models/anomalous_event.py
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
```

#### `credentials.py`, `stock_filter.py`, `column_preference.py`
Estos modelos guardan la configuración del usuario.

```python
# src/models/credentials.py
from src.extensions import db
class Credential(db.Model):
    __tablename__ = 'credentials'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

# src/models/stock_filter.py
from src.extensions import db
class StockFilter(db.Model):
    __tablename__ = 'stock_filters'
    id = db.Column(db.Integer, primary_key=True)
    codes_json = db.Column(db.Text, nullable=True)
    all = db.Column(db.Boolean, default=False)

# ... y así sucesivamente para todos los demás modelos ...
```

*(Nota para la IA: Se deben crear archivos separados para cada modelo como se muestra en la estructura de directorios, incluyendo `user.py`, `alert.py`, `portfolio.py`, `filtered_stock_history.py` y todas las tablas de preferencias de columnas. El código debe ser extraído de los archivos originales del proyecto analizado.)*

---

## 4. Lógica de Negocio y Servicios (`src/scripts/`)

Esta capa contiene el cerebro de la aplicación: el bot de automatización y los servicios de análisis.

### 4.1. El Orquestador del Bot: `bolsa_service.py`

Este script es el punto de entrada para la ejecución del bot. La función `run_bolsa_bot` es llamada desde la API para iniciar una actualización de datos.

**Lógica Clave:**
-   **Lock de Ejecución**: Utiliza un `asyncio.Lock` para asegurar que solo una instancia del bot se ejecute a la vez.
-   **Chequeo de Salud**: Llama a `perform_session_health_check` para validar la sesión antes de actuar.
-   **Bucle de Captura**: Intenta la captura de datos hasta 3 veces, manejando errores y recreando la página si es necesario.
-   **Almacenamiento**: Una vez que los datos son capturados y validados, llama a `store_prices_in_db` del módulo `db_io` para guardarlos.

```python
# src/scripts/bolsa_service.py
async def run_bolsa_bot(app=None, username=None, password=None, filtered_symbols: Optional[List[str]] = None, **kwargs) -> str | None:
    global _is_first_run_since_startup
    
    # Adquirir el lock para evitar ejecuciones simultáneas
    try:
        await asyncio.wait_for(_bot_running_lock.acquire(), timeout=0.1)
    except asyncio.TimeoutError:
        logger.warning("Se ignoró una nueva solicitud de ejecución del bot porque ya estaba en curso.")
        return "ignored_already_running"
    
    page = None
    try:
        # 1. Obtener la página y chequear la sesión
        page = await get_page()
        page = await perform_session_health_check(page, username, password)
        
        # ... Lógica de primera ejecución ...

        # 2. Bucle de intentos de captura
        max_attempts = 3
        market_time, raw_data = None, None
        for attempt in range(1, max_attempts + 1):
            # ... (manejo de página cerrada y lógica de reintento) ...
            market_time, raw_data = await _attempt_data_capture(page)
            if market_time and raw_data:
                break # Salir del bucle si es exitoso
        
        # ... (manejo de fallback de hora y errores de captura) ...

        # 3. Guardar en la base de datos
        with (app or current_app).app_context():
            store_prices_in_db(raw_data, market_time, app=app, filtered_symbols=filtered_symbols)
            save_filtered_comparison_history(market_timestamp=market_time, app=app)
            
        return "update_complete"

    except Exception as e:
        # ... (manejo de errores y logging) ...
    finally:
        # Liberar el lock
        if _bot_running_lock.locked():
             _bot_running_lock.release()
```

### 4.2. El Proceso de Login: `bot_login.py`

Este script maneja la autenticación en el sitio de la Bolsa de Santiago, con tácticas para parecer un usuario humano.

**Lógica Clave:**
-   **Simulación Humana**: `type_like_human` y `click_like_human` añaden pausas aleatorias.
-   **Manejo de Casos Borde**: Detecta y maneja páginas de CAPTCHA y de múltiples sesiones activas.
-   **Flujo Robusto**: Navega a través de varias páginas (landing -> login -> sso) para llegar al formulario de autenticación.

```python
# src/scripts/bot_login.py
async def auto_login(page: Page, username: str, password: str) -> Page:
    if not username or not password:
        raise LoginError("Credenciales no encontradas.")
    
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            # 1. Navegar a la página principal y detectar anti-bot
            await page.goto(BASE_URL, wait_until="networkidle", timeout=45000)
            if "validate.perfdrive.com" in page.url:
                # ... (lógica de espera y reintento) ...

            # 2. Navegar al formulario de login
            # ... (código para hacer clic en menús y botones) ...

            # 3. Rellenar credenciales y enviar
            await type_like_human(page.locator(USER_SEL), username)
            await type_like_human(page.locator(PASS_SEL), password)
            await click_like_human(page, page.locator("input[type='submit']"))
            
            # 4. Manejar página de sesiones activas
            if await _handle_active_sessions(page):
                continue # Reiniciar el flujo de login
            
            return page # Éxito

        except Exception as e:
            # ... (lógica de reintentos y manejo de errores) ...
```

### 4.3. Captura de Datos de Red: `bot_data_capture.py`

Este script se especializa en interceptar las respuestas de la API interna del sitio web.

**Lógica Clave:**
-   **Escucha de Red**: Utiliza `page.expect_response` para esperar una respuesta de red que coincida con un patrón de URL específico (definido en `config.py`).
-   **Captura Concurrente**: En `bolsa_service.py`, la captura de la hora y de los precios se lanza como tareas de asyncio concurrentes para mayor eficiencia.
-   **Validación**: Incluye una función simple para asegurar que el JSON capturado tiene la estructura esperada.

```python
# src/scripts/bot_data_capture.py
async def capture_premium_data_via_network(page: Page, logger_instance=None) -> Optional[Dict[str, Any]]:
    # ...
    def is_target_response(response: Response) -> bool:
        # API_PRIMARY_DATA_PATTERNS viene de config.py
        return response.status == 200 and any(p in response.url for p in API_PRIMARY_DATA_PATTERNS)
    try:
        async with page.expect_response(is_target_response, timeout=30000) as response_info:
            response = await response_info.value
        return await response.json()
    except Exception as e:
        # ...
        return None
```

### 4.4. Otros Servicios (`dividend_service.py`, `closing_service.py`, `drainer_service.py`)

Estos scripts siguen un patrón similar:
1.  **Navegan** a una página específica del sitio.
2.  **Interceptan** la respuesta de una API concreta.
3.  **Procesan** los datos JSON recibidos.
4.  **Almacenan** los datos en la base de datos, usando una estrategia de "reemplazo total" (para dividendos) o "upsert" (para cierres).
5.  El `drainer_service` es diferente: no captura datos externos, sino que **lee de la propia base de datos** (`stock_closings`) para realizar análisis estadísticos con `pandas` y guardar los resultados en `anomalous_events`. 

---

## 5. API y Rutas (`src/routes/`)

La capa de API es el punto de contacto entre el frontend y el backend. Utiliza Blueprints de Flask para mantener el código modular y organizado.

### 5.1. Estructura de los Blueprints

-   **`api_bp`**: El blueprint principal, prefijado en `/api`.
-   **`crud_bp`**: Un blueprint para la API de CRUD genérica, prefijado en `/api/crud`.
-   **Módulos de Rutas**: Archivos como `bot_routes.py`, `data_routes.py`, etc., que definen endpoints y se registran dentro de `api_bp`.

### 5.2. Endpoints Clave (`bot_routes.py`)

Estos endpoints controlan la ejecución de las tareas de fondo. Su diseño es asíncrono para no bloquear la interfaz de usuario.

**Patrón de Ejecución Asíncrona:**
1.  El endpoint de la API recibe la solicitud HTTP.
2.  Inicia una nueva tarea en un **hilo de fondo** (`threading.Thread`).
3.  Devuelve inmediatamente una respuesta `HTTP 202 Accepted` para indicar que la tarea ha comenzado.
4.  La tarea en el hilo ejecuta la lógica de negocio (a menudo llamando al loop de asyncio del bot con `run_coroutine_threadsafe`).
5.  Una vez que la tarea finaliza, utiliza `socketio.emit()` para enviar el resultado (éxito o error) directamente al cliente a través de WebSockets.

#### `POST /api/stocks/update`
Inicia el proceso principal de captura de precios de acciones.
-   **Lógica**: Llama a `run_bolsa_bot` en el hilo del bot.
-   **Filtros**: Lee la tabla `StockFilter` para pasar los símbolos filtrados por el usuario al bot.

#### `POST /api/dividends/update`
Inicia la actualización de los datos de dividendos.
-   **Lógica**: Llama a `dividend_service.compare_and_update_dividends`.

#### `POST /api/closing/update`
Inicia la actualización de los datos de cierre bursátil.
-   **Lógica**: Llama a `closing_service.update_stock_closings`.

#### `POST /api/kpis/update`
Orquesta la actualización de los KPIs avanzados (simulados por IA).
-   **Lógica**:
    1.  Consulta la tabla `KpiSelection` para obtener las acciones a analizar.
    2.  Llama al servicio de IA (`ai_financial_service.get_advanced_kpis`) para cada acción.
    3.  Guarda los resultados en la tabla `AdvancedKPI`.
    4.  Emite múltiples eventos de Socket.IO para informar el progreso al frontend.

#### `GET /api/bot-status`
Devuelve el estado actual del bot.
-   **Lógica**: Comprueba los `locks` de ejecución para saber si hay una tarea en curso.
-   **Uso**: El frontend utiliza este endpoint para deshabilitar los botones de "Actualizar" y evitar ejecuciones duplicadas.

### 5.3. Endpoints de Datos (`data_routes.py`)

Estos endpoints son responsables de servir los datos ya procesados al frontend. Son en su mayoría llamadas de lectura a la base de datos.

-   **`GET /api/data`**: Devuelve los últimos precios de las acciones, aplicando los filtros del usuario. Llama a `db_io.filter_stocks`.
-   **`GET /api/comparison`**: Devuelve una comparación entre los dos últimos snapshots de datos. Llama a `db_io.compare_last_two_db_entries`.
-   **`GET /api/logs`**: Sirve las entradas de la tabla `log_entries`.
-   ... y otros endpoints para obtener dividendos, datos de cierre, etc.

### 5.4. API de CRUD Genérica (`crud_api.py`)

Esta es una pieza de ingeniería notable en el proyecto. Proporciona endpoints `GET`, `POST`, `PUT`, `DELETE` que pueden operar sobre *cualquier* modelo de la base de datos sin necesidad de código específico.

-   **`GET /api/crud/<table_name>`**: Lista todos los registros de una tabla.
-   **`POST /api/crud/<table_name>`**: Crea un nuevo registro en la tabla.
-   **Lógica Clave**: Utiliza el `app.model_map` (creado en `main.py`) para encontrar la clase del modelo SQLAlchemy correspondiente al `<table_name>` de la URL. Luego, utiliza los métodos de SQLAlchemy (`.query.all()`, `.add()`, etc.) para realizar la operación. Esto hace que añadir un mantenedor para una nueva tabla en el frontend sea trivial. 

---

## 6. Frontend (`src/templates/` y `src/static/`)

El frontend está construido con una combinación de plantillas **Jinja2** servidas por Flask, y **JavaScript "vanilla"** organizado en módulos. No utiliza un framework pesado como React o Vue.

### 6.1. Plantillas HTML (`src/templates/`)

La estructura se basa en la herencia de plantillas de Jinja2.

-   **`base.html`**: Es la plantilla raíz.
    -   Importa las librerías CSS y JS globales (Bootstrap, FontAwesome, jQuery, DataTables, Socket.IO, GridStack.js).
    -   Define la estructura básica de la página, incluyendo una barra de navegación (`_navbar.html`) y un bloque de contenido principal (`{% block content %}{% endblock %}`).
-   **`dashboard.html`**: Hereda de `base.html`.
    -   Define la estructura de la cuadrícula (`grid-stack`) donde se colocarán los widgets.
    -   Importa todos los scripts JavaScript específicos de la aplicación (`uiManager.js`, `portfolioManager.js`, `app.js`, etc.).
-   **Otras Plantillas**: Páginas como `historico.html`, `logs.html`, etc., también heredan de `base.html` y definen su propio contenido.
-   **`_modals.html`**: Contiene el HTML para todas las ventanas modales de la aplicación, que se incluyen en las páginas que las necesitan.

### 6.2. Arquitectura de JavaScript (`src/static/`)

El frontend está orquestado por `app.js` y dividido en módulos (patrón similar a "singletons" u objetos globales) con responsabilidades claras.

-   **`app.js`**: El punto de entrada principal.
    -   Instancia y coordina todos los "managers".
    -   Mantiene el estado global de la aplicación (aunque gran parte del estado se delega a los managers).
    -   Inicializa los manejadores de eventos y la carga inicial de datos.

-   **`uiManager.js`**: Responsable de todas las manipulaciones del DOM.
    -   Muestra/oculta overlays de carga.
    -   Actualiza el texto y estado de los botones.
    -   Renderiza tablas usando la librería **DataTables**.
    -   Proporciona funciones de formato de números, monedas y porcentajes.

-   **Managers de Widgets (`portfolioManager.js`, `dividendManager.js`, etc.)**:
    -   Cada "manager" controla un widget o una sección de la UI.
    -   **Lógica**: Contiene la lógica para buscar sus propios datos a través de la API, procesarlos y prepararlos para la visualización.
    -   **Estado**: Mantiene su propio estado interno (ej. las preferencias de columnas del portafolio).
    -   **Renderizado**: Llama a `uiManager` para renderizar su tabla o contenido.

-   **`eventHandlers.js`**: Centraliza los manejadores de eventos.
    -   Define qué sucede cuando un usuario hace clic en "Actualizar Ahora" (llama a la API `/api/stocks/update`), cambia un filtro, etc.

-   **`botStatusManager.js`**: Escucha los eventos de Socket.IO relacionados con el bot (`bot_error`, `new_data`) y actualiza la UI correspondientemente (ej. mostrando un mensaje de estado).

-   **`dashboardLayout.js`**: Gestiona la disposición de los widgets.
    -   Utiliza la librería **GridStack.js** para crear un dashboard modular donde los widgets se pueden añadir, eliminar y arrastrar.
    -   Guarda el layout del usuario en `localStorage` para persistir la personalización.

### 6.3. Flujo de Comunicación Frontend-Backend

1.  **Carga Inicial**:
    -   El usuario carga una página (ej. `/dashboard`).
    -   `app.js` se inicializa y los managers de los widgets llaman a sus respectivos endpoints de la API (`/api/data`, `/api/portfolio`, etc.) para obtener el estado inicial.
2.  **Acción del Usuario (Ej. "Actualizar")**:
    -   El usuario hace clic en el botón.
    -   `eventHandlers.js` captura el evento y realiza una llamada `POST` a `/api/stocks/update`.
    -   El backend devuelve `HTTP 202 Accepted` y el frontend muestra un estado de "cargando".
3.  **Actualización en Tiempo Real**:
    -   El bot termina su trabajo en el backend.
    -   El backend emite un evento de Socket.IO (ej. `socketio.emit('new_data', ...)`).
    -   El cliente de Socket.IO en el frontend recibe el evento.
    -   El `botStatusManager` (o el manager correspondiente) captura el evento y vuelve a llamar a la API para obtener los datos frescos, o actualiza la UI directamente con los datos del evento si vienen incluidos.
    -   Se actualizan las tablas y la UI sin necesidad de recargar la página.

---

Este documento ahora contiene una guía técnica completa para la reconstrucción del proyecto, abarcando desde la configuración inicial hasta los detalles de implementación del backend y el frontend. 