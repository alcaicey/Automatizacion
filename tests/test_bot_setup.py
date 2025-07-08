import pytest
import asyncio
import threading
from src.app import create_app

@pytest.fixture(scope="module")
def full_app():
    """
    Crea una instancia completa de la aplicación, incluyendo la inicialización
    del bucle de eventos del bot, que ocurre en la función `start()`.
    
    Usamos 'module' para que la app se cree una sola vez para todos los tests
    de este archivo.
    """
    # En lugar de llamar a start(), replicamos las partes relevantes
    # para no iniciar el servidor web, solo la lógica de la app.
    app = create_app()

    # Iniciar el bucle de eventos del bot en un hilo separado
    bot_event_loop = asyncio.new_event_loop()
    
    def run_loop():
        asyncio.set_event_loop(bot_event_loop)
        bot_event_loop.run_forever()

    bot_thread = threading.Thread(target=run_loop, daemon=True)
    bot_thread.start()
    
    app.bot_event_loop = bot_event_loop
    app.bot_thread = bot_thread

    yield app

    # Limpieza: detener el bucle de eventos
    if bot_event_loop and bot_event_loop.is_running():
        bot_event_loop.call_soon_threadsafe(bot_event_loop.stop)
    if bot_thread and bot_thread.is_alive():
        bot_thread.join(timeout=2)


def test_bot_event_loop_attached_to_app(full_app):
    """
    Verifica que el bucle de eventos del bot (bot_event_loop)
    se haya creado y adjuntado correctamente a la instancia de la app.
    """
    assert hasattr(full_app, 'bot_event_loop'), "La app no tiene el atributo 'bot_event_loop'"
    assert isinstance(full_app.bot_event_loop, asyncio.AbstractEventLoop), "'bot_event_loop' no es un event loop de asyncio"

def test_bot_event_loop_is_running_in_thread(full_app):
    """
    Verifica que el bucle de eventos del bot se esté ejecutando
    y que lo haga en un hilo separado.
    """
    assert hasattr(full_app, 'bot_thread'), "La app no tiene el atributo 'bot_thread'"
    assert full_app.bot_thread.is_alive(), "El hilo del bot no se está ejecutando"
    assert full_app.bot_event_loop.is_running(), "El event loop del bot no se está ejecutando" 