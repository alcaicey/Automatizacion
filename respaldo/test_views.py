# tests/test_views.py
import pytest
import re
from playwright.sync_api import Page, expect, APIResponse
from typing import cast

# Marcar todos los tests en este archivo como 'slow'
pytestmark = pytest.mark.slow
# @pytest.mark.playwright 

def test_home_page(page: Page, live_server):
    """
    Prueba que la página de inicio se carga correctamente, tiene el título
    correcto y muestra el widget de estado del bot.
    """
    page.goto(live_server.url)
    expect(page).to_have_title(re.compile("Monitor de Acciones"))
    expect(page.locator("#bot-status-widget")).to_be_visible()

def test_historico_page(page: Page, live_server):
    """
    Prueba que la página de histórico se carga correctamente y muestra su título.
    """
    page.goto(live_server.url + "/historico")
    expect(page).to_have_title(re.compile("Histórico de Cargas"))
    heading = page.locator("h1")
    expect(heading).to_have_text(re.compile("Histórico de Cargas"))

def test_logs_page(page: Page, live_server):
    """
    Prueba que la página de logs se carga correctamente y muestra su título.
    """
    page.goto(live_server.url + "/logs")
    expect(page).to_have_title(re.compile("Logs del Sistema"))
    heading = page.locator("h1")
    expect(heading).to_have_text(re.compile("Logs del Sistema"))

def test_indicadores_page(page: Page, live_server):
    """
    Prueba que la página de indicadores se carga correctamente y muestra su título.
    """
    page.goto(live_server.url + "/indicadores")
    expect(page).to_have_title(re.compile("Indicadores del Mercado"))
    heading = page.locator("h1")
    expect(heading).to_have_text(re.compile("Indicadores del Mercado"))

def test_stock_filter_flow(page: Page, live_server):
    """
    Prueba el flujo completo de filtrar acciones en el dashboard.
    """
    page.goto(live_server.url)

    # 1. Abrir el menú para añadir widgets y hacer clic en la opción de controles
    add_widget_button = page.get_by_role("button", name="Añadir Widget")
    expect(add_widget_button).to_be_enabled()
    add_widget_button.click()

    # Esperar a que el menú desplegable esté visible
    page.wait_for_selector(".dropdown-menu.show")
    
    # Esperar a que el enlace sea visible y esté habilitado antes de hacer clic
    config_link = page.get_by_text("Configuración y Acciones")
    expect(config_link).to_be_visible()
    expect(config_link).to_be_enabled()
    config_link.click()

    # Esperar a que el formulario de filtro sea visible y su botón esté listo
    stock_filter_form = page.locator("#stockFilterForm")
    expect(stock_filter_form).to_be_visible()
    apply_button = stock_filter_form.get_by_role("button", name="Aplicar")
    expect(apply_button).to_be_enabled()

    # 2. Rellenar el formulario de filtro
    form_input = stock_filter_form.locator('input[placeholder="COPEC"]')
    form_input.fill("TEST_STOCK")

    # 3. Interceptar la petición a la API y verificar su contenido
    with page.expect_request("**/api/data/filter", timeout=5000) as request_info:
        apply_button.click()
    
    request = request_info.value
    assert request.method == "POST"
    assert request.post_data_json == {"stocks": ["TEST_STOCK"]}

def test_historico_filter_flow(page: Page, live_server):
    """
    Prueba el flujo de filtrar la comparación en la página de histórico.
    """
    # Navegar a la página. La página hace una llamada a /api/filters para cargar
    # el estado inicial del formulario.
    page.goto(live_server.url + "/historico")

    # Usar el context manager correcto para esperar la respuesta
    with page.expect_response("**/api/filters") as response_info:
        page.goto(live_server.url + "/historico")
    
    response = response_info.value
    assert response.ok

    # Esperar a que el formulario sea visible y su botón esté listo
    filter_form = page.locator("#stockFilterForm")
    expect(filter_form).to_be_visible()
    apply_button = filter_form.get_by_role("button", name="Aplicar Filtro")
    expect(apply_button).to_be_enabled()

    # Desmarcar la casilla "Todas" para que el filtro por código se aplique
    all_stocks_checkbox = filter_form.locator("#allStocksCheck")
    expect(all_stocks_checkbox).to_be_checked()
    all_stocks_checkbox.uncheck()

    # Rellenar el primer campo de filtro
    filter_form.locator('input.stock-code').first.fill("TESTCODE")

    # Interceptar la llamada POST que guarda las preferencias del filtro
    with page.expect_request("**/api/filters", timeout=5000) as request_info:
        apply_button.click()

    request = request_info.value
    assert request.method == "POST"
    assert request.post_data_json == {"codes": ["TESTCODE"], "all": False}

def test_logs_search_flow(page: Page, live_server):
    """
    Prueba el flujo de búsqueda en la página de logs.
    Como el filtrado es en el cliente, se simula una respuesta de la API
    y se verifica que el DOM de la tabla se actualiza.
    """
    # Datos de prueba para simular la respuesta de la API
    mock_logs = [
        {"timestamp": "2023-10-27 10:00:00", "level": "INFO", "message": "Iniciando sistema"},
        {"timestamp": "2023-10-27 10:00:01", "level": "INFO", "message": "Conexión exitosa"},
        {"timestamp": "2023-10-27 10:00:02", "level": "ERROR", "message": "Fallo en el módulo X"}
    ]

    # Interceptar la llamada a la API de logs y devolver los datos de prueba
    page.route("**/api/logs", lambda route: route.fulfill(status=200, json=mock_logs))
    
    page.goto(live_server.url + "/logs")

    # Esperar a que el contenedor de la tabla esté presente antes de buscar texto
    page.wait_for_selector('#logsTableBody')
    expect(page.get_by_text("Iniciando sistema")).to_be_visible()
    expect(page.get_by_text("Conexión exitosa")).to_be_visible()
    expect(page.get_by_text("Fallo en el módulo X")).to_be_visible()

    # Escribir en el campo de búsqueda para filtrar
    search_input = page.locator("#searchInput")
    expect(search_input).to_be_enabled()
    search_input.fill("exitosa")

    # Verificar que solo la fila correcta es visible y las otras no
    expect(page.get_by_text("Conexión exitosa")).to_be_visible()
    expect(page.get_by_text("Iniciando sistema")).not_to_be_visible()
    expect(page.get_by_text("Fallo en el módulo X")).not_to_be_visible()

def test_dividend_filter_flow(page: Page, live_server):
    """
    Prueba el flujo de filtrar dividendos por fecha en la página de indicadores.
    """
    page.goto(live_server.url + "/indicadores")

    # Usar el context manager correcto para esperar la respuesta
    with page.expect_response("**/api/dividends?*") as response_info:
        page.goto(live_server.url + "/indicadores")
    
    response = response_info.value
    assert response.ok

    # Esperar a que el formulario de filtro de dividendos sea visible
    start_date_input = page.locator("#dividendStartDate")
    end_date_input = page.locator("#dividendEndDate")
    apply_button = page.locator("#applyDividendFilters")

    expect(start_date_input).to_be_enabled()
    expect(end_date_input).to_be_enabled()
    expect(apply_button).to_be_enabled()

    # Rellenar las fechas
    start_date_input.fill("2024-01-01")
    end_date_input.fill("2024-03-31")

    # Interceptar la llamada GET a la API de dividendos
    with page.expect_request("**/api/dividends?**", timeout=5000) as request_info:
        apply_button.click()

    request = request_info.value
    assert request.method == "GET"
    
    # Verificar que los parámetros de la URL son correctos
    url = request.url
    assert "start_date=2024-01-01" in url
    assert "end_date=2024-03-31" in url

def test_dashboard_fully_loads(page: Page, live_server):
    """
    Prueba que el dashboard se carga completamente, lo que implica
    que el overlay de 'Cargando...' desaparece y los widgets principales
    son visibles e interactivos.
    """
    page.goto(live_server.url)

    # 1. El overlay de "Cargando..." debe desaparecer.
    #    Le damos un tiempo de espera generoso (e.g., 15 segundos) porque могут
    #    ocurrir llamadas a la red y procesos en segundo plano.
    loading_overlay = page.locator("#loading-overlay")
    expect(loading_overlay).not_to_be_visible(timeout=15000)

    # 2. Una vez que la carga finaliza, el botón "Añadir Widget" debe
    #    ser visible y estar habilitado, indicando que la UI está lista.
    add_widget_button = page.get_by_role("button", name="Añadir Widget")
    expect(add_widget_button).to_be_visible()
    expect(add_widget_button).to_be_enabled() 


def test_db_connection_button(page: Page, live_server):
    """
    Testea que el botón 'Probar Conexión DB' en el dashboard
    realiza una llamada a la API y recibe una respuesta exitosa.
    """
    page.goto(f"{live_server.url}/dashboard")

    # Esperar a que el botón de prueba de conexión a la BD sea visible
    expect(page.locator("button#test-connection-db")).to_be_visible()

    # Hacer clic en el botón y esperar la respuesta de la API
    with page.expect_response(re.compile(r"/api/system/status$")) as response_info:
        page.click("button#test-connection-db")
    
    response = response_info.value
    assert response.ok


def test_login_flow_successful(page: Page, live_server):
    """
    Simula un flujo de login exitoso.
    """
    page.goto(f"{live_server.url}/login")

    # Rellenar el formulario
    page.fill("input[name='username']", "testuser")
    page.fill("input[name='password']", "testpassword")

    # Esperar la respuesta de la API de login
    with page.expect_response(re.compile(r"/api/user/login$")) as response_info:
        page.click("button[type=submit]")

    response = response_info.value
    assert response.ok
    
    # Verificar que se redirige al dashboard
    expect(page).to_have_url(re.compile(r"/dashboard$"))
    expect(page.locator("h1")).to_contain_text("Dashboard") 