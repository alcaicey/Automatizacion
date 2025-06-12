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
    getattr(logger, level)(msg, *args, **kwargs) 

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
