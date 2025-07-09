import json
import logging
import os 
from datetime import datetime, timezone

module_logger = logging.getLogger(__name__ + ".har_analyzer")
if not module_logger.handlers: 
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[HAR_ANALYZER - %(levelname)s] %(message)s'))
    module_logger.addHandler(handler)
    module_logger.setLevel(logging.INFO)


def analyze_har_and_extract_data(har_filepath, primary_api_url_patterns, other_urls_to_log, output_data_filepath, output_summary_filepath, logger_param=None):
    logger = logger_param or module_logger
    logger.info(f"Analizando archivo HAR: {har_filepath}")
    
    data_saved = False
    summary_list = []

    try:
        with open(har_filepath, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        entries = har_data.get("log", {}).get("entries", [])
        
        for i, entry in enumerate(entries):
            req_url = entry.get("request", {}).get("url", "")
            if not req_url: continue

            if "api/Securities/csrfToken" in req_url or req_url.endswith(('.css', '.js', '.png', '.woff2')):
                continue
            
            content = entry.get("response", {}).get("content", {})
            text = content.get("text", "") 
            status = entry.get("response", {}).get("status")

            is_primary = any(p in req_url for p in primary_api_url_patterns)
            is_other = any(o in req_url for o in other_urls_to_log if not any(p in o for p in primary_api_url_patterns))
            
            if is_primary or is_other:
                name = "API Principal de Acciones" if is_primary else "API de Contexto"
                logger.info(f"HAR: Petición a '{name}' (Entrada #{i}): {req_url} - Status: {status}")

                summary = {
                    "entry_index": i, "name_desc": name, "url": req_url, "status": status,
                    "response_mime": content.get("mimeType"), "response_size": content.get("size"),
                }
                
                if status == 200 and "application/json" in str(summary["response_mime"]) and text:
                    try:
                        parsed_json = json.loads(text)
                        summary["data_json"] = parsed_json

                        if "getEstadoSesionUsuario" in req_url and isinstance(parsed_json, dict):
                            exp_val = parsed_json.get("tiempoRestante") or parsed_json.get("expiration")
                            if exp_val:
                                summary["session_remaining_seconds"] = int(exp_val)
                                logger.info(f"HAR: Sesión expira en {exp_val}s según {req_url}")

                        if is_primary and not data_saved:
                            with open(output_data_filepath, 'w', encoding='utf-8') as f_out:
                                json.dump(parsed_json, f_out, indent=2, ensure_ascii=False)
                            logger.info(f"*** DATOS PRINCIPALES GUARDADOS EN: {output_data_filepath} ***")
                            data_saved = True
                    except json.JSONDecodeError:
                        summary["data_preview"] = f"Error: JSON inválido. Preview: {text[:200]}"
                        logger.warning(f"No se pudo parsear JSON de {req_url}")

                elif text and ("<html" in text.lower() and ("captcha" in text.lower() or "radware" in text.lower())):
                    summary["is_captcha"] = True
                    logger.warning(f"Página de CAPTCHA detectada en {req_url}")
                
                summary_list.append(summary)
        
        if not data_saved:
            logger.warning(f"No se encontraron datos JSON válidos para las APIs principales en el HAR.")

    except FileNotFoundError:
        logger.error(f"Archivo HAR no encontrado: {har_filepath}")
    except Exception as e:
        logger.exception("Error inesperado al analizar el archivo HAR:")
    
    try:
        with open(output_summary_filepath, 'w', encoding='utf-8') as f_summary:
            json.dump(summary_list, f_summary, indent=2, ensure_ascii=False)
        logger.info(f"Resumen de análisis del HAR guardado en: {output_summary_filepath}")
    except Exception as e:
        logger.error(f"No se pudo guardar el resumen del HAR: {e}")