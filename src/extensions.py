from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from src.config import REDIS_URL

# Crear la instancia de la base de datos
db = SQLAlchemy()

# Crear la instancia de Socket.IO, configurada para usar Redis como message queue
# Esto es esencial para que los workers de Celery puedan emitir eventos a los clientes.
socketio = SocketIO(message_queue=REDIS_URL)