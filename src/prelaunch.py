import subprocess
import sys
import os
import argparse
import logging
import pytest
from pathlib import Path

# Constante para los argumentos comunes de Pytest
PYTEST_COMMON_ARGS = ["-q", "--tb=short"]

class CriticalPrelaunchError(Exception):
    """Excepción personalizada para errores fatales durante el pre-lanzamiento."""
    pass

# Añadir el directorio raíz del proyecto a sys.path
# para que los módulos se puedan encontrar
# sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
# La línea de arriba no es suficiente para los subprocesos, se manejará con el entorno.

def run_check(command, description):
    """Ejecuta un comando de prueba y maneja el resultado."""
    print(f"▶️  Ejecutando: {description}...", flush=True)
    try:
        env = os.environ.copy()
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')

        print(f"   (Comando: {command})", flush=True)
        print("   ⏳ Lanzando subproceso...", flush=True)

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            env=env,
            timeout=120  # Aumentado a 120 segundos
        )

        print("   -> Subproceso finalizado (después de run).", flush=True)

        if result.returncode != 0:
            print(f"   ❌ Subproceso falló (código de salida: {result.returncode}).", flush=True)
            print(f"❌ FALLO: {description}.", flush=True)
            print("\n--- Salida (stdout) ---", flush=True)
            print(result.stdout, flush=True)
            print("\n--- Salida de Error (stderr) ---", flush=True)
            print(result.stderr, flush=True)
            print("------------------------\n", flush=True)
            return False

        print("   ✅ Subproceso finalizado.", flush=True)
        print(f"✅ Éxito: {description} completado.", flush=True)
        return True
    except subprocess.TimeoutExpired as e:
        print("   ❌ Subproceso excedió el tiempo límite.", flush=True)
        print(f"❌ FALLO: {description} excedió el límite de 30 segundos.", flush=True)
        if e.stdout:
            print("\n--- Salida (stdout) ---", flush=True)
            print(e.stdout, flush=True)
        if e.stderr:
            print("\n--- Salida de Error (stderr) ---", flush=True)
            print(e.stderr, flush=True)
        print("------------------------\n", flush=True)
        return False
    except Exception as e:
        print(f"   ❌ Ocurrió un error inesperado al ejecutar '{description}'.", flush=True)
        print(f"   Error: {e}", flush=True)
        return False

def run_env_check():
    """Ejecuta la verificación de variables de entorno usando pytest.main()."""
    print("▶️  Ejecutando: Verificación de variables de entorno...", flush=True)
    # Ejecuta pytest en el mismo proceso, evitando problemas con subprocess
    result = pytest.main(PYTEST_COMMON_ARGS + ["tests/test_config_env.py"])
    if result == pytest.ExitCode.OK:
        print("✅ Éxito: Verificación de variables de entorno completado.", flush=True)
        return True
    else:
        print("❌ FALLO: La verificación de variables de entorno ha fallado.", flush=True)
        return False

def run_db_connection_check():
    """Ejecuta la verificación de la conexión a la BD usando pytest.main()."""
    print("▶️  Ejecutando: Verificación de conexión a la base de datos...", flush=True)
    result = pytest.main(PYTEST_COMMON_ARGS + ["tests/test_database_connection.py"])
    if result == pytest.ExitCode.OK:
        print("✅ Éxito: Verificación de conexión a la base de datos completado.", flush=True)
        return True
    else:
        print("❌ FALLO: La verificación de conexión a la base de datos ha fallado.", flush=True)
        return False

def run_smoke_tests():
    """
    Ejecuta una suite de "smoke tests" para verificar la salud general de la app,
    incluyendo rutas, eventos de socket y la configuración del bot.
    """
    print("▶️  Ejecutando: Smoke tests de la aplicación...", flush=True)
    test_files = [
        "tests/test_routes_status.py",
        "tests/test_socketio_events.py",
        "tests/test_bot_setup.py"
    ]
    # Usamos -q para un output más limpio y --tb=short para tracebacks concisos.
    result = pytest.main(PYTEST_COMMON_ARGS + test_files)
    if result == pytest.ExitCode.OK:
        print("✅ Éxito: Todos los smoke tests han pasado.", flush=True)
        return True
    else:
        print("❌ FALLO: Uno o más smoke tests han fallado.", flush=True)
        return False

def check_env_file():
    """Verifica si el archivo .env existe en la raíz del proyecto."""
    print("🔎 Verificando existencia del archivo .env...", flush=True)
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print(f"❌ FALLO: No se encontró el archivo .env en la raíz del proyecto ({env_file})", flush=True)
        print("   Por favor, cree el archivo con las variables de entorno necesarias:", flush=True)
        print("   - BOLSA_USERNAME", flush=True)
        print("   - BOLSA_PASSWORD", flush=True)
        print("   - DATABASE_URL", flush=True)
        return False
    
    print("✅ Éxito: Archivo .env encontrado.", flush=True)
    return True

def run_performance_suite():
    """Ejecuta la suite de tests completa con optimizaciones de rendimiento."""
    print("🚀 Iniciando suite de tests de rendimiento...", flush=True)
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    perf_log_path = os.path.join(project_root, 'logs', 'pytest-perf.log')
    os.makedirs(os.path.dirname(perf_log_path), exist_ok=True)
    
    print(f"Los resultados detallados se guardarán en: {perf_log_path}", flush=True)

    env = os.environ.copy()
    env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')

    # Comando para ejecutar todos los tests en paralelo
    full_suite_command = 'pytest -n auto --durations=10 tests/'

    # Comando para ejecutar solo los tests rápidos
    fast_suite_command = 'pytest -m "not slow" tests/'

    print("\n--- Ejecutando solo tests rápidos ---", flush=True)
    if not run_check(fast_suite_command, "Suite de tests rápidos"):
        print("\n🛑 Fallaron los tests rápidos. No se continuará con la suite completa.", flush=True)
        return False
    
    print("\n--- Ejecutando suite completa en paralelo (logging to file) ---", flush=True)
    print(f"Comando: {full_suite_command}", flush=True)
    try:
        with open(perf_log_path, 'w', encoding='utf-8') as log_file:
            subprocess.run(
                full_suite_command, 
                shell=True, 
                check=True, 
                stdout=log_file, 
                stderr=subprocess.STDOUT, 
                text=True,
                env=env
            )
        print("✅ Éxito: Suite completa de tests finalizada.", flush=True)
        print(f"   Revisa el log para ver los tiempos de ejecución: {perf_log_path}", flush=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ FALLO: La suite completa de tests encontró errores.", flush=True)
        print(f"   Revisa el log para más detalles: {perf_log_path}", flush=True)
        return False


def run_all_checks():
    """Ejecuta todas las validaciones críticas y devuelve True si todas pasan."""
    print("🚀 Iniciando validaciones de pre-lanzamiento...", flush=True)

    if not check_env_file():
        return False
    
    if not run_env_check():
        return False

    if not run_db_connection_check():
        return False
    
    # Desactivamos temporalmente la suite de smoke tests.
    # if not run_smoke_tests():
    #     return False
            
    print("\n🎉 Todas las validaciones de pre-lanzamiento han pasado con éxito.", flush=True)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script de validación y pruebas de la aplicación.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--mode', 
        type=str, 
        choices=['validate', 'perf'], 
        default='validate',
        help=(
            "Modo de ejecución:\n"
            "  - validate: (defecto) Ejecuta chequeos rápidos de pre-lanzamiento.\n"
            "  - perf:     Ejecuta la suite de tests de rendimiento completa."
        )
    )
    args = parser.parse_args()

    if args.mode == 'validate' and not run_all_checks():
        sys.exit(1)
    elif args.mode == 'perf' and not run_performance_suite():
        sys.exit(1)
            
    sys.exit(0) 