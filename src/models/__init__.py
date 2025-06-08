from flask_sqlalchemy import SQLAlchemy

# Base de datos
db = SQLAlchemy()

# Import models to ensure they are registered with SQLAlchemy
from .user import User  # noqa: E402,F401
from .stock_price import StockPrice  # noqa: E402,F401
from .credentials import Credential  # noqa: E402,F401
