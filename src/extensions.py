from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# Instancia única de SQLAlchemy que será usada por toda la aplicación.
db = SQLAlchemy()

# Instancia única de SocketIO.
socketio = SocketIO()