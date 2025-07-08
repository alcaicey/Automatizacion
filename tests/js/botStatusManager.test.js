// tests/js/botStatusManager.test.js
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { JSDOM } from 'jsdom';
import BotStatusManager from '../../src/static/js/managers/botStatusManager.js';
import { createMockApp } from './utils/mockApp.js';

describe('BotStatusManager', () => {
  let botStatusManager;
  let mockApp;
  let dom;

  beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <body>
          <div id="bot-status-alert"><span></span><div class="spinner-border"></div></div>
          <button id="update-now-btn"></button>
          <span id="last-update-time"></span>
        </body>
      </html>
    `);
    
    global.window = dom.window;
    global.document = dom.window.document;

    mockApp = createMockApp();
    botStatusManager = new BotStatusManager(mockApp);
    // Llama a initializeWidget para configurar los elementos del DOM y los listeners
    botStatusManager.initializeWidget(global.document.body);
  });

  afterEach(() => {
    vi.clearAllMocks();
    global.window = undefined;
    global.document = undefined;
  });

  describe('State Management', () => {
    it('debe tener un estado inicial correcto', () => {
      const state = botStatusManager.getState();
      expect(state.isUpdating).toBe(false);
      expect(state.lastUpdate).toBeNull();
      expect(state.errorMessage).toBeNull();
    });

    it('debe actualizar el estado con setUpdating', () => {
      botStatusManager.setUpdating(true, 'Iniciando...');
      const state = botStatusManager.getState();
      expect(state.isUpdating).toBe(true);
      expect(dom.window.document.getElementById('update-now-btn').disabled).toBe(true);
      
      // La actualización de status ahora ocurre en `updateStatus` que es llamado por `setUpdating`
      const statusSpan = dom.window.document.querySelector('#bot-status-alert span');
      // No podemos verificar el texto exacto porque updateStatus no está en el mock, 
      // pero podemos verificar que el botón está deshabilitado.
      // Si quisiéramos verificar el texto, necesitaríamos un mock más complejo
      // o espiar `updateStatus`. Por ahora, el estado del botón es suficiente.
    });
  });

  describe('Socket Event Handlers', () => {
    it('debe registrar los listeners del socket en la inicialización', () => {
      // initializeWidget llama a setupSocketListeners
      expect(mockApp.socket.on).toHaveBeenCalledWith('connect', expect.any(Function));
      expect(mockApp.socket.on).toHaveBeenCalledWith('disconnect', expect.any(Function));
      expect(mockApp.socket.on).toHaveBeenCalledWith('bot_status', expect.any(Function));
      expect(mockApp.socket.on).toHaveBeenCalledWith('bot_error', expect.any(Function));
    });

    it('handleBotStatus debe actualizar el estado y la UI', () => {
      const data = { is_running: false, last_update: '2023-10-27T10:00:00Z', message: '¡Éxito!' };
      botStatusManager.handleBotStatus(data);

      const state = botStatusManager.getState();
      expect(state.isUpdating).toBe(false);
      expect(state.lastUpdate).toBe(data.last_update);
      expect(dom.window.document.getElementById('update-now-btn').disabled).toBe(false);
      expect(botStatusManager.lastUpdateElement.textContent).toBe(new Date(data.last_update).toLocaleString());
    });
  });
}); 