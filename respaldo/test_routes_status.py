import pytest
from flask.testing import FlaskClient

# Lista de rutas que se espera que existan y devuelvan un 200 OK
# Se excluyen las rutas que requieren parámetros o lógica más compleja
# que se probará en tests de integración específicos.
ENDPOINTS = [
    '/',
    '/dashboard',
    '/historico',
    '/indicadores',
    '/logs',
    '/mantenedores',
    # '/login',
    # '/favicon.ico',
    # '/api/system/status',
    # '/api/portfolio/data',
    # '/api/config/prompt',
    # '/arquitectura/diagrama.png' # Esta es dinámica, se prueba por separado
]

@pytest.mark.parametrize('endpoint', ENDPOINTS)
def test_all_routes_return_200(app, endpoint):
    """
    Test parametrizado para verificar que todas las rutas principales
    devuelven un código de estado 200 OK.
    """
    # El fixture 'app' nos da una instancia de la app de Flask configurada para tests
    client: FlaskClient = app.test_client()
    
    # Realizar una petición GET a la ruta
    response = client.get(endpoint)
    
    # Verificar que el código de estado sea 200
    assert response.status_code == 200, f"La ruta {endpoint} devolvió {response.status_code} en lugar de 200" 