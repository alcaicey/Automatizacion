# src/models/__init__.py

# El __init__.py en la carpeta de modelos sirve para que Python reconozca el
# directorio como un paquete. También es un buen lugar para definir el
# __all__, que controla qué se importa con 'from src.models import *'.

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
from .advanced_kpi import AdvancedKPI
from .kpi_selection import KpiSelection 
from .prompt_config import PromptConfig 
from .kpi_column_preference import KpiColumnPreference
from .portfolio_column_preference import PortfolioColumnPreference
from .anomalous_event import AnomalousEvent

__all__ = [
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
    "AdvancedKPI",
    "KpiSelection", 
    "PromptConfig",
    "KpiColumnPreference",
    "PortfolioColumnPreference",
    "AnomalousEvent",
]

# src/models/__init__.py
# ... (imports existentes)
