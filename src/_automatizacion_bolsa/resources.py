import os
from src.config import LOGS_DIR
from .config_loader import timestamp

HAR_FILENAME = os.path.join(LOGS_DIR, "network_capture.har")
OUTPUT_ACCIONES_DATA_FILENAME = os.path.join(
    LOGS_DIR, f"acciones-precios-plus_{timestamp}.json"
)
ANALYZED_SUMMARY_FILENAME = os.path.join(
    LOGS_DIR, f"network_summary_{timestamp}.json"
)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

MIN_EXPECTED_RESULTS = 5

__all__ = [
    "HAR_FILENAME",
    "OUTPUT_ACCIONES_DATA_FILENAME",
    "ANALYZED_SUMMARY_FILENAME",
    "DEFAULT_USER_AGENT",
    "MIN_EXPECTED_RESULTS",
]