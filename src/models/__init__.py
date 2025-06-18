# Este archivo sirve para que Python reconozca el directorio 'models' como un paquete.
# No es necesario que contenga código, pero podemos usarlo para facilitar las importaciones.

from .user import User
from .stock_price import StockPrice
from .credentials import Credential
from .column_preference import ColumnPreference
from .stock_filter import StockFilter
from .last_update import LastUpdate
from .log_entry import LogEntry
from .alert import Alert


# El __all__ define qué se importa cuando se hace 'from src.models import *'
__all__ = [
    "db",
    "User",
    "StockPrice",
    "Credential",
    "ColumnPreference",
    "StockFilter",
    "LastUpdate",
    "LogEntry",
    "Alert",
]