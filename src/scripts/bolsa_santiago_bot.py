"""Archivo corregido y mejorado: Automatización Bolsa Santiago"""

import logging
import os
import random
import asyncio
from playwright.async_api import async_playwright

from src.config import (
    INITIAL_PAGE_URL,
    TARGET_DATA_PAGE_URL,
    USERNAME,
    PASSWORD,
    USERNAME_SELECTOR,
    PASSWORD_SELECTOR,
    LOGIN_BUTTON_SELECTOR,
    API_PRIMARY_DATA_PATTERNS,
    URLS_TO_INSPECT_IN_HAR_FOR_CONTEXT,
    MIS_CONEXIONES_TITLE_SELECTOR,
    CERRAR_TODAS_SESIONES_SELECTOR,
    STORAGE_STATE_PATH,
    LOGS_DIR,
)
from src.scripts.har_analyzer import analyze_har_and_extract_data

from src.automatizacion_bolsa import run_automation as _run_automation
from src.automatizacion_bolsa.page_refresh import refresh_active_page
from src.automatizacion_bolsa import clean_percentage
from src.automatizacion_bolsa.playwright_session import (
    create_page,
    get_active_page,
    close_resources as close_playwright_resources,
)
from src.automatizacion_bolsa.data_capture import (
    capture_premium_data_via_network,
    fetch_premium_data,
)
from src.automatizacion_bolsa.config_loader import (
    logger,
    configure_run_specific_logging,
    validate_credentials,
    timestamp as TIMESTAMP_NOW,
)
from src.automatizacion_bolsa.resources import (
    HAR_FILENAME,
    OUTPUT_ACCIONES_DATA_FILENAME,
    ANALYZED_SUMMARY_FILENAME,
    DEFAULT_USER_AGENT,
    MIN_EXPECTED_RESULTS,
)

logger_instance_global = logger


async def run_automation(
    log_instance: logging.Logger,
    max_attempts: int = 1,
    non_interactive: bool | None = None,
    keep_open: bool = True,
):
    return await _run_automation(
        log_instance,
        max_attempts=max_attempts,
        non_interactive=non_interactive,
        keep_open=keep_open,
        capture_func=capture_premium_data_via_network,
        fetch_func=fetch_premium_data,
        async_pw=async_playwright,
        sleep_func=asyncio.sleep,
        input_func=input,
    )


__all__ = [
    "run_automation",
    "refresh_active_page",
    "clean_percentage",
    "create_page",
    "get_active_page",
    "close_playwright_resources",
    "capture_premium_data_via_network",
    "fetch_premium_data",
    "logger_instance_global",
    "TIMESTAMP_NOW",
    "HAR_FILENAME",
    "OUTPUT_ACCIONES_DATA_FILENAME",
    "ANALYZED_SUMMARY_FILENAME",
    "DEFAULT_USER_AGENT",
    "MIN_EXPECTED_RESULTS",
    "configure_run_specific_logging",
    "validate_credentials",
]
