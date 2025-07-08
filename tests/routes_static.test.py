import pytest

def test_static_app_js_is_served(app):
    """
    Verifica que el archivo JavaScript principal de la aplicación estática se sirve correctamente.
    """
    with app.test_client() as client:
        response = client.get('/static/js/app.js')
        assert response.status_code == 200, "El archivo estático app.js no se pudo encontrar (código de estado no es 200)"
        assert 'application/javascript' in response.content_type, "El tipo de contenido para app.js no es JavaScript"

def test_static_css_is_served(app):
    """
    Verifica que el archivo CSS principal se sirve correctamente.
    """
    with app.test_client() as client:
        response = client.get('/static/styles.css')
        assert response.status_code == 200, "El archivo estático styles.css no se pudo encontrar (código de estado no es 200)"
        assert 'text/css' in response.content_type, "El tipo de contenido para styles.css no es CSS" 