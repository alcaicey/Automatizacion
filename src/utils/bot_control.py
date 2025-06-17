"""
Compatibilidad: expone run_bolsa_bot / is_bot_running sin ciclos de importación.
Las funciones reales están en ``src.scripts.bolsa_service``.
El import se hace *dentro* de cada wrapper (lazy import) para evitar
circular dependencies con utils.db_io.
"""

from __future__ import annotations
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
