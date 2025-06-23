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
from .portfolio import Portfolio
from .filtered_stock_history import FilteredStockHistory
from .dividend import Dividend
from .dividend_column_preference import DividendColumnPreference
from .stock_closing import StockClosing
from .closing_column_preference import ClosingColumnPreference

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
    "Portfolio",
    "FilteredStockHistory", 
    "Dividend",
    "DividendColumnPreference",
    "StockClosing",
    "ClosingColumnPreference",
]