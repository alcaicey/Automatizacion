import os

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
PROJECT_SRC_DIR = os.path.join(BASE_DIR, 'src')

# Directorio con los scripts de scraping
SCRIPTS_DIR = os.environ.get('BOLSA_SCRIPTS_DIR', os.path.join(PROJECT_SRC_DIR, 'scripts'))

# Directorio donde se guardan los logs y archivos JSON generados por el bot
LOGS_DIR = os.environ.get('BOLSA_LOGS_DIR', os.path.join(PROJECT_SRC_DIR, 'logs_bolsa'))
os.makedirs(LOGS_DIR, exist_ok=True)

# Credenciales de acceso
# Por defecto se utilizan cadenas vacías. Es obligatorio definirlas mediante las
# variables de entorno ``BOLSA_USERNAME`` y ``BOLSA_PASSWORD`` antes de ejecutar
# el bot.
USERNAME = os.environ.get('BOLSA_USERNAME', '')
PASSWORD = os.environ.get('BOLSA_PASSWORD', '')

# URLs y selectores utilizados por el bot
INITIAL_PAGE_URL = 'https://www.bolsadesantiago.com/plus_acciones_precios'
TARGET_DATA_PAGE_URL = 'https://www.bolsadesantiago.com/plus_acciones_precios'

USERNAME_SELECTOR = '#username'
PASSWORD_SELECTOR = '#password'
LOGIN_BUTTON_SELECTOR = '#kc-login'

API_PRIMARY_DATA_PATTERNS = [
    'https://www.bolsadesantiago.com/api/RV_ResumenMercado/getAccionesPrecios',
    'https://www.bolsadesantiago.com/api/Cuenta_Premium/getPremiumAccionesPrecios',
]

URLS_TO_INSPECT_IN_HAR_FOR_CONTEXT = [
    'https://www.bolsadesantiago.com/api/Comunes_User/getEstadoSesionUsuario',
    'https://www.bolsadesantiago.com/api/Indices/getIndicesPremium',
]

MIS_CONEXIONES_TITLE_SELECTOR = "h1:has-text('MIS CONEXIONES')"
CERRAR_TODAS_SESIONES_SELECTOR = "button:has-text('Cerrar sesión en todos los dispositivos')"

# Carpeta base de logs para la ejecución del bot
LOG_DIR = os.path.join(PROJECT_SRC_DIR, 'logs_bolsa')
os.makedirs(LOG_DIR, exist_ok=True)

# Configuración de base de datos
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/bolsa')
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
