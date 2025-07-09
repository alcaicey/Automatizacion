from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# Crear la instancia de la base de datos
db = SQLAlchemy()

# Crear la instancia de Socket.IO, configurada para usar Redis como message queue
# Esto es esencial para que los workers de Celery puedan emitir eventos a los clientes.
socketio = SocketIO(message_queue='redis://127.0.0.1:6379/0')