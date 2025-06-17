# ───────────────────────────────  src/utils/browser_utils.py  ─────────────────────
"""
Utilidades para localizar una instancia abierta de Chromium 139.x y simular un
ENTER en la barra de direcciones, refrescando la página activa.
"""
from __future__ import annotations

import logging
import sys
import time
from typing import Optional

import psutil
import pyautogui

CHROMIUM_VERSION_PREFIX = "139."         # se valida solo el prefijo mayor
PROCESS_NAMES = {"chrome.exe", "chromium.exe", "chrome", "chromium"}
TIMEOUT_SEC = 15


def _match_version(proc: psutil.Process) -> bool:
    """
    Devuelve True si el ejecutable coincide con la versión 139.x.
    En Linux/Mac no suele incluir metadatos, por eso solo validamos el nombre.
    """
    try:
        if sys.platform.startswith("win"):
            # En Windows, extraemos la versión del ejecutable.
            import win32api  # pywin32
            info = win32api.GetFileVersionInfo(proc.exe(), "\\")
            ms, ls = info["FileVersionMS"], info["FileVersionLS"]
            ver = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
            return ver.startswith(CHROMIUM_VERSION_PREFIX)
        # Otros SO: basta con el nombre.
        return True
    except Exception:  # pragma: no cover
        return False


def find_chromium_process() -> Optional[psutil.Process]:
    """Localiza la primera instancia viva de Chromium 139.x."""
    for proc in psutil.process_iter(["name", "exe"]):
        if proc.info["name"] in PROCESS_NAMES and _match_version(proc):
            return proc
    return None


def refresh_chromium_tab(proc: psutil.Process) -> bool:
    """
    Trae al frente la ventana de `proc` y envía CTRL+L → ENTER.
    Devuelve True si se pudo enviar la secuencia; False en caso contrario.
    """
    logging.info("[3] Simulando ENTER en Chromium (PID %s)", proc.pid)
    try:
        if sys.platform.startswith("win"):
            # Traer la ventana al frente (solo Windows).
            import pygetwindow as gw
            win = gw.getWindowsWithTitle("Chromium")[0]
            win.activate()
            time.sleep(0.3)

        pyautogui.hotkey("ctrl", "l")   # foco en la URL
        time.sleep(0.2)
        pyautogui.press("enter")        # refresco
        return True
    except Exception as exc:            # pragma: no cover
        logging.error("[ERR] No se pudo refrescar Chromium: %s", exc)
        return False
# ───────────────────────────────────────────────────────────────────────────────────
