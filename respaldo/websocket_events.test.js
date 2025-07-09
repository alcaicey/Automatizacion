// tests/js/websocket_events.test.js

import { vi, describe, it, expect, beforeEach } from 'vitest';
import BotStatusManager from '../../src/static/js/managers/botStatusManager.js';
import { createMockApp } from './utils/mockApp.js';

describe('Manejo de eventos de WebSocket', () => {
  let app;
  let botStatusManager;

  beforeEach(() => {
    app = createMockApp();
    
    // Crear el DOM necesario para el widget
    document.body.innerHTML = `
      <div id="bot-status-widget">
        <div id="bot-status-alert" class="alert">
          <span class="spinner-border"></span>
          <span></span>
        </div>
        <button id="update-now-btn"></button>
        <span id="last-update-time"></span>
      </div>
    `;

    // Espiar el método updateStatus antes de inicializar
    const spy = vi.spyOn(BotStatusManager.prototype, 'updateStatus');

    botStatusManager = new BotStatusManager(app);
    const widgetElement = document.getElementById('bot-status-widget');
    botStatusManager.initializeWidget(widgetElement);
    
    // Restaurar el espía si es necesario para no interferir con otras llamadas, o mantenerlo
    // para verificar todas las llamadas. Para este caso, lo mantenemos.
    // spy.mockRestore(); // No restaurar para poder verificar las llamadas.
  });

  it('debe manejar el evento "bot_status" para una actualización completada', () => {
    // Espiar el método handleBotStatus para asegurar que se llama
    const handleBotStatusSpy = vi.spyOn(botStatusManager, 'handleBotStatus');
    const updateStatusSpy = vi.spyOn(botStatusManager, 'updateStatus');

    // Simular la recepción del evento de WebSocket
    const data = { is_running: false, message: 'Actualización finalizada.', last_update: new Date().toISOString() };
    app.socket.emit('bot_status', data);

    // Verificar que el manejador fue llamado con los datos correctos
    expect(handleBotStatusSpy).toHaveBeenCalledWith(data);

    // Verificar que el estado interno del manager se actualizó
    expect(botStatusManager.getState().isUpdating).toBe(false);
    expect(botStatusManager.getState().message).toBe('Actualización finalizada.');
    
    // Verificar que se llamó a updateStatus con los parámetros de "éxito"
    expect(updateStatusSpy).toHaveBeenCalledWith('Actualización finalizada.', 'success', false);
    
    // Verificar que el botón de actualización está habilitado
    expect(botStatusManager.updateNowBtn.disabled).toBe(false);
  });

  it('debe manejar el evento "bot_error" y mostrar un mensaje de error', () => {
    const updateStatusSpy = vi.spyOn(botStatusManager, 'updateStatus');

    // Simular la recepción del evento de error
    const errorData = { message: 'Fallo crítico en el bot.' };
    app.socket.emit('bot_error', errorData);

    // Verificar que updateStatus fue llamado con los parámetros de "error"
    expect(updateStatusSpy).toHaveBeenCalledWith('Fallo crítico en el bot.', 'danger');
  });

  it('debe manejar el evento "bot_status" para una actualización en curso', () => {
    const handleBotStatusSpy = vi.spyOn(botStatusManager, 'handleBotStatus');
    const updateStatusSpy = vi.spyOn(botStatusManager, 'updateStatus');

    const data = { is_running: true, message: 'Extrayendo datos...', last_update: null };
    app.socket.emit('bot_status', data);

    expect(handleBotStatusSpy).toHaveBeenCalledWith(data);
    expect(botStatusManager.getState().isUpdating).toBe(true);
    expect(updateStatusSpy).toHaveBeenCalledWith('Extrayendo datos...', 'info', true);
    expect(botStatusManager.updateNowBtn.disabled).toBe(true);
  });
}); 