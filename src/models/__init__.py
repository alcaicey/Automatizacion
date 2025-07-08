# src/models/__init__.py
"""
Este paquete contiene todos los modelos de la base de datos SQLAlchemy.
La importación de todos los modelos aquí permite que SQLAlchemy los descubra
automáticamente al inicializar la aplicación.
"""
from .advanced_kpi import AdvancedKPI
from .alert import Alert
from .anomalous_event import AnomalousEvent
from .closing_column_preference import ClosingColumnPreference
from .column_preference import ColumnPreference
from .credentials import Credential
from .dividend_column_preference import DividendColumnPreference
from .dividend import Dividend
from .filtered_stock_history import FilteredStockHistory
from .kpi_column_preference import KpiColumnPreference
from .kpi_selection import KpiSelection
from .last_update import LastUpdate
from .log_entry import LogEntry
from .portfolio_column_preference import PortfolioColumnPreference
from .portfolio import Portfolio
from .prompt_config import PromptConfig
from .stock_closing import StockClosing
from .stock_filter import StockFilter
from .stock_price import StockPrice
from .user import User
