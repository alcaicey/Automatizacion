# tests/test_views.py
import re
from playwright.sync_api import Page, expect

def test_home_page(page: Page):
    """
    Prueba que la página de inicio se carga correctamente, tiene el título
    correcto y muestra el widget de estado del bot.
    """
    # Ir a la página de inicio
    page.goto("/")

    # 1. Verificar que el título de la página sea correcto
    expect(page).to_have_title(re.compile("Dashboard de Acciones"))

    # 2. Verificar que el widget de "Estado del Bot" es visible
    bot_status_widget = page.get_by_text("Estado del Bot")
    expect(bot_status_widget).to_be_visible()

def test_historico_page(page: Page):
    """
    Prueba que la página de histórico se carga correctamente y muestra su título.
    """
    page.goto("/historico")
    expect(page).to_have_title(re.compile("Histórico de Cargas"))
    heading = page.locator("h1")
    expect(heading).to_have_text(re.compile("Histórico de Cargas"))

def test_logs_page(page: Page):
    """
    Prueba que la página de logs se carga correctamente y muestra su título.
    """
    page.goto("/logs")
    expect(page).to_have_title(re.compile("Logs del Sistema"))
    heading = page.locator("h1")
    expect(heading).to_have_text(re.compile("Logs del Sistema"))

def test_indicadores_page(page: Page):
    """
    Prueba que la página de indicadores se carga correctamente y muestra su título.
    """
    page.goto("/indicadores")
    expect(page).to_have_title(re.compile("Indicadores del Mercado"))
    heading = page.locator("h1")
    expect(heading).to_have_text(re.compile("Indicadores del Mercado"))

def test_stock_filter_flow(page: Page):
    """
    Prueba el flujo completo de filtrar acciones en el dashboard.
    """
    page.goto("/")

    # 1. Abrir el menú para añadir widgets y hacer clic en la opción de controles
    add_widget_button = page.get_by_role("button", name="Añadir Widget")
    expect(add_widget_button).to_be_enabled()
    add_widget_button.click()

    # Esperar a que el enlace sea visible y esté habilitado antes de hacer clic
    config_link = page.get_by_role("link", name="Configuración y Acciones")
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

def test_historico_filter_flow(page: Page):
    """
    Prueba el flujo de filtrar la comparación en la página de histórico.
    """
    # Navegar a la página. La página hace una llamada a /api/filters para cargar
    # el estado inicial del formulario.
    page.goto("/historico")

    # Esperar a que la llamada inicial a la API de filtros se complete.
    # Esto asegura que el formulario se haya inicializado antes de interactuar con él.
    page.wait_for_response("**/api/filters")  # type: ignore

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

def test_logs_search_flow(page: Page):
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
    
    page.goto("/logs")

    # Esperar a que la tabla se llene con los datos de prueba
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

def test_dividend_filter_flow(page: Page):
    """
    Prueba el flujo de filtrar dividendos por fecha en la página de indicadores.
    """
    page.goto("/indicadores")

    # La página hace varias llamadas para inicializarse. Esperamos la de dividendos.
    page.wait_for_response("**/api/dividends?**")  # type: ignore

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

def test_dashboard_fully_loads(page: Page):
    """
    Prueba que el dashboard se carga completamente, lo que implica
    que el overlay de 'Cargando...' desaparece y los widgets principales
    son visibles e interactivos.
    """
    page.goto("/")

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