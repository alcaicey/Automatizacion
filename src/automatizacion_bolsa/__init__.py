"""
Paquete «automatizacion_bolsa»

Reexporta de forma controlada las funciones públicas que necesitan otros
módulos del proyecto, evitando dependencias circulares con *run_automation*.

• run_automation        →  se importa *perezosamente* cuando se solicita,
                           porque su propio módulo importa a su vez partes de
                           este paquete.
• refresh_active_page   →  no genera ciclos, se importa de inmediato.
• clean_percentage      →  idem.
"""

# ─── Reexportaciones *no* problemáticas ─────────────────────────────────────────
from .page_refresh import refresh_active_page
from .utils import clean_percentage

# ─── Exportaciones disponibles mediante `from … import *` ───────────────────────
__all__ = ["run_automation", "refresh_active_page", "clean_percentage"]

# ─── Import perezoso para romper el ciclo con run_automation.py ────────────────
def __getattr__(name: str):
    """
    Solo cuando alguien accede a `automatizacion_bolsa.run_automation`
    importamos el módulo correspondiente y devolvemos la función.
    """
    if name == "run_automation":
        # Import local para no ejecutar el módulo hasta que sea necesario
        from .run_automation import run_automation as _run_automation
        return _run_automation
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ─── Mejora: hacer que dir() muestre los símbolos reexportados ─────────────────
def __dir__() -> list[str]:  # pragma: no cover
    return sorted(list(globals().keys()) + __all__)
