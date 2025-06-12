
"""utils/json_utils.py
Funciones auxiliares para trabajar con archivos JSON de precios de acciones.
Extraídas de bolsa_service.py sin modificar la lógica original.
"""
from __future__ import annotations
import os, re, json, hashlib, glob
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import logging
from src.config import LOGS_DIR

logger = logging.getLogger(__name__)

def get_latest_json_file() -> Optional[str]:
    """Devuelve el archivo JSON más reciente `acciones-precios-plus_*.json`."""
    try:
        pattern = os.path.join(LOGS_DIR, "acciones-precios-plus_*.json")
        json_files = [f for f in glob.glob(pattern)]
        if not json_files:
            logger.warning("No se encontraron 'acciones-precios-plus_*.json' en %s", LOGS_DIR)
            return None
        return max(json_files, key=os.path.getmtime)
    except Exception as e:
        logger.exception("Error al buscar JSON más reciente: %s", e)
        return None

def extract_timestamp_from_filename(filename: str) -> str:
    """Extrae timestamp del nombre 'acciones-precios-plus_YYYYMMDD_HHMMSS.json'."""
    try:
        base = os.path.basename(filename)
        m = re.search(r"acciones-precios-plus_(\d{8})_(\d{6})\.json", base)
        if m:
            date_str, time_str = m.groups()
            dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        stat = os.stat(filename)
        return datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
    except Exception as e:
        logger.exception("Error al extraer timestamp: %s", e, exc_info=False)
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def get_json_hash_and_timestamp(path: str) -> Tuple[Optional[str], Optional[str]]:
    """Devuelve (md5, timestamp ISO) de un JSON."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = None
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(k, str) and any(kw in k.lower() for kw in ("time", "fecha", "stamp")):
                    ts = str(v); break
        if ts:
            from datetime import datetime as _dt
            try: _dt.fromisoformat(ts)
            except Exception: ts = None
        if not ts:
            ts = datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
        hash_val = hashlib.md5(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()
        return hash_val, ts
    except Exception:
        return None, None
