import os
import json
import logging
import time
import subprocess
from datetime import datetime
import threading
import re
import glob
import random # Asegurarse de que random esté importado

# Configuración de rutas obtenidas desde variables de entorno
SCRIPTS_DIR = os.environ.get("BOLSA_SCRIPTS_DIR")
if not SCRIPTS_DIR:
    raise ValueError("Environment variable BOLSA_SCRIPTS_DIR must be set")

LOGS_DIR = os.environ.get("BOLSA_LOGS_DIR", os.path.join(SCRIPTS_DIR, "logs_bolsa"))

# Configuración de logging para este script de servicio/orquestador
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Crear directorio de logs para este script si no existe (diferente al de bolsa_santiago_bot.py)
service_log_dir = os.path.join(SCRIPTS_DIR, "service_logs")
os.makedirs(service_log_dir, exist_ok=True)
service_log_file = os.path.join(service_log_dir, "bolsa_service.log")

file_handler = logging.FileHandler(service_log_file, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s'))
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s'))

# Evitar añadir handlers múltiples si el script se recarga o se llama a la configuración varias veces
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

# Variable para controlar el hilo de actualización
update_thread = None
stop_update_thread = False

def get_latest_json_file():
    """
    Obtiene el archivo JSON de datos de acciones más reciente del directorio de logs
    generado por bolsa_santiago_bot.py.
    """
    try:
        # Patrón para los archivos JSON de datos de acciones
        pattern = os.path.join(LOGS_DIR, "acciones-precios-plus_*.json")
        
        json_files = glob.glob(pattern)
        
        if not json_files:
            logger.warning(f"No se encontraron archivos 'acciones-precios-plus_*.json' en {LOGS_DIR}")
            return None
        
        latest_json = max(json_files, key=os.path.getmtime)
        logger.info(f"Archivo JSON de datos más reciente encontrado: {latest_json}")
        return latest_json
    
    except Exception as e:
        logger.exception(f"Error al buscar el archivo JSON de datos más reciente: {e}")
        return None

def extract_timestamp_from_filename(filename):
    """
    Extrae el timestamp del nombre del archivo
    Formato esperado: acciones-precios-plus_AAAAMMDD_HHMMSS.json
    """
    try:
        base_name = os.path.basename(filename)
        match = re.search(r'acciones-precios-plus_(\d{8})_(\d{6})\.json', base_name)
        
        if match:
            date_str, time_str = match.groups()
            dt_obj = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
            return dt_obj.strftime("%d/%m/%Y %H:%M:%S")
        
        # Fallback si el patrón no coincide, usar fecha de modificación del archivo
        stat = os.stat(filename)
        return datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
    
    except Exception as e:
        logger.exception(f"Error al extraer timestamp del nombre de archivo '{filename}': {e}")
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S") # Fallback a ahora

def run_bolsa_bot():
    """
    Ejecuta el script bolsa_santiago_bot.py y devuelve la ruta al archivo JSON de datos generado.
    """
    try:
        logger.info("Iniciando ejecución de bolsa_santiago_bot.py para obtener datos frescos...")
        script_path = os.path.join(SCRIPTS_DIR, "bolsa_santiago_bot.py")
        
        if not os.path.exists(script_path):
            logger.error(f"El script 'bolsa_santiago_bot.py' no existe en: {script_path}")
            return None
        
        # Usar Popen para no bloquear y poder capturar stdout/stderr si es necesario más adelante
        # o call/run para esperar a que termine. Por ahora, run es más simple si esperamos.
        logger.info(f"Ejecutando: python \"{script_path}\" en el directorio {SCRIPTS_DIR}")
        process = subprocess.run(
            ["python", script_path], 
            capture_output=True, # Captura stdout y stderr
            text=True, 
            cwd=SCRIPTS_DIR, # Directorio de trabajo para el script
            check=False # No lanzar excepción si el script falla, lo manejamos con returncode
        )
        
        if process.stdout:
            logger.info(f"Salida de bolsa_santiago_bot.py:\n{process.stdout[-1000:]}") # Últimos 1000 caracteres
        if process.stderr:
            logger.error(f"Errores de bolsa_santiago_bot.py:\n{process.stderr}")

        if process.returncode != 0:
            logger.error(f"bolsa_santiago_bot.py terminó con código de error: {process.returncode}")
            return None
        
        latest_json = get_latest_json_file() # Busca el archivo generado por el bot
        
        if latest_json:
            logger.info(f"bolsa_santiago_bot.py ejecutado, datos actualizados en: {latest_json}")
            return latest_json
        else:
            logger.error("bolsa_santiago_bot.py ejecutado, pero no se encontró el archivo JSON de datos esperado.")
            return None
    
    except Exception as e:
        logger.exception(f"Error en run_bolsa_bot: {e}")
        return None

def get_latest_data():
    """
    Obtiene los datos más recientes del archivo JSON de acciones.
    Si no existe, intenta ejecutar el bot para generarlo.
    """
    try:
        latest_json_path = get_latest_json_file()
        
        if not latest_json_path or not os.path.exists(latest_json_path):
            logger.warning("No existe archivo de datos o no es accesible. Ejecutando scraping...")
            latest_json_path = run_bolsa_bot() # Intentar generar uno nuevo
            
        if latest_json_path and os.path.exists(latest_json_path):
            with open(latest_json_path, 'r', encoding='utf-8') as f:
                data_content = json.load(f)
            
            timestamp = extract_timestamp_from_filename(latest_json_path)
            
            # La estructura esperada de los datos de acciones es {"listaResult": [acciones]}
            # o podría ser directamente una lista [acciones] si la API Cuenta_Premium lo devolviera así.
            if isinstance(data_content, dict) and "listaResult" in data_content and isinstance(data_content["listaResult"], list):
                return {"data": data_content["listaResult"], "timestamp": timestamp, "source_file": latest_json_path}
            elif isinstance(data_content, list): # Si el JSON raíz es la lista de acciones
                return {"data": data_content, "timestamp": timestamp, "source_file": latest_json_path}
            else:
                logger.error(f"El archivo JSON {latest_json_path} no tiene la estructura esperada ('listaResult' o lista raíz). Contenido: {str(data_content)[:200]}")
                return {"error": "Estructura de datos inesperada en archivo JSON.", "timestamp": timestamp, "source_file": latest_json_path}
        else:
            logger.error("No se pudo obtener el archivo de datos actualizado.")
            return {"error": "No se pudieron obtener datos", "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    
    except Exception as e:
        logger.exception(f"Error en get_latest_data: {e}")
        return {"error": str(e), "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

def filter_stocks(stock_codes):
    """
    Filtra las acciones según los códigos proporcionados (NEMO).
    """
    try:
        latest_data_result = get_latest_data()
        
        if "error" in latest_data_result:
            logger.error(f"Error al obtener datos para filtrar: {latest_data_result['error']}")
            return latest_data_result 
        
        # Los datos de acciones están bajo la clave "data" en el resultado de get_latest_data()
        stocks_list = latest_data_result.get("data")
        original_timestamp = latest_data_result.get("timestamp")
        source_file = latest_data_result.get("source_file", "N/A")

        if not isinstance(stocks_list, list):
            logger.error(f"Se esperaba una lista de acciones, pero se obtuvo: {type(stocks_list)}. Archivo: {source_file}")
            return {"error": "Datos de acciones no son una lista.", "timestamp": original_timestamp, "source_file": source_file}
            
        if not stock_codes: # Si no se proporcionan códigos, devolver todos los datos
            logger.info("No se proporcionaron códigos de acciones para filtrar, devolviendo todos los datos.")
            return {"data": stocks_list, "timestamp": original_timestamp, "count": len(stocks_list), "source_file": source_file}

        stock_codes_upper = [code.upper().strip() for code in stock_codes if isinstance(code, str) and code.strip()]
        
        filtered_stocks = []
        for stock in stocks_list:
            if isinstance(stock, dict) and "NEMO" in stock and isinstance(stock["NEMO"], str):
                if stock["NEMO"].upper() in stock_codes_upper:
                    filtered_stocks.append(stock)
            else:
                logger.warning(f"Elemento de acción con formato inesperado o sin 'NEMO': {str(stock)[:100]}")
        
        logger.info(f"Filtradas {len(filtered_stocks)} acciones de {len(stocks_list)} originales.")
        return {
            "data": filtered_stocks, 
            "timestamp": original_timestamp, 
            "count": len(filtered_stocks),
            "source_file": source_file
        }
    
    except Exception as e:
        logger.exception(f"Error en filter_stocks: {e}")
        return {"error": str(e), "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

def update_data_periodically(min_interval_seconds, max_interval_seconds):
    """
    Actualiza los datos periódicamente en un intervalo aleatorio.
    """
    global stop_update_thread
    
    logger.info(f"Hilo de actualización periódica iniciado. Intervalo: {min_interval_seconds}-{max_interval_seconds} segundos.")
    while not stop_update_thread:
        try:
            logger.info("Ejecutando actualización periódica de datos...")
            run_bolsa_bot() # Ejecuta el bot para obtener datos frescos
            
            interval = random.randint(min_interval_seconds, max_interval_seconds)
            logger.info(f"Próxima actualización periódica en {interval} segundos.")
            
            # Esperar el intervalo, verificando periódicamente si debemos detenernos
            for _ in range(interval):
                if stop_update_thread:
                    logger.info("Señal de detención recibida en el hilo de actualización.")
                    break
                time.sleep(1)
                
        except Exception as e:
            logger.exception(f"Error en la actualización periódica: {e}")
            logger.info("Esperando 60 segundos antes de reintentar la actualización periódica.")
            time.sleep(60)
    logger.info("Hilo de actualización periódica detenido.")


def start_periodic_updates(min_minutes=15, max_minutes=45): # Intervalos más largos por defecto
    """
    Inicia la actualización periódica de datos en un hilo separado.
    """
    global update_thread, stop_update_thread
    
    if update_thread and update_thread.is_alive():
        logger.info("El hilo de actualización periódica ya está en ejecución.")
        return False
    
    stop_update_thread = False
    min_interval_seconds = min_minutes * 60
    max_interval_seconds = max_minutes * 60
    
    update_thread = threading.Thread(
        target=update_data_periodically,
        args=(min_interval_seconds, max_interval_seconds),
        daemon=True # El hilo terminará cuando el programa principal termine
    )
    update_thread.start()
    
    logger.info(f"Actualización periódica iniciada. Intervalo entre ejecuciones: {min_minutes}-{max_minutes} minutos.")
    return True

def stop_periodic_updates():
    """
    Detiene la actualización periódica de datos.
    """
    global stop_update_thread, update_thread
    
    if not update_thread or not update_thread.is_alive():
        logger.info("El hilo de actualización periódica no está en ejecución.")
        return True

    logger.info("Enviando señal de detención al hilo de actualización periódica...")
    stop_update_thread = True
    update_thread.join(timeout=10) # Esperar hasta 10 segundos a que el hilo termine
    
    if update_thread.is_alive():
        logger.warning("El hilo de actualización periódica no terminó limpiamente después de 10 segundos.")
    else:
        logger.info("Hilo de actualización periódica detenido exitosamente.")
    update_thread = None
    return True

# Ejemplo de uso (puedes comentar o eliminar esto si usas el script como módulo)
if __name__ == "__main__":
    logger.info("--- Servicio de Datos de Bolsa de Santiago Iniciado ---")
    
    # Obtener datos una vez al iniciar
    initial_data = get_latest_data()
    if "error" not in initial_data:
        logger.info(f"Datos iniciales cargados desde: {initial_data.get('source_file', 'N/A')}")
        logger.info(f"Timestamp de datos iniciales: {initial_data['timestamp']}")
        logger.info(f"Número de acciones en datos iniciales: {len(initial_data.get('data', []))}")
    else:
        logger.error(f"Error al cargar datos iniciales: {initial_data['error']}")

    # Filtrar algunas acciones de ejemplo
    codigos_a_filtrar = ["SQM-B", "COPEC", "CMPC", "FALABELLA", "CHILE"] # Ejemplo
    logger.info(f"Filtrando por los siguientes códigos: {codigos_a_filtrar}")
    acciones_filtradas = filter_stocks(codigos_a_filtrar)
    
    if "error" not in acciones_filtradas:
        logger.info(f"Resultado del filtrado (Fuente: {acciones_filtradas.get('source_file', 'N/A')}, Timestamp: {acciones_filtradas['timestamp']}):")
        for accion in acciones_filtradas.get("data", []):
            print(f"  NEMO: {accion.get('NEMO')}, PRECIO_CIERRE: {accion.get('PRECIO_CIERRE')}, VARIACION: {accion.get('VARIACION')}")
    else:
        logger.error(f"Error al filtrar acciones: {acciones_filtradas['error']}")

    # Iniciar actualizaciones periódicas (ej. cada 15-45 minutos)
    # start_periodic_updates(min_minutes=15, max_minutes=45)
    
    # Mantener el script principal vivo si se desea que el hilo siga corriendo
    # o si esto fuera parte de una aplicación más grande (ej. Flask, FastAPI)
    # try:
    #     while True:
    #         time.sleep(60) # Dormir y verificar estado o esperar comandos
    #         logger.debug("Servicio principal activo...")
    # except KeyboardInterrupt:
    #     logger.info("Interrupción por teclado recibida. Deteniendo servicio...")
    # finally:
    #     stop_periodic_updates()
    #     logger.info("--- Servicio de Datos de Bolsa de Santiago Detenido ---")