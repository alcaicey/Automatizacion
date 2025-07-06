import pytest
import threading
from src.main import create_app
from src.extensions import db

# Registrar el plugin de Playwright
pytest_plugins = "playwright"


@pytest.fixture(scope="session")
def app():
    """Crea una instancia de la aplicación Flask para toda la sesión de pruebas."""
    app = create_app(testing=True)
    app_context = app.app_context()
    app_context.push()
    db.create_all()
    yield app
    db.drop_all()
    app_context.pop()


@pytest.fixture(scope="session")
def live_server(app):
    """Inicia un servidor Flask en vivo en un hilo separado."""
    server = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000})
    server.daemon = True
    server.start()
    yield "http://localhost:5000"
    # El servidor se detendrá cuando el proceso de prueba principal termine


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, live_server):
    """Proporciona la URL base del servidor en vivo a Playwright."""
    return {
        **browser_context_args,
        "base_url": live_server,
        "ignore_https_errors": True,
    }
