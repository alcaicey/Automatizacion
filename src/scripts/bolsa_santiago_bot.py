from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
import time
import json
import logging
from datetime import datetime
import os
import random

# Importar la función de análisis del otro archivo
from har_analyzer import analyze_har_and_extract_data

# --- Configuración de Logging Global ---
LOG_DIR = "logs_bolsa"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILENAME = "" 
HAR_FILENAME = "" 
OUTPUT_ACCIONES_DATA_FILENAME = "" 
ANALYZED_SUMMARY_FILENAME = "" 

logger_instance_global = logging.getLogger(__name__)
# --- Fin Configuración de Logging ---

# --- CONFIGURACIÓN ---
INITIAL_PAGE_URL = "https://www.bolsadesantiago.com/plus_acciones_precios"
TARGET_DATA_PAGE_URL = "https://www.bolsadesantiago.com/plus_acciones_precios"

USERNAME = "alcaicey@gmail.com"
PASSWORD = "Carlosirenee13#"

USERNAME_SELECTOR = "#username"
PASSWORD_SELECTOR = "#password"
LOGIN_BUTTON_SELECTOR = "#kc-login"

API_PRIMARY_DATA_PATTERNS = [
    "https://www.bolsadesantiago.com/api/RV_ResumenMercado/getAccionesPrecios",
    "https://www.bolsadesantiago.com/api/Cuenta_Premium/getPremiumAccionesPrecios"
]
URLS_TO_INSPECT_IN_HAR_FOR_CONTEXT = [
    "https://www.bolsadesantiago.com/api/Securities/csrfToken",
    "https://www.bolsadesantiago.com/api/Comunes_User/getEstadoSesionUsuario",
    "https://www.bolsadesantiago.com/api/Indices/getIndicesPremium"
]
MIS_CONEXIONES_TITLE_SELECTOR = "h1:has-text('MIS CONEXIONES')"
CERRAR_TODAS_SESIONES_SELECTOR = "button:has-text('Cerrar sesión en todos los dispositivos')"
# --- FIN DE LA CONFIGURACIÓN ---

def configure_run_specific_logging(logger_to_configure):
    global LOG_FILENAME, HAR_FILENAME, OUTPUT_ACCIONES_DATA_FILENAME, ANALYZED_SUMMARY_FILENAME
    
    for handler in list(logger_to_configure.handlers):
        logger_to_configure.removeHandler(handler)
        handler.close()

    TIMESTAMP_NOW = datetime.now().strftime('%Y%m%d_%H%M%S')
    LOG_FILENAME = os.path.join(LOG_DIR, f"bolsa_bot_log_{TIMESTAMP_NOW}.txt")
    HAR_FILENAME = os.path.join(LOG_DIR, f"bolsa_bot_network_{TIMESTAMP_NOW}.har")
    OUTPUT_ACCIONES_DATA_FILENAME = os.path.join(LOG_DIR, f"acciones-precios-plus_{TIMESTAMP_NOW}.json")
    ANALYZED_SUMMARY_FILENAME = os.path.join(LOG_DIR, f"network_summary_{TIMESTAMP_NOW}.json")

    logger_to_configure.setLevel(logging.INFO)
    file_handler = logging.FileHandler(LOG_FILENAME, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s'))
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s'))
    
    if not logger_to_configure.handlers:
        logger_to_configure.addHandler(file_handler)
        logger_to_configure.addHandler(stream_handler)
    logger_to_configure.info(f"Logging configurado. Log: {LOG_FILENAME}, HAR: {HAR_FILENAME}, Datos: {OUTPUT_ACCIONES_DATA_FILENAME}")


def handle_console_message(msg, logger_param):
    text = msg.text
    if "Failed to load resource" in text and \
       ("doubleclick.net" in text or "google-analytics.com" in text or "validate.perfdrive.com" in text or "googlesyndication.com" in text or "cdn.ampproject.org" in text):
        logger_param.debug(f"JS CONSOLE (Filtered Error/CSP): {text}")
    elif "Slow network is detected" in text:
        logger_param.debug(f"JS CONSOLE (Performance): {text}")
    else:
        logger_param.info(f"JS CONSOLE ({msg.type}): {text}")


def run_automation(logger_param, attempt=1, max_attempts=2):
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
    is_mis_conexiones_page = False 

    try:
        p_instance = sync_playwright().start()
        browser = p_instance.chromium.launch(headless=False, slow_mo=250, args=["--start-maximized"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            no_viewport=True,
            record_har_path=current_har_filename,
            record_har_mode="full"
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

        logger_param.info("Paso 5: Esperando redirección post-login a www.bolsadesantiago.com...")
        try:
            page.wait_for_url(
                lambda url: "www.bolsadesantiago.com" in url and "sso.bolsadesantiago.com" not in url,
                timeout=60000
            )
            logger_param.info(f"Paso 5: Redirección a www.bolsadesantiago.com exitosa. URL actual: {page.url}")
        except PlaywrightTimeoutError:
            logger_param.error(f"Paso 5: Timeout esperando redirección. URL actual: {page.url if page else 'N/A'}")
            if page and not page.is_closed(): page.screenshot(path=os.path.join(LOG_DIR,f"timeout_post_login_redirect_{TIMESTAMP_NOW}.png"))
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
                    if context: context.close() 
                    if browser: browser.close()
                    if p_instance: p_instance.stop()
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
        if page and not page.is_closed(): page.screenshot(path=os.path.join(LOG_DIR, f"timeout_error_{TIMESTAMP_NOW}.png"))
    except Exception as e:
        logger_param.exception("ERROR GENERAL:")
        if page and not page.is_closed(): page.screenshot(path=os.path.join(LOG_DIR,f"general_error_{TIMESTAMP_NOW}.png"))
    finally:
        logger_param.info("Bloque Finally: Intentando cerrar contexto y navegador...")
        
        effective_har_filename = HAR_FILENAME 
        effective_output_acciones_data_filename = OUTPUT_ACCIONES_DATA_FILENAME
        effective_analyzed_summary_filename = ANALYZED_SUMMARY_FILENAME

        if context:
            try:
                context.close() 
                logger_param.info(f"Contexto cerrado. Archivo HAR debería estar guardado en: {effective_har_filename}")
            except Exception as e_har:
                logger_param.error(f"Error al cerrar el contexto (HAR podría no haberse guardado completamente): {e_har}")
        else:
            logger_param.warning("Contexto no fue inicializado o ya estaba cerrado.")

        if browser and browser.is_connected():
            try: browser.close()
            except Exception as e_close_final: logger_param.warning(f"Error menor durante cierre final del navegador: {e_close_final}")
        else: logger_param.warning("Navegador no fue inicializado o ya está cerrado.")
        
        if p_instance:
            try: p_instance.stop()
            except Exception as e_stop: logger_param.warning(f"Error al detener la instancia de Playwright: {e_stop}")

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
        if not is_mis_conexiones_page or attempt >= max_attempts:
             input("Presiona Enter para terminar el script (después del análisis HAR)...")


if __name__ == "__main__":
    configure_run_specific_logging(logger_instance_global) 
    run_automation(logger_instance_global)