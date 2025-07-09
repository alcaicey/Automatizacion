# src/socket_events.py
import logging
from flask import request
from .extensions import socketio

# Importamos la función de lógica de negocio desde su módulo original
from .routes.api.bot_routes import _start_bot_process

logger = logging.getLogger(__name__)

@socketio.on('connect')
def handle_connect():
    """Esta función se ejecuta cada vez que un cliente se conecta."""
    logger.info(f"✅ Cliente conectado al WebSocket con sid: {request.sid}") # type: ignore

@socketio.on('disconnect')
def handle_disconnect():
    """Esta función se ejecuta cuando un cliente se desconecta."""
    logger.info(f"🔌 Cliente desconectado del WebSocket con sid: {request.sid}") # type: ignore

@socketio.on('run_bot_manually')
def handle_run_bot_manually():
    """
    Manejador para el evento de Socket.IO que solicita una ejecución manual del bot.
    """
    logger.info(f"[Socket.IO] ¡Evento 'run_bot_manually' recibido del cliente {request.sid}!") # type: ignore
    
    # Llama a la lógica centralizada que inicia el bot
    success = _start_bot_process()
    
    # Emite una respuesta inmediata para confirmar la recepción
    if success:
        socketio.emit('bot_status_update', 
                      {'status': 'running', 'message': 'Servidor recibió solicitud de actualización.'},
                      to=request.sid) # type: ignore
    else:
        socketio.emit('bot_status_update',
                      {'status': 'idle', 'message': 'El servidor recibió la solicitud, pero ya hay un proceso en curso.'},
                      to=request.sid) # type: ignore 