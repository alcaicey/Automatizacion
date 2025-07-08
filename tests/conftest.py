# tests/conftest.py
import pytest
import sys
import os
import threading
from werkzeug.serving import make_server
import socket
# Eliminar gevent, ya no se usa.
# from gevent.pywsgi import WSGIServer
# from geventwebsocket.handler import WebSocketHandler
import pytest
from playwright.sync_api import Playwright, Browser, Page
from typing import Generator

# Añadir el directorio 'src' explícitamente al sys.path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

# Ahora las importaciones desde 'src' deberían funcionar
from src.app import create_app
from src.extensions import db, socketio

# (imports de blueprints)
from src.routes.errors import errors_bp
from src.routes.user import user_bp
from src.routes.api import api_bp
from src.routes.crud_api import crud_bp
from src.routes.architecture import architecture_bp

# 1. FIX: Custom LiveServer implementation to avoid pickling errors on Windows.
class ThreadedLiveServer:
    """
    Runs a Flask app in a separate thread using eventlet,
    mimicking the production environment to ensure WebSockets work during tests.
    """
    def __init__(self, app, port=5000):
        self._app = app
        # Find an open port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        self.port = s.getsockname()[1]
        s.close()

        # Usar socketio.run en un hilo para alinear con main.py (usa eventlet)
        self._thread = threading.Thread(
            target=lambda: socketio.run(
                self._app, host='localhost', port=self.port, debug=False
            )
        )
        self._thread.daemon = True

    @property
    def app(self):
        """The Flask application object."""
        return self._app

    def start(self):
        self._thread.start()

    def stop(self):
        # El servidor eventlet iniciado con socketio.run() no tiene un método stop() limpio.
        # El hilo daemon se terminará cuando pytest finalice.
        pass

    @property
    def url(self):
        return f'http://localhost:{self.port}'

@pytest.fixture(scope="session")
def app():
    """Crea una instancia de la aplicación Flask para las pruebas."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SERVER_NAME": "localhost.local"
    })

    # La inicialización de la BD y los blueprints ya ocurre dentro de create_app.
    # No es necesario registrar BPs ni llamar a db.init_app() aquí.
    
    with app.app_context():
        # Aunque create_app ya hace un create_all, en el contexto de testing
        # con una BD en memoria, nos aseguramos de que esté limpio.
        db.drop_all()
        db.create_all()
        yield app

@pytest.fixture(scope="session")
def live_server(app):
    """
    Replaces the default pytest-flask live_server with our custom
    thread-based implementation.
    """
    server = ThreadedLiveServer(app)
    server.start()
    yield server
    server.stop()

@pytest.fixture(scope="session")
def base_url(live_server):
    """
    Provides the base URL for Playwright tests, powered by our
    custom threaded live_server.
    """
    return live_server.url

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Fuerza la ejecución de los tests en modo headless."""
    return {
        **browser_type_launch_args,
        "headless": True,
    }

@pytest.fixture(scope="session")
def browser(
    browser_type_launch_args: dict,
    playwright: Playwright,
    browser_name: str,
) -> Generator[Browser, None, None]:
    """
    Crea una instancia del navegador (ej. Chromium) una sola vez por sesión
    para mejorar el rendimiento.
    """
    browser = playwright[browser_name].launch(**browser_type_launch_args)
    yield browser
    browser.close()

@pytest.fixture
def page(browser: Browser, base_url: str) -> Generator[Page, None, None]:
    """
    Crea un nuevo contexto y una nueva página para cada test,
    asegurando el aislamiento, pero reusando la instancia del navegador.
    """
    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    yield page
    context.close()
