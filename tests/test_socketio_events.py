import pytest
from flask_socketio import SocketIOTestClient
from src.extensions import socketio
import time

@pytest.fixture
def socketio_client(app):
    """
    Crea un cliente de prueba de Socket.IO para interactuar con
    los eventos del servidor en un entorno de prueba.
    """
    # El 'app' fixture ya está en el contexto de la aplicación,
    # por lo que podemos usarlo directamente.
    return SocketIOTestClient(app, socketio)

def test_socketio_connection(socketio_client):
    """
    Verifica que un cliente de Socket.IO pueda conectarse exitosamente al servidor.
    """
    assert socketio_client.is_connected()
    print("Cliente de Socket.IO conectado exitosamente.")

def test_manual_update_event(socketio_client):
    """
    Simula el envío del evento 'manual_update' desde el cliente al servidor
    y verifica que el servidor lo recibe.
    """
    # Nos aseguramos de que el cliente esté conectado antes de emitir un evento.
    assert socketio_client.is_connected()

    # Emitimos el evento 'manual_update'. No necesitamos pasar datos para este evento.
    socketio_client.emit('manual_update')

    # Esperamos un momento para que el backend tenga tiempo de procesar el evento
    # y emitir una respuesta. Aumentamos a 2 segundos para más fiabilidad.
    time.sleep(2)

    # Obtenemos la lista de eventos recibidos por el cliente.
    received = socketio_client.get_received()

    # Verificamos si algún evento en la lista es el 'status_update' que esperamos.
    assert any(event['name'] == 'status_update' for event in received), \
        "El servidor no emitió un 'status_update' en respuesta a 'manual_update'" 