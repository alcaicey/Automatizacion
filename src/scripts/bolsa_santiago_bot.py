from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
import time
import json
import logging
from datetime import datetime
import os
import random
import argparse

from src.config import (
    LOGS_DIR,
    INITIAL_PAGE_URL,
    TARGET_DATA_PAGE_URL,
    USERNAME,
    PASSWORD,
    USERNAME_SELECTOR,
    PASSWORD_SELECTOR,
    LOGIN_BUTTON_SELECTOR,
    API_PRIMARY_DATA_PATTERNS,
    URLS_TO_INSPECT_IN_HAR_FOR_CONTEXT,
    MIS_CONEXIONES_TITLE_SELECTOR,
    CERRAR_TODAS_SESIONES_SELECTOR,
)

# Importar la función de análisis ubicada en src.scripts
from src.scripts.har_analyzer import analyze_har_and_extract_data

# --- Configuración de Logging Global ---
LOG_FILENAME = ""
# Archivo HAR con nombre fijo para capturas de red
HAR_FILENAME = os.path.join(LOGS_DIR, "network_capture.har")
OUTPUT_ACCIONES_DATA_FILENAME = ""
ANALYZED_SUMMARY_FILENAME = ""
# Timestamp para nombrar archivos generados en cada ejecución
TIMESTAMP_NOW = ""

# Controla si el script se ejecuta en modo no interactivo
NON_INTERACTIVE = os.getenv("BOLSA_NON_INTERACTIVE") == "1"
# User-Agent reutilizado para todos los contextos
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

logger_instance_global = logging.getLogger(__name__)
# --- Fin Configuración de Logging ---

# --- CONFIGURACIÓN ---
# La mayoría de parámetros estáticos se obtienen desde src.config

def validate_credentials():
    """Comprueba que las credenciales estén definidas en el entorno."""
    if not USERNAME or not PASSWORD:
        raise ValueError(
            "Missing credentials: set BOLSA_USERNAME and BOLSA_PASSWORD"
        )

# --- FIN DE LA CONFIGURACIÓN ---

def configure_run_specific_logging(logger_to_configure):
    global LOG_FILENAME, OUTPUT_ACCIONES_DATA_FILENAME, ANALYZED_SUMMARY_FILENAME, TIMESTAMP_NOW
    
    for handler in list(logger_to_configure.handlers):
        logger_to_configure.removeHandler(handler)
        handler.close()

    TIMESTAMP_NOW = datetime.now().strftime('%Y%m%d_%H%M%S')
    LOG_FILENAME = os.path.join(LOGS_DIR, f"bolsa_bot_log_{TIMESTAMP_NOW}.txt")
    OUTPUT_ACCIONES_DATA_FILENAME = os.path.join(LOGS_DIR, f"acciones-precios-plus_{TIMESTAMP_NOW}.json")
    ANALYZED_SUMMARY_FILENAME = os.path.join(LOGS_DIR, f"network_summary_{TIMESTAMP_NOW}.json")

    # Borrar captura HAR previa para iniciar una nueva
    if os.path.exists(HAR_FILENAME):
        os.remove(HAR_FILENAME)

    logger_to_configure.setLevel(logging.INFO)
    file_handler = logging.FileHandler(LOG_FILENAME, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s'))
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s'))
    
    if not logger_to_configure.handlers:
        logger_to_configure.addHandler(file_handler)
        logger_to_configure.addHandler(stream_handler)
    logger_to_configure.info(f"Logging configurado. Log: {LOG_FILENAME}, HAR: {HAR_FILENAME}, Datos: {OUTPUT_ACCIONES_DATA_FILENAME}")


def ensure_timestamp_current(logger_to_configure):
    """Verifica que el timestamp global esté actualizado y reconfigura si es necesario."""
    global TIMESTAMP_NOW
    try:
        if not TIMESTAMP_NOW:
            raise ValueError("Timestamp vacío")
        ts_dt = datetime.strptime(TIMESTAMP_NOW, '%Y%m%d_%H%M%S')
        if abs((datetime.now() - ts_dt).total_seconds()) > 3600:
            raise ValueError("Timestamp desfasado")
    except Exception:
        configure_run_specific_logging(logger_to_configure)


def handle_console_message(msg, logger_param):
    text = msg.text
    if "Failed to load resource" in text and \
       ("doubleclick.net" in text or "google-analytics.com" in text or "validate.perfdrive.com" in text or "googlesyndication.com" in text or "cdn.ampproject.org" in text):
        logger_param.debug(f"JS CONSOLE (Filtered Error/CSP): {text}")
    elif "Slow network is detected" in text:
        logger_param.debug(f"JS CONSOLE (Performance): {text}")
    else:
        logger_param.info(f"JS CONSOLE ({msg.type}): {text}")


def run_automation(logger_param, attempt=1, max_attempts=2, *, non_interactive=None, keep_open=True):
    if non_interactive is None:
        non_interactive = NON_INTERACTIVE or os.getenv("BOLSA_NON_INTERACTIVE") == "1"

    ensure_timestamp_current(logger_param)

    current_har_filename = HAR_FILENAME
    current_output_acciones_data_filename = OUTPUT_ACCIONES_DATA_FILENAME
    current_analyzed_summary_filename = ANALYZED_SUMMARY_FILENAME

    logger_param.info(f"--- Iniciando Intento de Automatización #{attempt} ---")

    if attempt > max_attempts:
        logger_param.error(f"Se alcanzó el número máximo de reintentos ({max_attempts}). Abortando.")
        return

    p_instance = None
    browser = None
    context = None
    page = None
    storage_state = None
    is_mis_conexiones_page = False

    try:
        p_instance = sync_playwright().start()
        browser = p_instance.chromium.launch(headless=False, slow_mo=250, args=["--start-maximized"])
        context = browser.new_context(
            user_agent=DEFAULT_USER_AGENT,
            no_viewport=True,
            record_har_path=current_har_filename,
            record_har_mode="full",
        )
        logger_param.info(f"Grabando tráfico de red en: {current_har_filename}")
        
        page = context.new_page()
        page.on("console", lambda msg: handle_console_message(msg, logger_param))

        logger_param.info(f"Paso 1: Navegando a la página que requiere login: {INITIAL_PAGE_URL}")
        page.goto(INITIAL_PAGE_URL, timeout=60000)
        logger_param.info(f"Paso 1: URL actual después de goto inicial: {page.url}")

        logger_param.info("Paso 2: Esperando por la página de login de SSO (si fuimos redirigidos)...")
        if "sso.bolsadesantiago.com" not in page.url:
            page.wait_for_url(lambda url: "sso.bolsadesantiago.com" in url, timeout=30000)
            logger_param.info(f"Paso 2: Redirigido a SSO. URL actual: {page.url}")
        page.wait_for_selector(USERNAME_SELECTOR, state="visible", timeout=45000)
        logger_param.info("Paso 2: Página de login de SSO cargada.")

        logger_param.info(f"Paso 3: Ingresando usuario: {USERNAME}")
        page.fill(USERNAME_SELECTOR, USERNAME)
        logger_param.info("Paso 3: Ingresando contraseña...")
        page.fill(PASSWORD_SELECTOR, PASSWORD)
        logger_param.info("Paso 3: Credenciales ingresadas.")

        logger_param.info("Paso 4: Haciendo clic en el botón de Iniciar Sesión...")
        page.click(LOGIN_BUTTON_SELECTOR)

        logger_param.info("Paso 4b: Comprobando indicios de CAPTCHA tras el login...")
        page_content = ""
        try:
            page_content = page.content()
        except PlaywrightError as err:
            logger_param.debug(f"No se pudo obtener el contenido de la página: {err}")
        indicators = ["radware", "captcha"]
        captcha_detected = any(ind in page.url.lower() for ind in indicators)
        if not captcha_detected and page_content:
            lower_content = page_content.lower()
            captcha_detected = any(ind in lower_content for ind in indicators)

        if captcha_detected:
            logger_param.warning("Posible CAPTCHA detectado. Esperando al usuario si es posible...")
            if not non_interactive:
                try:
                    page.wait_for_function(
                        "() => !document.body.innerText.toLowerCase().includes('captcha') "
                        "&& !window.location.href.toLowerCase().includes('radware') "
                        "&& !window.location.href.toLowerCase().includes('captcha')",
                        timeout=120000,
                    )
                    logger_param.info("Continuando después de la resolución del CAPTCHA")
                except PlaywrightTimeoutError:
                    logger_param.warning("Timeout esperando resolución del CAPTCHA, se continúa")

        logger_param.info("Paso 5: Esperando redirección post-login a www.bolsadesantiago.com...")
        try:
            page.wait_for_url(
                lambda url: "www.bolsadesantiago.com" in url and "sso.bolsadesantiago.com" not in url,
                timeout=60000
            )
            logger_param.info(f"Paso 5: Redirección a www.bolsadesantiago.com exitosa. URL actual: {page.url}")
        except PlaywrightTimeoutError:
            logger_param.error(f"Paso 5: Timeout esperando redirección. URL actual: {page.url if page else 'N/A'}")
            if page and not page.is_closed():
                page.screenshot(path=os.path.join(LOGS_DIR, f"timeout_post_login_redirect_{TIMESTAMP_NOW}.png"))
            raise

        time.sleep(3)
        logger_param.info("Paso 7: Verificando si estamos en la página 'MIS CONEXIONES'...")
        try:
            if page.locator(MIS_CONEXIONES_TITLE_SELECTOR).is_visible(timeout=7000):
                is_mis_conexiones_page = True
                logger_param.warning("Paso 7: Detectada página 'MIS CONEXIONES'. Límite de sesiones alcanzado.")
                cerrar_todas_button = page.locator(CERRAR_TODAS_SESIONES_SELECTOR)
                if cerrar_todas_button.is_visible(timeout=5000):
                    logger_param.info("Paso 7: Intentando hacer clic en 'Cerrar sesión en todos los dispositivos'...")
                    cerrar_todas_button.click()
                    logger_param.info("Paso 7: Clic en 'Cerrar todas las sesiones' realizado. Esperando...")
                    page.wait_for_load_state("networkidle", timeout=20000) 
                    time.sleep(5) 
                    logger_param.info(f"Paso 7: Página actualizada después de cerrar sesiones. URL actual: {page.url}")
                    logger_param.info("Paso 7: Sesiones cerradas. Reiniciando el proceso de automatización...")
                    logger_param.info(
                        "El navegador permanecerá abierto; cierre manualmente si es necesario."
                    )
                    time.sleep(random.uniform(3,7))
                    configure_run_specific_logging(logger_param)
                    return run_automation(logger_param, attempt + 1, max_attempts)
                else:
                    logger_param.error("Paso 7: Botón 'Cerrar sesión en todos los dispositivos' no encontrado.")
            else:
                logger_param.info("Paso 7: No se detectó la página 'MIS CONEXIONES' (título no visible), continuando...")
        except PlaywrightTimeoutError:
            logger_param.info("Paso 7: Página 'MIS CONEXIONES' no apareció en el tiempo esperado, continuando...")
        except Exception as pe_err: 
             logger_param.warning(f"Paso 7: Error al verificar página 'MIS CONEXIONES': {pe_err}. Asumiendo que no es la página de error.")

        if not is_mis_conexiones_page:
            logger_param.info(f"Paso 8: Navegando a la página de destino para datos: {TARGET_DATA_PAGE_URL}")
            if TARGET_DATA_PAGE_URL not in page.url:
                page.goto(TARGET_DATA_PAGE_URL, timeout=60000, wait_until="domcontentloaded")
            else:
                page.wait_for_load_state("domcontentloaded", timeout=45000)
            logger_param.info(f"Paso 8: Navegación inicial a {page.url} (DOM cargado) completada.")

            logger_param.info(f"Paso 9: Forzando recarga de la página actual ({page.url}) para asegurar carga de datos premium...")
            page.reload(wait_until="networkidle", timeout=60000)
            logger_param.info(f"Paso 9: Página recargada ({page.url}) y red en reposo.")
            
            if TARGET_DATA_PAGE_URL not in page.url: # Doble check
                logger_param.error(f"Paso 9: Después de recargar, la URL es {page.url}, NO la esperada {TARGET_DATA_PAGE_URL}.")
            
            logger_param.info("Paso 9b: Esperando 10 segundos adicionales para asegurar que todos los datos se carguen por XHR/WebSocket...")
            time.sleep(10) 

            logger_param.info("Paso 10: El script ha completado la navegación y espera. Los datos de la API deberían estar en el HAR.")
        
        if is_mis_conexiones_page:
            logger_param.info("Flujo principal detenido debido a la página 'MIS CONEXIONES'.")

    except PlaywrightTimeoutError as pte:
        logger_param.error(f"ERROR DE TIMEOUT: {pte}")
        if page and not page.is_closed():
            page.screenshot(path=os.path.join(LOGS_DIR, f"timeout_error_{TIMESTAMP_NOW}.png"))
    except Exception as e:
        logger_param.exception("ERROR GENERAL:")
        if page and not page.is_closed():
            page.screenshot(path=os.path.join(LOGS_DIR, f"general_error_{TIMESTAMP_NOW}.png"))
    finally:
        logger_param.info("Bloque Finally: Preparando análisis HAR y finalización...")

        # Guardar el estado de la sesión antes de cerrar el contexto
        storage_state = None
        if context is not None:
            try:
                storage_state = context.storage_state()
                context.close()
            except Exception as close_err:
                logger_param.warning(f"No se pudo cerrar el contexto del navegador: {close_err}")

        effective_har_filename = HAR_FILENAME
        effective_output_acciones_data_filename = OUTPUT_ACCIONES_DATA_FILENAME
        effective_analyzed_summary_filename = ANALYZED_SUMMARY_FILENAME

        if os.path.exists(effective_har_filename):
            analyze_har_and_extract_data(
                effective_har_filename,
                API_PRIMARY_DATA_PATTERNS,
                URLS_TO_INSPECT_IN_HAR_FOR_CONTEXT,
                effective_output_acciones_data_filename,
                effective_analyzed_summary_filename,
                logger_param
            )
        else:
            logger_param.error(f"El archivo HAR {effective_har_filename} no fue creado o no se encontró, no se puede analizar.")

        logger_param.info("Proceso del script realmente finalizado.")
        if keep_open and (not is_mis_conexiones_page or attempt >= max_attempts):
            if browser is not None:
                try:
                    keep_context = browser.new_context(
                        user_agent=DEFAULT_USER_AGENT,
                        no_viewport=True,
                        storage_state=storage_state or {},
                    )
                    keep_page = keep_context.new_page()
                    keep_page.goto(TARGET_DATA_PAGE_URL, timeout=60000)
                    logger_param.info(
                        "Contexto adicional abierto para inspección manual. El script no cerrará el navegador."
                    )
                except Exception as reopen_err:
                    logger_param.warning(
                        f"No se pudo abrir un contexto de inspección: {reopen_err}"
                    )

            logger_param.info(
                "El script permanecerá en ejecución. Cierre el navegador manualmente cuando termine."
            )
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                logger_param.info(
                    "Interrupción recibida. Finalizando script y navegador..."
                )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bolsa Santiago bot")
    parser.add_argument("--no-keep-open", dest="keep_open", action="store_false", help="Cerrar el navegador automáticamente al finalizar", default=True)
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="No esperar confirmación del usuario al finalizar",
    )
    args = parser.parse_args(argv)

    global NON_INTERACTIVE
    if args.non_interactive:
        NON_INTERACTIVE = True

    validate_credentials()
    configure_run_specific_logging(logger_instance_global)
    run_automation(logger_instance_global, non_interactive=NON_INTERACTIVE, keep_open=args.keep_open)


if __name__ == "__main__":
    main()
