"""
Servicio/orquestador que coordina el scraping de precios, el refresco de datos
y su almacenamiento en la base de datos.

Novedades de esta versión
─────────────────────────
1.  Busca si existe una ventana de **Chromium 139.x** abierta; si la encuentra,
    la trae al frente y envía «CTRL+L → ENTER» para recargar la página, evitando
    lanzar Playwright cuando no es necesario.

2.  Todos los pasos relevantes del flujo se enumeran en el log para facilitar
    el diagnóstico («[1] …», «[2] …», etc.).

3.  Se añaden las dependencias `psutil` y `pygetwindow` (esta última solo
    necesaria en Windows para activar la ventana).
"""

from __future__ import annotations

# ───────────────────────────────────────────────────────────── imports estándar ──
import asyncio
import glob
import hashlib
import json
import logging
import os
import random
import re
import sys
import threading
import time
import traceback
from contextlib import nullcontext
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app
from sqlalchemy.dialects.postgresql import insert

# ───────────────────────────────────────── imports de terceros añadidos ──────────
from .browser_refresh import (
    find_chromium_process,
    refresh_chromium_tab,
)
# ──────────────────────────────────────────── imports internos del proyecto ─────
from src.config import BASE_DIR, LOGS_DIR, PROJECT_SRC_DIR, SCRIPTS_DIR
from src.extensions import socketio
from src.models import db
from src.models.last_update import LastUpdate
from src.models.stock_price import StockPrice

# ───────────────────────────────────────────────────── configuración de logging ─
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

service_log_file = os.path.join(LOGS_DIR, "bolsa_service.log")
_file_hdlr = logging.FileHandler(service_log_file, encoding="utf-8")
_file_hdlr.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s"))
_stream_hdlr = logging.StreamHandler()
_stream_hdlr.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s"))

if not logger.hasHandlers():
    logger.addHandler(_file_hdlr)
    logger.addHandler(_stream_hdlr)

# ─── helper anti-ValueError cuando logging.shutdown() cierra streams ───
def _safe_log(level: str, msg: str, *args, **kwargs):
    """Escribe solo si todos los handlers mantienen su stream abierto."""
    root = logging.getLogger()
    def _closed(h):
        return getattr(h, "stream", None) and getattr(h.stream, "closed", False)
    if any(_closed(h) for h in logger.handlers) or any(_closed(h) for h in root.handlers):
        return
    getattr(logger, level)(msg, *args, **kwargs) True

    if os.getenv("BOLSA_USERNAME") and os.getenv("BOLSA_PASSWORD"):
        return True

    client_logger = logging.getLogger("client_errors")
    client_logger.error("No hay credenciales disponibles")
    from src.routes.errors import log_error
    logger.error("No hay credenciales disponibles")
    log_error("service", "No hay credenciales disponibles")
    return False


def get_last_update_timestamp(app=None):
    """Devuelve la marca de tiempo de la última actualización registrada."""
    ctx = app.app_context() if app else nullcontext()
    with ctx:
        lu = LastUpdate.query.get(1)
        return lu.timestamp if lu else None


def is_bot_running() -> bool:
    """True si el bot de Playwright está corriendo."""
    with bot_lock:
        return bot_running


# ═════════════════════════════════════════════════════════════════════════════════
# 3. Refresco de datos (ENTER o Playwright) — modificado
# ═════════════════════════════════════════════════════════════════════════════════
def send_enter_key_to_browser(app=None, *, wait_seconds: int = 5) -> Tuple[bool, bool]:
    """
    Flujo de refresco:

    1. Busca Chromium 139.x abierto → intenta ENTER.
    2. Si falla o no hay Chromium → reutiliza Playwright si la página está viva.
    3. Como último recurso: pyautogui 'ciego'.

    Devuelve (success, via_playwright).
    """
    # ── Paso 1: intento de ENTER sobre Chromium existente ──────────────────────
    logger.info("[1] Buscando instancia de Chromium 139.x…")
    proc = find_chromium_process()
    if proc:
        logger.info("[2] Chromium hallado (PID %s) — enviando ENTER.", proc.pid)
        if refresh_chromium_tab(proc):
            logger.info("[4] ENTER enviado correctamente.")
            prev_ts = get_last_update_timestamp(app)
            if wait_seconds:
                time.sleep(wait_seconds)
            new_ts = get_last_update_timestamp(app)
            if new_ts and prev_ts != new_ts:
                logger.info("[5] last_update cambió: %s → %s", prev_ts, new_ts)
            else:
                logger.warning("[5] last_update NO cambió tras ENTER.")
            return True, False
        logger.warning("[4] Falló el ENTER; probaremos Playwright.")

    # ── Paso 2: reutilizar Playwright si la página sigue activa ────────────────
    if app is None:
        try:
            app = current_app._get_current_object()
        except Exception:
            app = None

    from src.scripts import bolsa_santiago_bot as bot  # import tardío

    page = bot.get_active_page()
    if page:
        logger.info("[6] Navegador Playwright vivo — refrescando página.")
        try:
            success, _ = bot.refresh_active_page(bot.logger_instance_global)
        except Exception as exc:
            if "different thread" in str(exc) or "greenlet" in str(exc):
                logger.warning("[ERR] Navegador ligado a hilo inactivo: %s", exc)
                return False, True
            logger.exception("[ERR] Error inesperado al refrescar: %s", exc)
            return False, True

        if success:
            logger.info("[7] Refresco Playwright OK.")
        else:
            logger.warning("[7] No se capturó JSON al refrescar (Playwright).")
        return success, True

    # ── Paso 3: intento 'ciego' con pyautogui si el entorno es interactivo ────
    try:
        if os.getenv("BOLSA_NON_INTERACTIVE") == "1":
            logger.info("[8] Entorno no-interactivo — se omite ENTER ciego.")
            return False, False

        logger.info("[8] Enviando ENTER 'ciego' (sin referencia de página).")
        prev_ts = get_last_update_timestamp(app)
        pyautogui.hotkey("ctrl", "l")
        pyautogui.press("enter")
        if wait_seconds:
            time.sleep(wait_seconds)
        new_ts = get_last_update_timestamp(app)
        if new_ts and prev_ts != new_ts:
            logger.info("[9] last_update cambió: %s → %s", prev_ts, new_ts)
        else:
            logger.warning("[9] last_update NO cambió tras ENTER ciego.")
        return True, False
    except Exception as exc:
        logger.exception("[ERR] No se pudo enviar ENTER: %s", exc)
        return False, False


# ═════════════════════════════════════════════════════════════════════════════════
# 4.  Resto de funciones originales (sin cambios)
# ═════════════════════════════════════════════════════════════════════════════════
# (Todas las funciones que siguen provienen íntegramente de tu versión anterior:
#  get_latest_json_file, extract_timestamp_from_filename, get_json_hash_and_timestamp,
#  _build_price_summary, store_prices_in_db, get_latest_summary_file,
#  get_session_remaining_seconds, run_bolsa_bot, get_latest_data, filter_stocks,
#  compare_last_two_db_entries, update_data_periodically, start_periodic_updates,
#  stop_periodic_updates,  y el bloque `if __name__ == "__main__": …`)

# --------------  Copia SIN CAMBIOS cada función a partir de aquí  --------------

def get_latest_json_file():
    """Obtiene el archivo JSON de datos más reciente generado por el bot."""
    try:
        pattern = os.path.join(LOGS_DIR, "acciones-precios-plus_*.json")
        json_files = glob.glob(pattern)
        if not json_files:
            logger.warning(
                "No se encontraron archivos 'acciones-precios-plus_*.json' en %s",
                LOGS_DIR,
            )
            return None
        latest_json = max(json_files, key=os.path.getmtime)
        logger.info("JSON más reciente: %s", latest_json)
        return latest_json
    except Exception as e:
        logger.exception("Error al buscar JSON más reciente: %s", e)
        return None


def extract_timestamp_from_filename(filename: str) -> str:
    """
    Extrae timestamp seguro del nombre (formato acciones-precios-plus_YYYYMMDD_HHMMSS.json).
    Si no coincide, usa mtime del archivo.
    """
    try:
        base_name = os.path.basename(filename)
        m = re.search(r"acciones-precios-plus_(\d{8})_(\d{6})\.json", base_name)
        if m:
            date_str, time_str = m.groups()
            dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        stat = os.stat(filename)
        return datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
    except Exception as e:
        logger.exception(
            "Error al extraer timestamp de '%s': %s", filename, e, exc_info=False
        )
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def get_json_hash_and_timestamp(path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Devuelve (md5, timestamp) de un JSON.  Timestamp ISO; si no existe en data,
    se usa mtime del archivo.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = None
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(k, str) and any(
                    kw in k.lower() for kw in ("time", "fecha", "stamp")
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
        hash_val = hashlib.md5(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()
        return hash_val, ts
    except Exception:
        return None, None


def _build_price_summary(rows: List[Dict[str, Any]], ts: datetime) -> str:
    """Devuelve una línea legible con resumen de las variaciones capturadas."""
    if not rows:
        return "0 acciones capturadas"
    parsed: List[Tuple[str, float]] = []
    top_symbol, top_var = "", 0.0
    for item in rows:
        if not isinstance(item, dict):
            continue
        symbol = item.get("NEMO") or item.get("symbol") or ""
        if not symbol:
            for k, v in item.items():
                if isinstance(k, str) and re.search(r"(nemo|symbol)", k, re.IGNORECASE):
                    if isinstance(v, str):
                        symbol = v.strip()
                        break
        try:
            variation = float(item.get("VARIACION") or item.get("variation") or 0)
        except (TypeError, ValueError):
            variation = 0.0
        parsed.append((symbol, variation))
        if not top_symbol or abs(variation) > abs(top_var):
            top_symbol, top_var = symbol, variation
    sample = ", ".join(f"{s} {v:+.1f}%" for s, v in parsed[:2])
    summary = f"{len(parsed)} acciones. {sample}. Top mover: {top_symbol} {top_var:+.1f}%"
    return f"{ts.strftime('%Y-%m-%d %H:%M')} - {summary}"


def store_prices_in_db(json_path: str, app=None):
    """Guarda precios en la DB y emite evento `new_data`."""
    ctx = app.app_context() if app else nullcontext()
    with ctx:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            rows = data.get("listaResult") if isinstance(data, dict) else data
            ts_str = extract_timestamp_from_filename(json_path)
            ts = datetime.strptime(ts_str, "%d/%m/%Y %H:%M:%S")

            if isinstance(rows, list):
                for item in rows:
                    if not isinstance(item, dict):
                        continue
                    # --- symbol --------------------------------------------------
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
                            "Elemento sin NEMO/symbol válido: %s", str(item)[:100]
                        )
                        continue
                    # --- price ---------------------------------------------------
                    price = item.get("PRECIO_CIERRE") or item.get("price")
                    if price is None:
                        for k, v in item.items():
                            if isinstance(k, str) and re.search(
                                r"(precio|price)", k, re.IGNORECASE
                            ):
                                price = v
                                break
                    price = float(price or 0)
                    # --- variation ----------------------------------------------
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
                            .on_conflict_do_nothing(index_elements=["symbol", "timestamp"])
                        )
                        db.session.execute(stmt)
                    else:
                        db.session.merge(StockPrice(**values))

                # actualizar LastUpdate
                lu = LastUpdate.query.get(1)
                if lu:
                    lu.timestamp = ts
                else:
                    db.session.add(LastUpdate(id=1, timestamp=ts))

                db.session.commit()
                socketio.emit("new_data")
                logger.info(_build_price_summary(rows, ts))
        except Exception as e:
            logger.exception("Error al guardar en DB: %s", e)


def get_latest_summary_file() -> Optional[str]:
    """Archivo HAR-summary más reciente, o None."""
    try:
        pattern = os.path.join(LOGS_DIR, "network_summary_*.json")
        summary_files = glob.glob(pattern)
        if not summary_files:
            logger.warning(
                "No se encontraron 'network_summary_*.json' en %s", LOGS_DIR
            )
            return None
        return max(summary_files, key=os.path.getmtime)
    except Exception as e:
        logger.exception("Error al buscar resumen HAR: %s", e)
        return None


def get_session_remaining_seconds() -> Optional[int]:
    """Lee el campo session_remaining_seconds del resumen HAR más reciente."""
    try:
        summary_path = get_latest_summary_file()
        if not summary_path:
            return None
        with open(summary_path, "r", encoding="utf-8") as f:
            summary_data = json.load(f)
        if isinstance(summary_data, list):
            for entry in summary_data:
                if isinstance(entry, dict) and "session_remaining_seconds" in entry:
                    return int(entry["session_remaining_seconds"])
        return None
    except Exception as e:
        logger.exception("Error al leer session_remaining_seconds: %s", e)
        return None


def run_bolsa_bot(app=None, *, non_interactive=None, keep_open=True, force_update=False):
    """Ejecuta el bot Playwright o reutiliza navegador existente."""
    global bot_running
    ctx = app.app_context() if app else nullcontext()
    with ctx:
        if not _ensure_env_credentials(app):
            bot_running = False
            return None
        with bot_lock:
            if bot_running:
                logger.info("Bot ya está en ejecución; se omite nuevo lanzamiento.")
                return None
            bot_running = True

        prev_file = get_latest_json_file()
        prev_hash, _ = get_json_hash_and_timestamp(prev_file) if prev_file else (None, None)

        try:
            logger.info("=== INICIO DE SCRAPING ===")
            from src.scripts import bolsa_santiago_bot as bot

            # prepara variable de entorno según non_interactive
            if non_interactive is not None:
                if non_interactive:
                    os.environ["BOLSA_NON_INTERACTIVE"] = "1"
                else:
                    os.environ.pop("BOLSA_NON_INTERACTIVE", None)

            # si hay página activa → recargar; si no → ejecutar flujo completo
            if bot.get_active_page():
                logger.info("Recargando navegador activo con Playwright.")
                bot.configure_run_specific_logging(bot.logger_instance_global)
                success, json_path = bot.refresh_active_page(bot.logger_instance_global)
            else:
                try:
                    bot.validate_credentials()
                except Exception as cred_err:
                    logger.warning("Credenciales no configuradas: %s", cred_err)
                bot.configure_run_specific_logging(bot.logger_instance_global)
                asyncio.run(
                    bot.run_automation(
                        bot.logger_instance_global,
                        non_interactive=os.getenv("BOLSA_NON_INTERACTIVE") == "1",
                        keep_open=keep_open,
                    )
                )
                success, json_path = bot.refresh_active_page(bot.logger_instance_global)

            if not success or not json_path:
                from src.routes.errors import log_error
                logger.error("No se obtuvo JSON fresco; usando último disponible.")
                log_error("service", "No se pudo obtener datos frescos")
                fallback = prev_file or get_latest_json_file()
                if fallback and os.path.exists(fallback):
                    store_prices_in_db(fallback, app=app)
                    return fallback
                return None

            new_hash, _ = get_json_hash_and_timestamp(json_path)
            if prev_hash and new_hash == prev_hash and not force_update:
                logger.warning("El JSON recién capturado es idéntico al anterior.")
                socketio.emit(
                    "no_new_data",
                    {"timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")},
                )
                return None

            store_prices_in_db(json_path, app=app)
            return json_path
        except Exception as e:
            logger.exception("Error en run_bolsa_bot: %s", e)
            return None
        finally:
            with bot_lock:
                bot_running = False
            logger.info("=== FIN DE SCRAPING ===")


def get_latest_data():
    """
    Devuelve datos más recientes (archivo JSON o DB).  Ejecuta bot si es necesario.
    """
    try:
        latest_entry = StockPrice.query.order_by(StockPrice.timestamp.desc()).first()
        ts_db = latest_entry.timestamp if latest_entry else None

        latest_json_path = get_latest_json_file()
        if not latest_json_path and not is_bot_running():
            latest_json_path = run_bolsa_bot()
        elif latest_json_path and not os.path.exists(latest_json_path) and not is_bot_running():
            latest_json_path = run_bolsa_bot()

        if latest_json_path and os.path.exists(latest_json_path):
            ts_file = extract_timestamp_from_filename(latest_json_path)
            ts_file_dt = datetime.strptime(ts_file, "%d/%m/%Y %H:%M:%S")
            if ts_db and ts_file_dt <= ts_db:
                prices = StockPrice.query.filter_by(timestamp=ts_db).all()
                return {
                    "data": [p.to_dict() for p in prices],
                    "timestamp": ts_db.strftime("%d/%m/%Y %H:%M:%S"),
                    "source": "db",
                }

            with open(latest_json_path, "r", encoding="utf-8") as f:
                data_content = json.load(f)
            rows = (
                data_content["listaResult"]
                if isinstance(data_content, dict) and "listaResult" in data_content
                else data_content
            )
            return {
                "data": rows,
                "timestamp": ts_file,
                "source": latest_json_path,
            }

        if ts_db:
            prices = StockPrice.query.filter_by(timestamp=ts_db).all()
            return {
                "data": [p.to_dict() for p in prices],
                "timestamp": ts_db.strftime("%d/%m/%Y %H:%M:%S"),
                "source": "db",
            }

        from src.routes.errors import log_error
        log_error("service", "No se hallaron datos disponibles")
        return {"error": "Sin datos", "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    except Exception as e:
        from src.routes.errors import log_error
        logger.exception("Error en get_latest_data: %s", e)
        log_error("service", str(e), traceback.format_exc())
        return {"error": str(e), "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}


def filter_stocks(stock_codes: List[str]):
    """
    Filtra lista de acciones por NEMO/código.
    """
    try:
        latest = get_latest_data()
        if "error" in latest:
            return latest

        stocks_list = latest["data"]
        if not stock_codes:
            return {
                "data": stocks_list,
                "timestamp": latest["timestamp"],
                "count": len(stocks_list),
                "source": latest["source"],
            }

        wanted = [c.upper().strip() for c in stock_codes if isinstance(c, str) and c.strip()]
        def get_symbol(item):
            if not isinstance(item, dict):
                return ""
            for k, v in item.items():
                if isinstance(k, str) and re.search(r"(nemo|symbol)", k, re.IGNORECASE):
                    return str(v).strip().upper()
            return ""

        filtered = [s for s in stocks_list if get_symbol(s) in wanted]
        logger.info(
            "Filtradas %s de %s acciones (%s).",
            len(filtered),
            len(stocks_list),
            ", ".join(wanted),
        )
        return {
            "data": filtered,
            "timestamp": latest["timestamp"],
            "count": len(filtered),
            "source": latest["source"],
        }
    except Exception as e:
        logger.exception("Error en filter_stocks: %s", e)
        return {"error": str(e), "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}


def compare_last_two_db_entries():
    """Compara los dos últimos registros de precios en la base de datos."""
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

        changes, unchanged = [], []
        for sym in curr_map.keys() & prev_map.keys():
            curr, prev = curr_map[sym], prev_map[sym]
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
            "current_ts": ts_curr.strftime("%d/%m/%Y %H:%M:%S"),
            "previous_ts": ts_prev.strftime("%d/%m/%Y %H:%M:%S"),
            "new": [curr_map[s].to_dict() for s in new_syms],
            "removed": [prev_map[s].to_dict() for s in removed_syms],
            "changes": changes,
            "unchanged": unchanged,
            "total_compared": len(curr_map.keys() | prev_map.keys()),
            "change_count": len(changes),
        }
        return result
    except Exception as exc:
        logger.exception("Error comparando históricos: %s", exc)
        return {}


def update_data_periodically(min_interval_s: int, max_interval_s: int, app=None):
    """Hilo que ejecuta actualizaciones periódicas (intervalo aleatorio)."""
    global stop_update_thread
    logger.info(
        "Hilo periódico iniciado (intervalo %s–%s s).", min_interval_s, max_interval_s
    )
    while not stop_update_thread:
        try:
            logger.info("Lanzando actualización periódica…")
            if not is_bot_running():
                run_bolsa_bot(app=app)
            else:
                logger.info("Se omite: bot ya en curso.")

            interval = random.randint(min_interval_s, max_interval_s)
            logger.info("Próxima actualización en %s s.", interval)
            for _ in range(interval):
                if stop_update_thread:
                    logger.info("Detención solicitada.")
                    break
                time.sleep(1)
        except Exception as e:
            logger.exception("Error en actualización periódica: %s", e)
            time.sleep(60)
    _safe_log("info", "Hilo periódico detenido.")


def start_periodic_updates(min_minutes: int = 15, max_minutes: int = 45, app=None) -> bool:
    """
    Lanza un hilo de actualizaciones periódicas.
    """
    global update_thread, stop_update_thread
    if update_thread and update_thread.is_alive():
        logger.info("Hilo periódico ya ejecutándose.")
        return False

    stop_update_thread = False
    update_thread = threading.Thread(
        target=update_data_periodically,
        args=(min_minutes * 60, max_minutes * 60, app),
        daemon=True,
    )
    update_thread.start()
    logger.info("Actualización periódica iniciada.")
    return True


def stop_periodic_updates() -> bool:
    global stop_update_thread, update_thread
    if not update_thread or not update_thread.is_alive():
        _safe_log("info", "No hay hilo periódico activo.")
        return True

    stop_update_thread = True
    update_thread.join(timeout=10)
    if update_thread.is_alive():
        _safe_log("warning", "El hilo periódico no terminó limpiamente.")
    else:
        _safe_log("info", "Hilo periódico detenido.")
    update_thread = None
    return True
