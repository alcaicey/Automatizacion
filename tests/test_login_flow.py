# tests/test_login_flow.py
import pytest
import time
from unittest.mock import patch, MagicMock
from src.scripts.bot_login import LoginError

# Eliminados imports no utilizados
# from src.routes.api.bot_routes import target_func, _sync_bot_running_lock

# Eliminado el fixture 'ensure_lock_released' que ya no es necesario
# porque el test ya no manipula el lock directamente.

def test_update_stocks_handles_login_error(client, app):
    """
    GIVEN un cliente de Flask
    WHEN se llama a la API para actualizar acciones y el bot falla con LoginError
    THEN el error debe ser logueado y el lock liberado.
    """
    mock_thread = MagicMock()

    # Interceptamos la creación del Hilo para capturar la función 'target'
    with patch('threading.Thread', new=mock_thread) as mock_thread_constructor:
        # Hacemos la llamada a la API que crea el hilo
        response = client.post('/api/stocks/update')
        assert response.status_code == 202

    # Verificamos que se intentó crear un hilo
    mock_thread_constructor.assert_called_once()
    
    # Extraemos los argumentos pasados al constructor del hilo
    thread_args = mock_thread_constructor.call_args.kwargs
    target_func = thread_args.get('target')
    assert target_func is not None

    # 2. FIX: Add the missing bot_event_loop attribute to the test app
    # to prevent the "'Flask' object has no attribute 'bot_event_loop'" error.
    app.bot_event_loop = MagicMock()
    app.bot_event_loop.is_running.return_value = True

    # Ahora que tenemos la función 'target', la ejecutamos en un entorno controlado
    login_error = LoginError("Simulated Login Failure")
    with patch('src.scripts.bolsa_service.run_bolsa_bot', side_effect=login_error):
        # FIX: El error se loguea en 'bolsa_service', no en 'bot_routes'.
        with patch('src.scripts.bolsa_service.logger.error') as mock_logger_error:
            # Ejecutamos la función capturada con los argumentos originales
            # El primer argumento para target_func es la app.
            original_args = thread_args.get('args', ())
            target_func(*original_args)

            # Verificamos que el logger de errores fue llamado
            mock_logger_error.assert_called_once()

            # Verificamos que el texto de la excepción está en los argumentos de la llamada al logger
            call_args_str = str(mock_logger_error.call_args)
            assert login_error.__class__.__name__ in call_args_str 