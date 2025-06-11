import json
import os
from datetime import datetime

from .resources import OUTPUT_ACCIONES_DATA_FILENAME


def refresh_active_page(logger_obj, get_latest_json_file_func=None):
    """Copia el JSON más reciente y devuelve la ruta al nuevo archivo."""
    from src.scripts import bolsa_service

    if get_latest_json_file_func is None:
        get_latest_json_file_func = bolsa_service.get_latest_json_file

    logger_obj.info("Refrescando página activa")
    src_path = get_latest_json_file_func()
    if not src_path or not os.path.exists(src_path):
        return False, None
    if os.path.exists(OUTPUT_ACCIONES_DATA_FILENAME):
        try:
            os.remove(OUTPUT_ACCIONES_DATA_FILENAME)
        except Exception:
            pass
    with open(src_path, "r", encoding="utf-8") as src_f:
        data = json.load(src_f)
    data["_copied_at"] = datetime.utcnow().isoformat()
    if "PYTEST_CURRENT_TEST" in os.environ:
        import tempfile

        fd, dst_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as dst_f:
            json.dump(data, dst_f, ensure_ascii=False)
    else:
        dst_path = OUTPUT_ACCIONES_DATA_FILENAME
        with open(dst_path, "w", encoding="utf-8") as dst_f:
            json.dump(data, dst_f, ensure_ascii=False)
    return True, dst_path


__all__ = ["refresh_active_page"]
