import os
import json
import logging
import time
import subprocess
from datetime import datetime
import threading
import re
import glob
import random  # Asegurarse de que random esté importado
import sys
import hashlib
from contextlib import nullcontext
from flask import current_app

from src.extensions import socketio
from src.models import db
from src.models.stock_price import StockPrice
from src.models.last_update import LastUpdate
from sqlalchemy.dialects.postgresql import insert

from src.config import SCRIPTS_DIR, LOGS_DIR, BASE_DIR, PROJECT_SRC_DIR

# Rutas de trabajo obtenidas desde el módulo de configuración
# Configuración de logging para este script de servicio/orquestador
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Centralizar logs en la misma carpeta definida en LOGS_DIR
service_log_file = os.path.join(LOGS_DIR, "bolsa_service.log")

file_handler = logging.FileHandler(service_log_file, encoding="utf-8")
file_handler.setFormatter(
    logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(
    logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
)

# Evitar añadir handlers múltiples si el script se recarga o se llama a la configuración varias veces
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

# Variable para controlar el hilo de actualización
update_thread = None
stop_update_thread = False

# Controla si ya hay una instancia del bot corriendo para evitar abrir
# varias ventanas del navegador simultáneamente.
bot_running = False
bot_lock = threading.Lock()


def _ensure_env_credentials(app=None) -> bool:
    """Carga credenciales de la base de datos al entorno si existen."""
    ctx = app.app_context() if app else nullcontext()
    with ctx:
        cred = None
        try:
            from src.models.credentials import Credential

            cred = Credential.query.first()
        except Exception:
            cred = None

        if cred:
            os.environ["BOLSA_USERNAME"] = cred.username
            os.environ["BOLSA_PASSWORD"] = cred.password
            return True

    if os.getenv("BOLSA_USERNAME") and os.getenv("BOLSA_PASSWORD"):
        return True

    client_logger = logging.getLogger("client_errors")
    client_logger.error("No hay credenciales disponibles")
    logger.error("No hay credenciales disponibles")
    return False


def get_last_update_timestamp(app=None):
    """Devuelve la marca de tiempo de la última actualización registrada."""
    ctx = app.app_context() if app else nullcontext()
    with ctx:
        lu = LastUpdate.query.get(1)
        return lu.timestamp if lu else None


def is_bot_running():
    """Devuelve True si el bot se está ejecutando actualmente."""
    with bot_lock:
        return bot_running


def send_enter_key_to_browser(app=None, wait_seconds=5):
    """Intenta refrescar la página abierta usando Playwright.

    Si no hay una página activa disponible se recurre al envío de
    ``Ctrl+L`` y ``Enter`` mediante ``pyautogui`` como último recurso.
    """
    if app is None:
        try:
            app = current_app._get_current_object()
        except Exception:
            app = None

    from src.scripts import bolsa_santiago_bot as bot

    page = bot.get_active_page()
    if page:
        logger.info("Reutilizando navegador existente con Playwright")
        try:
            success, _ = bot.refresh_active_page(bot.logger_instance_global)
        except Exception as exc:  # Posible error de hilos/greenlet
            if "different thread" in str(exc) or "greenlet" in str(exc):
                logger.warning(f"Navegador ligado a hilo inactivo: {exc}")
                return False, True
            logger.exception(f"Error inesperado al refrescar: {exc}")
            return False, True
        if success:
            logger.info("Actualización realizada vía Playwright")
        else:
            logger.warning("No se capturó JSON al refrescar con Playwright")
        return success, True

    if os.getenv("BOLSA_NON_INTERACTIVE") == "1":
        logger.info("Entorno no interactivo detectado y no hay página activa")
        return False, False

    prev_ts = get_last_update_timestamp(app)
    try:
        import pyautogui

        pyautogui.hotkey("ctrl", "l")
        pyautogui.press("enter")
        logger.info("ENTER enviado al navegador externo")
        if wait_seconds:
            time.sleep(wait_seconds)
        new_ts = get_last_update_timestamp(app)
        if new_ts and prev_ts != new_ts:
            logger.info(f"last_update modificado: {prev_ts} -> {new_ts}")
        else:
            logger.warning("last_update no cambió tras refrescar la página")
        return True, False
    except Exception as e:
        logger.exception(f"No se pudo enviar ENTER al navegador externo: {e}")
        return False, False


def get_latest_json_file():
    """
    Obtiene el archivo JSON de datos de acciones más reciente del directorio de logs
    generado por bolsa_santiago_bot.py.
    """
    try:
        # Patrón para los archivos JSON de datos de acciones
        pattern = os.path.join(LOGS_DIR, "acciones-precios-plus_*.json")

        json_files = glob.glob(pattern)

        if not json_files:
            logger.warning(
                f"No se encontraron archivos 'acciones-precios-plus_*.json' en {LOGS_DIR}"
            )
            return None

        latest_json = max(json_files, key=os.path.getmtime)
        logger.info(f"Archivo JSON de datos más reciente encontrado: {latest_json}")
        return latest_json

    except Exception as e:
        logger.exception(f"Error al buscar el archivo JSON de datos más reciente: {e}")
        return None


def extract_timestamp_from_filename(filename):
    """
    Extrae el timestamp del nombre del archivo
    Formato esperado: acciones-precios-plus_AAAAMMDD_HHMMSS.json
    """
    try:
        base_name = os.path.basename(filename)
        match = re.search(r"acciones-precios-plus_(\d{8})_(\d{6})\.json", base_name)

        if match:
            date_str, time_str = match.groups()
            dt_obj = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
            return dt_obj.strftime("%d/%m/%Y %H:%M:%S")

        # Fallback si el patrón no coincide, usar fecha de modificación del archivo
        stat = os.stat(filename)
        return datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S")

    except Exception as e:
        logger.exception(
            f"Error al extraer timestamp del nombre de archivo '{filename}': {e}"
        )
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")  # Fallback a ahora


def get_json_hash_and_timestamp(path):
    """Return md5 hash and a timestamp extracted from the JSON file.

    If the JSON does not contain a recognisable timestamp, the file modification
    time will be used instead.  The timestamp string is returned in ISO format so
    callers can log or compare it easily.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ts = None
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(k, str) and any(
                    t in k.lower() for t in ["time", "fecha", "stamp"]
                ):
                    ts = str(v)
                    break

        if ts:
            try:
                datetime.fromisoformat(ts)
            except Exception:
                ts = None

        if not ts:
            ts = datetime.fromtimestamp(os.path.getmtime(path)).isoformat()

        hash_val = hashlib.md5(
            json.dumps(data, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return hash_val, ts
    except Exception:
        return None, None


def store_prices_in_db(json_path, app=None):
    """Guarda los precios de acciones en la base de datos y emite notificación."""
    ctx = app.app_context() if app else nullcontext()
    with ctx:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            rows = data.get("listaResult") if isinstance(data, dict) else data
            timestamp_str = extract_timestamp_from_filename(json_path)
            ts = datetime.strptime(timestamp_str, "%d/%m/%Y %H:%M:%S")

            if isinstance(rows, list):
                for item in rows:
                    if not isinstance(item, dict):
                        continue

                    symbol = item.get("NEMO") or item.get("symbol")
                    if not symbol:
                        for k, v in item.items():
                            if isinstance(k, str) and re.search(
                                r"(nemo|symbol)", k, re.IGNORECASE
                            ):
                                if isinstance(v, str):
                                    symbol = v.strip()
                                    break

                    if not symbol:
                        logger.warning(
                            "Elemento de acción con formato inesperado o sin 'NEMO/symbol': %s",
                            str(item)[:100],
                        )
                        continue

                    price = item.get("PRECIO_CIERRE") or item.get("price")
                    if price is None:
                        for k, v in item.items():
                            if isinstance(k, str) and re.search(
                                r"(precio|price)", k, re.IGNORECASE
                            ):
                                price = v
                                break
                    price = float(price or 0)

                    variation = item.get("VARIACION") or item.get("variation")
                    if variation is None:
                        for k, v in item.items():
                            if isinstance(k, str) and re.search(
                                r"(var|variation)", k, re.IGNORECASE
                            ):
                                variation = v
                                break
                    variation = float(variation or 0)
                    values = {
                        "symbol": symbol,
                        "price": price,
                        "variation": variation,
                        "timestamp": ts,
                    }

                    bind = db.session.get_bind()
                    if bind and bind.dialect.name == "postgresql":
                        stmt = (
                            insert(StockPrice)
                            .values(**values)
                            .on_conflict_do_nothing(
                                index_elements=["symbol", "timestamp"]
                            )
                        )
                        db.session.execute(stmt)
                    else:
                        db.session.merge(StockPrice(**values))

                # Actualizar registro de última actualización
                lu = LastUpdate.query.get(1)
                if lu:
                    lu.timestamp = ts
                else:
                    lu = LastUpdate(id=1, timestamp=ts)
                    db.session.add(lu)

                db.session.commit()
                socketio.emit("new_data")
        except Exception as e:
            logger.exception(f"Error al guardar datos en DB: {e}")


def get_latest_summary_file():
    """Devuelve la ruta al resumen HAR más reciente generado por el bot."""
    try:
        pattern = os.path.join(LOGS_DIR, "network_summary_*.json")
        summary_files = glob.glob(pattern)

        if not summary_files:
            logger.warning(
                f"No se encontraron archivos 'network_summary_*.json' en {LOGS_DIR}"
            )
            return None

        latest_summary = max(summary_files, key=os.path.getmtime)
        logger.info(f"Archivo de resumen HAR más reciente encontrado: {latest_summary}")
        return latest_summary

    except Exception as e:
        logger.exception(f"Error al buscar el archivo de resumen HAR más reciente: {e}")
        return None


def get_session_remaining_seconds():
    """Obtiene los segundos restantes de la sesión desde el resumen HAR más reciente."""
    try:
        summary_path = get_latest_summary_file()
        if not summary_path or not os.path.exists(summary_path):
            return None

        with open(summary_path, "r", encoding="utf-8") as f:
            summary_data = json.load(f)

        if isinstance(summary_data, list):
            for entry in summary_data:
                if isinstance(entry, dict) and "session_remaining_seconds" in entry:
                    return int(entry["session_remaining_seconds"])

        return None
    except Exception as e:
        logger.exception(f"Error al obtener los segundos restantes de la sesión: {e}")
        return None


def run_bolsa_bot(
    app=None, *, non_interactive=None, keep_open=True, force_update=False
):
    """Ejecuta el bot reutilizando el navegador si es posible."""
    global bot_running
    ctx = app.app_context() if app else nullcontext()
    with ctx:
        if not _ensure_env_credentials(app):
            bot_running = False
            return None
        with bot_lock:
            if bot_running:
                logger.info(
                    "La automatizacion ya está en ejecución. No se iniciará una nueva instancia."
                )
                return None
            bot_running = True
        lu_before = get_last_update_timestamp(app)
        if lu_before:
            logger.info(f"last_update antes de ejecutar: {lu_before}")
        prev_file = get_latest_json_file()
        prev_hash, prev_ts = (
            get_json_hash_and_timestamp(prev_file) if prev_file else (None, None)
        )
        logger.info(f"Hash previo: {prev_hash}, timestamp previo: {prev_ts}")
        try:
            logger.info("=== INICIO DE CICLO COMPLETO DE SCRAPING ===")
            from src.scripts import bolsa_santiago_bot as bot

            if non_interactive is not None:
                if non_interactive:
                    os.environ["BOLSA_NON_INTERACTIVE"] = "1"
                else:
                    os.environ.pop("BOLSA_NON_INTERACTIVE", None)

            if bot.get_active_page():
                logger.info("Recargando navegador existente via Playwright")
                bot.configure_run_specific_logging(bot.logger_instance_global)
                success, json_path = bot.refresh_active_page(bot.logger_instance_global)
            else:
                try:
                    bot.validate_credentials()
                except Exception as cred_err:
                    logger.warning(f"Credenciales no configuradas: {cred_err}")
                bot.configure_run_specific_logging(bot.logger_instance_global)
                bot.run_automation(
                    bot.logger_instance_global,
                    non_interactive=os.getenv("BOLSA_NON_INTERACTIVE") == "1",
                    keep_open=True,
                )
                success, json_path = bot.refresh_active_page(bot.logger_instance_global)

            if not success or not json_path:
                logger.error("No se pudo obtener datos frescos")
                fallback = prev_file or get_latest_json_file()
                if fallback and os.path.exists(fallback):
                    store_prices_in_db(fallback, app=app)
                    return fallback
                return None

            new_hash, new_ts = get_json_hash_and_timestamp(json_path)
            logger.info(f"Hash nuevo: {new_hash}, timestamp del JSON: {new_ts}")
            if prev_hash and new_hash == prev_hash and not force_update:
                logger.warning(
                    "response.text() no cambió entre ejecuciones. Los datos parecen ser los mismos."
                )
                socketio.emit(
                    "no_new_data",
                    {"timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")},
                )
                return None
            prev_lu = get_last_update_timestamp(app)
            store_prices_in_db(json_path, app=app)
            new_lu = get_last_update_timestamp(app)
            if new_lu and prev_lu != new_lu:
                logger.info(f"last_update modificado: {prev_lu} -> {new_lu}")
            else:
                logger.warning("last_update no cambió tras almacenar datos")
            return json_path
        except Exception as e:
            logger.exception(f"Error en run_bolsa_bot: {e}")
            return None
        finally:
            with bot_lock:
                bot_running = False
            logger.info("=== FIN DE CICLO COMPLETO DE SCRAPING ===")


def get_latest_data():
    """
    Obtiene los datos más recientes del archivo JSON de acciones.
    Si no existe, intenta ejecutar el bot para generarlo.
    """
    try:
        # Intentar obtener datos desde la base de datos
        latest_entry = StockPrice.query.order_by(StockPrice.timestamp.desc()).first()
        ts_db = None
        if latest_entry:
            ts_db = latest_entry.timestamp

        latest_json_path = get_latest_json_file()

        if not latest_json_path or not os.path.exists(latest_json_path):
            logger.warning(
                "No existe archivo de datos o no es accesible. Ejecutando scraping..."
            )
            if not is_bot_running():
                latest_json_path = run_bolsa_bot()
            else:
                logger.info(
                    "El bot ya se está ejecutando, no se iniciará una nueva instancia para obtener datos."
                )

        if latest_json_path and os.path.exists(latest_json_path):
            file_timestamp = extract_timestamp_from_filename(latest_json_path)
            try:
                ts_file_dt = datetime.strptime(file_timestamp, "%d/%m/%Y %H:%M:%S")
            except Exception:
                ts_file_dt = None

            if ts_db and ts_file_dt and ts_file_dt <= ts_db:
                prices = StockPrice.query.filter_by(timestamp=ts_db).all()
                return {
                    "data": [p.to_dict() for p in prices],
                    "timestamp": ts_db.strftime("%d/%m/%Y %H:%M:%S"),
                    "source_file": "db",
                }

            with open(latest_json_path, "r", encoding="utf-8") as f:
                data_content = json.load(f)

            timestamp = file_timestamp

            if (
                isinstance(data_content, dict)
                and "listaResult" in data_content
                and isinstance(data_content["listaResult"], list)
            ):
                return {
                    "data": data_content["listaResult"],
                    "timestamp": timestamp,
                    "source_file": latest_json_path,
                }
            elif isinstance(data_content, list):
                return {
                    "data": data_content,
                    "timestamp": timestamp,
                    "source_file": latest_json_path,
                }
            else:
                logger.error(
                    f"El archivo JSON {latest_json_path} no tiene la estructura esperada ('listaResult' o lista raíz). Contenido: {str(data_content)[:200]}"
                )
                return {
                    "error": "Estructura de datos inesperada en archivo JSON.",
                    "timestamp": timestamp,
                    "source_file": latest_json_path,
                }

        if ts_db:
            prices = StockPrice.query.filter_by(timestamp=ts_db).all()
            return {
                "data": [p.to_dict() for p in prices],
                "timestamp": ts_db.strftime("%d/%m/%Y %H:%M:%S"),
                "source_file": "db",
            }

        logger.error("No se pudo obtener el archivo de datos actualizado.")
        return {
            "error": "No se pudieron obtener datos",
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }

    except Exception as e:
        logger.exception(f"Error en get_latest_data: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }


def filter_stocks(stock_codes):
    """
    Filtra las acciones según los códigos proporcionados (NEMO).
    """
    try:
        latest_data_result = get_latest_data()

        if "error" in latest_data_result:
            logger.error(
                f"Error al obtener datos para filtrar: {latest_data_result['error']}"
            )
            return latest_data_result

        # Los datos de acciones están bajo la clave "data" en el resultado de get_latest_data()
        stocks_list = latest_data_result.get("data")
        original_timestamp = latest_data_result.get("timestamp")
        source_file = latest_data_result.get("source_file", "N/A")

        if not isinstance(stocks_list, list):
            logger.error(
                f"Se esperaba una lista de acciones, pero se obtuvo: {type(stocks_list)}. Archivo: {source_file}"
            )
            return {
                "error": "Datos de acciones no son una lista.",
                "timestamp": original_timestamp,
                "source_file": source_file,
            }

        if not stock_codes:  # Si no se proporcionan códigos, devolver todos los datos
            logger.info(
                "No se proporcionaron códigos de acciones para filtrar, devolviendo todos los datos."
            )
            return {
                "data": stocks_list,
                "timestamp": original_timestamp,
                "count": len(stocks_list),
                "source_file": source_file,
            }

        stock_codes_upper = [
            code.upper().strip()
            for code in stock_codes
            if isinstance(code, str) and code.strip()
        ]

        filtered_stocks = []

        def extract_symbol(item):
            if not isinstance(item, dict):
                return None
            for k, v in item.items():
                if isinstance(k, str) and re.search(r"(nemo|symbol)", k, re.IGNORECASE):
                    if isinstance(v, str):
                        return v.strip()
            return None

        for stock in stocks_list:
            symbol = extract_symbol(stock)
            if not symbol:
                logger.warning(
                    "Elemento de acción con formato inesperado o sin clave de símbolo: %s",
                    str(stock)[:100],
                )
                continue
            if (
                re.fullmatch(r"[A-Z0-9.-]+", symbol.upper())
                and symbol.upper() in stock_codes_upper
            ):
                filtered_stocks.append(stock)

        logger.info(
            f"Filtradas {len(filtered_stocks)} acciones de {len(stocks_list)} originales."
        )
        return {
            "data": filtered_stocks,
            "timestamp": original_timestamp,
            "count": len(filtered_stocks),
            "source_file": source_file,
        }

    except Exception as e:
        logger.exception(f"Error en filter_stocks: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }


def compare_last_two_db_entries():
    """Return comparison info between the last two stored timestamps."""
    try:
        timestamps = (
            db.session.query(StockPrice.timestamp)
            .distinct()
            .order_by(StockPrice.timestamp.desc())
            .limit(2)
            .all()
        )
        if len(timestamps) < 2:
            return {}

        ts_curr, ts_prev = timestamps[0][0], timestamps[1][0]
        curr_rows = StockPrice.query.filter_by(timestamp=ts_curr).all()
        prev_rows = StockPrice.query.filter_by(timestamp=ts_prev).all()

        curr_map = {r.symbol: r for r in curr_rows}
        prev_map = {r.symbol: r for r in prev_rows}

        new_syms = set(curr_map) - set(prev_map)
        removed_syms = set(prev_map) - set(curr_map)

        changes = []
        unchanged = []
        for sym in curr_map.keys() & prev_map.keys():
            curr = curr_map[sym]
            prev = prev_map[sym]
            if curr.price != prev.price:
                diff = curr.price - prev.price
                pct = (diff / prev.price * 100) if prev.price else 0.0
                changes.append(
                    {
                        "symbol": sym,
                        "old": prev.to_dict(),
                        "new": curr.to_dict(),
                        "abs_diff": diff,
                        "pct_diff": pct,
                    }
                )
            else:
                unchanged.append(curr.to_dict())

        result = {
            "current_timestamp": ts_curr.strftime("%d/%m/%Y %H:%M:%S"),
            "previous_timestamp": ts_prev.strftime("%d/%m/%Y %H:%M:%S"),
            "current_file": ts_curr.isoformat(),
            "previous_file": ts_prev.isoformat(),
            "new": [curr_map[s].to_dict() for s in new_syms],
            "removed": [prev_map[s].to_dict() for s in removed_syms],
            "changes": changes,
            "unchanged": unchanged,
            "errors": [],
            "total_compared": len(curr_map.keys() | prev_map.keys()),
            "change_count": len(changes),
        }

        if changes:
            diff_file = os.path.join(
                LOGS_DIR,
                f"diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            )
            try:
                with open(diff_file, "w", encoding="utf-8") as f:
                    json.dump(changes, f, indent=2, ensure_ascii=False)
                result["diff_file"] = diff_file
            except Exception as write_exc:
                logger.warning(f"No se pudo escribir diff_file: {write_exc}")

        return result
    except Exception as exc:
        logger.exception(f"Error al comparar registros históricos: {exc}")
        return {}


def update_data_periodically(min_interval_seconds, max_interval_seconds, app=None):
    """
    Actualiza los datos periódicamente en un intervalo aleatorio.
    """
    global stop_update_thread

    logger.info(
        f"Hilo de actualización periódica iniciado. Intervalo: {min_interval_seconds}-{max_interval_seconds} segundos."
    )
    while not stop_update_thread:
        try:
            logger.info("Ejecutando actualización periódica de datos...")
            if not is_bot_running():
                run_bolsa_bot(app=app)
            else:
                logger.info("Se omite la ejecución porque el bot ya está en marcha.")

            interval = random.randint(min_interval_seconds, max_interval_seconds)
            logger.info(f"Próxima actualización periódica en {interval} segundos.")

            # Esperar el intervalo, verificando periódicamente si debemos detenernos
            for _ in range(interval):
                if stop_update_thread:
                    logger.info(
                        "Señal de detención recibida en el hilo de actualización."
                    )
                    break
                time.sleep(1)

        except Exception as e:
            logger.exception(f"Error en la actualización periódica: {e}")
            logger.info(
                "Esperando 60 segundos antes de reintentar la actualización periódica."
            )
            time.sleep(60)
    logger.info("Hilo de actualización periódica detenido.")


def start_periodic_updates(
    min_minutes=15, max_minutes=45, app=None
):  # Intervalos más largos por defecto
    """
    Inicia la actualización periódica de datos en un hilo separado.
    """
    global update_thread, stop_update_thread

    if update_thread and update_thread.is_alive():
        logger.info("El hilo de actualización periódica ya está en ejecución.")
        return False

    stop_update_thread = False
    min_interval_seconds = min_minutes * 60
    max_interval_seconds = max_minutes * 60

    update_thread = threading.Thread(
        target=update_data_periodically,
        args=(min_interval_seconds, max_interval_seconds, app),
        daemon=True,  # El hilo terminará cuando el programa principal termine
    )
    update_thread.start()

    logger.info(
        f"Actualización periódica iniciada. Intervalo entre ejecuciones: {min_minutes}-{max_minutes} minutos."
    )
    return True


def stop_periodic_updates():
    """
    Detiene la actualización periódica de datos.
    """
    global stop_update_thread, update_thread

    if not update_thread or not update_thread.is_alive():
        logger.info("El hilo de actualización periódica no está en ejecución.")
        return True

    logger.info("Enviando señal de detención al hilo de actualización periódica...")
    stop_update_thread = True
    update_thread.join(timeout=10)  # Esperar hasta 10 segundos a que el hilo termine

    if update_thread.is_alive():
        logger.warning(
            "El hilo de actualización periódica no terminó limpiamente después de 10 segundos."
        )
    else:
        logger.info("Hilo de actualización periódica detenido exitosamente.")
    update_thread = None
    return True


# Ejemplo de uso (puedes comentar o eliminar esto si usas el script como módulo)
if __name__ == "__main__":
    logger.info("--- Servicio de Datos de Bolsa de Santiago Iniciado ---")

    # Obtener datos una vez al iniciar
    initial_data = get_latest_data()
    if "error" not in initial_data:
        logger.info(
            f"Datos iniciales cargados desde: {initial_data.get('source_file', 'N/A')}"
        )
        logger.info(f"Timestamp de datos iniciales: {initial_data['timestamp']}")
        logger.info(
            f"Número de acciones en datos iniciales: {len(initial_data.get('data', []))}"
        )
    else:
        logger.error(f"Error al cargar datos iniciales: {initial_data['error']}")

    # Filtrar algunas acciones de ejemplo
    codigos_a_filtrar = ["SQM-B", "COPEC", "CMPC", "FALABELLA", "CHILE"]  # Ejemplo
    logger.info(f"Filtrando por los siguientes códigos: {codigos_a_filtrar}")
    acciones_filtradas = filter_stocks(codigos_a_filtrar)

    if "error" not in acciones_filtradas:
        logger.info(
            f"Resultado del filtrado (Fuente: {acciones_filtradas.get('source_file', 'N/A')}, Timestamp: {acciones_filtradas['timestamp']}):"
        )
        for accion in acciones_filtradas.get("data", []):
            print(
                f"  NEMO: {accion.get('NEMO')}, PRECIO_CIERRE: {accion.get('PRECIO_CIERRE')}, VARIACION: {accion.get('VARIACION')}"
            )
    else:
        logger.error(f"Error al filtrar acciones: {acciones_filtradas['error']}")

    # Iniciar actualizaciones periódicas (ej. cada 15-45 minutos)
    # start_periodic_updates(min_minutes=15, max_minutes=45)

    # Mantener el script principal vivo si se desea que el hilo siga corriendo
    # o si esto fuera parte de una aplicación más grande (ej. Flask, FastAPI)
    # try:
    #     while True:
    #         time.sleep(60) # Dormir y verificar estado o esperar comandos
    #         logger.debug("Servicio principal activo...")
    # except KeyboardInterrupt:
    #     logger.info("Interrupción por teclado recibida. Deteniendo servicio...")
    # finally:
    #     stop_periodic_updates()
    #     logger.info("--- Servicio de Datos de Bolsa de Santiago Detenido ---")
