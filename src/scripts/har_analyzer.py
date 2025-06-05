import json
import logging
import os # Necesario para os.path.join

# Este logger se usará si la función es llamada sin un logger_param explícito.
# Es bueno tener un logger por defecto para el módulo.
module_logger = logging.getLogger(__name__ + ".har_analyzer")
if not module_logger.handlers: # Evitar añadir handlers múltiples si este módulo se importa varias veces
    module_stream_handler = logging.StreamHandler()
    module_stream_handler.setFormatter(logging.Formatter('[HAR_ANALYZER - %(levelname)s] %(asctime)s - %(message)s'))
    module_logger.addHandler(module_stream_handler)
    module_logger.setLevel(logging.INFO)


def analyze_har_and_extract_data(har_filepath, primary_api_url_patterns, other_urls_to_log, output_data_filepath, output_summary_filepath, logger_param=None):
    effective_logger = logger_param or module_logger
    effective_logger.info(f"Analizando archivo HAR: {har_filepath}")
    
    target_api_response_found_and_saved = False
    all_relevant_requests_summary = []

    try:
        with open(har_filepath, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        entries = har_data.get("log", {}).get("entries", [])
        
        for entry_index, entry in enumerate(entries):
            request_url = entry.get("request", {}).get("url", "")
            response_content = entry.get("response", {}).get("content", {})
            response_text = response_content.get("text", "") 
            response_text = response_text or "" 
            status = entry.get("response", {}).get("status")
            method = entry.get("request", {}).get("method")

            is_primary_target = any(pattern in request_url for pattern in primary_api_url_patterns)
            # Asegurar que other_urls_to_log no contenga los patrones primarios para evitar doble logueo con diferente nombre
            effective_other_urls = [url for url in other_urls_to_log if not any(p_pattern in url for p_pattern in primary_api_url_patterns)]
            is_other_relevant = any(other_url in request_url for other_url in effective_other_urls)
            
            name_desc = ""
            if is_primary_target: name_desc = "API de Datos Principal de Acciones"
            elif is_other_relevant: name_desc = "API de Contexto Relevante"

            if name_desc:
                effective_logger.info(f"HAR: Encontrada solicitud a '{name_desc}' (Entrada #{entry_index}): {method} {request_url} - Status: {status}")
                summary = {
                    "entry_index": entry_index,
                    "name_desc": name_desc,
                    "actual_url": request_url,
                    "method": method,
                    "status": status,
                    "request_headers": {h["name"]: h["value"] for h in entry.get("request", {}).get("headers", [])},
                    "response_headers": {h["name"]: h["value"] for h in entry.get("response", {}).get("headers", [])},
                    "response_content_mime": response_content.get("mimeType"),
                    "response_content_size": response_content.get("size"),
                }
                
                if status == 200 and summary["response_content_mime"] and "application/json" in summary["response_content_mime"] and response_text:
                    try:
                        parsed_json = json.loads(response_text)
                        summary["data_json"] = parsed_json # Guardar el JSON completo para el resumen
                        if is_primary_target and not target_api_response_found_and_saved:
                            target_api_response_found_and_saved = True
                            with open(output_data_filepath, 'w', encoding='utf-8') as f_out_data:
                                json.dump(parsed_json, f_out_data, indent=2, ensure_ascii=False)
                            effective_logger.info(f"*** DATOS DE ACCIONES COMPLETOS GUARDADOS EN: {output_data_filepath} desde {request_url} ***")
                    except json.JSONDecodeError:
                        summary["data_preview"] = f"Error: No se pudo parsear JSON. Preview: {response_text[:200]}"
                        effective_logger.warning(f"No se pudo parsear JSON para {request_url}. Preview: {response_text[:200]}")
                elif "<html" in response_text.lower() and ("captcha" in response_text.lower() or "radware" in response_text.lower()):
                    summary["is_captcha_page"] = True
                    summary["data_preview"] = response_text[:200] + "..."
                    effective_logger.warning(f"Se recibió página de CAPTCHA para {request_url}")
                else: 
                    summary["data_preview"] = response_text[:500] + ("..." if len(response_text) > 500 else "")
                
                all_relevant_requests_summary.append(summary)
        
        if not target_api_response_found_and_saved:
            effective_logger.warning(f"No se encontraron datos JSON válidos para las APIs de datos de acciones objetivo ({primary_api_url_patterns}) en el HAR.")

    except FileNotFoundError:
        effective_logger.error(f"Archivo HAR no encontrado: {har_filepath}")
    except json.JSONDecodeError:
        effective_logger.error(f"Error al decodificar el archivo HAR (no es JSON válido): {har_filepath}")
    except Exception as e:
        effective_logger.exception("Error inesperado al analizar el archivo HAR:")
    
    try:
        with open(output_summary_filepath, 'w', encoding='utf-8') as f_out_summary:
            json.dump(all_relevant_requests_summary, f_out_summary, indent=2, ensure_ascii=False)
        effective_logger.info(f"Resumen de análisis del HAR guardado en: {output_summary_filepath}")
    except Exception as e_save_summary:
        effective_logger.error(f"No se pudo guardar el resumen del análisis del HAR: {e_save_summary}")