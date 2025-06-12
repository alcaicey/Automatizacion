
"""
browser_refresh.py
------------------
Utilidades independientes para localizar una instancia de Chromium 139.x y
simular CTRL+L → ENTER para refrescar la pestaña activa.

Estas funciones NO dependen de la base de datos ni de Playwright.
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Optional

import psutil
import pyautogui

try:
    import pygetwindow as gw  # solo necesario en Windows
except ImportError:  # pragma: no cover
    gw = None  # type: ignore

logger = logging.getLogger(__name__)

CHROMIUM_VERSION_PREFIX = "139."
PROCESS_NAMES = {"chrome", "chrome.exe", "chromium", "chromium.exe"}


# ───────────────────────────── helper versión ─────────────────────────────
def _match_version(proc: psutil.Process) -> bool:
    """Devuelve True si `proc` es Chromium 139.x (o compatible)."""
    try:
        if sys.platform.startswith("win"):
            import win32api  # pywin32
            info = win32api.GetFileVersionInfo(proc.exe(), "\\")
            ms, ls = info["FileVersionMS"], info["FileVersionLS"]
            ver = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
            return ver.startswith(CHROMIUM_VERSION_PREFIX)
        # Linux/macOS: sin metadatos, se acepta por nombre
        return True
    except Exception:  # pragma: no cover
        return False


# ────────────────── localizar un proceso Chromium vivo ────────────────────
def find_chromium_process() -> Optional[psutil.Process]:
    """Devuelve la primera instancia de Chromium 139.x, o None."""
    for proc in psutil.process_iter(["name", "exe"]):
        if proc.info["name"] in PROCESS_NAMES and _match_version(proc):
            return proc
    return None


# ───────────────────── refrescar pestaña activa ───────────────────────────
def refresh_chromium_tab(proc: psutil.Process) -> bool:
    """Trae la ventana al frente y envía CTRL+L → ENTER."""
    logger.info("Simulando ENTER en Chromium (PID %s)", proc.pid)
    try:
        if sys.platform.startswith("win") and gw is not None:
            wins = gw.getWindowsWithTitle("Chromium")
            if wins:
                wins[0].activate()
                time.sleep(0.3)

        pyautogui.hotkey("ctrl", "l")
        time.sleep(0.2)
        pyautogui.press("enter")
        return True
    except Exception as exc:  # pragma: no cover
        logger.error("No se pudo refrescar Chromium: %s", exc)
        return False
