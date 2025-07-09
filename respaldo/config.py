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
USERNAME = os.environ.get('BOLSA_USERNAME', 'postgres')
PASSWORD = os.environ.get('BOLSA_PASSWORD', 'postgres')

# Puerto para el servidor Flask
PORT = int(os.environ.get('FLASK_PORT', 5000))

# URLs y selectores del bot
TARGET_DATA_PAGE_URL = 'https://www.bolsadesantiago.com/plus_acciones_precios'

API_PRIMARY_DATA_PATTERNS = [
    'api/RV_ResumenMercado/getAccionesPrecios',
    'api/Cuenta_Premium/getPremiumAccionesPrecios',
]

# Configuración de base de datos
# DATABASE_URL por defecto para docker-compose
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

# Configuración de Socket.IO
# (No se necesita configuración explícita aquí si se usa el modo de desarrollo)

# Configuración de Celery
REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL