from __future__ import annotations

"""
Compatibilidad: expone run_bolsa_bot / is_bot_running sin ciclos de importación.
Las funciones reales están en ``src.scripts.bolsa_service``.
El import se hace *dentro* de cada wrapper (lazy import) para evitar
circular dependencies con utils.db_io.
"""

import asyncio
import logging
from flask import current_app

from src.extensions import socketio

# Mantenemos un lock global para evitar múltiples ejecuciones síncronas
# que podrían competir por recursos (ej. hilos).
# NOTA: Este lock no previene ejecuciones asíncronas del bot,
# las cuales se gestionan con su propio lock en bolsa_service.
_sync_bot_running_lock = None

from src.services import bolsa_service          # import here = no cycle

logger = logging.getLogger(__name__)


from typing import Any, Callable

def _lazy(attr_name: str) -> Callable[..., Any]:       # helper interno
    def _wrapper(*args, **kwargs):
        from src.scripts import bolsa_service          # import here = no cycle
        real_fn = getattr(bolsa_service, attr_name)
        return real_fn(*args, **kwargs)
    _wrapper.__name__ = attr_name
    _wrapper.__doc__  = f"Lazy proxy for bolsa_service.{attr_name}()"
    return _wrapper

run_bolsa_bot  = _lazy("run_bolsa_bot")
is_bot_running = _lazy("is_bot_running")

__all__ = ["run_bolsa_bot", "is_bot_running"]
