// tests/js/eventHandlers.test.js

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { JSDOM } from 'jsdom';
import EventHandlers from '../../src/static/js/utils/eventHandlers.js'; // Corregido
import { createMockApp } from './utils/mockApp.js';
import * as api from '../../src/static/js/utils/api.js';

// Mockear el módulo de API
vi.mock('../../src/static/js/utils/api', () => ({
  post: vi.fn(),
}));

describe('Event Handlers', () => {
  let app;
  let dom;
  let eventHandlers; // Añadido

  // Configurar un DOM virtual antes de cada prueba
  beforeEach(() => {
    dom = new JSDOM(`
        <!DOCTYPE html>
        <html>
            <body>
                <button id="update-now-btn"></button>
            </body>
        </html>
    `, { url: "http://localhost" });

    global.window = dom.window;
    global.document = dom.window.document;
    
    // Usar una copia fresca de mockApp para evitar contaminación entre tests
    app = createMockApp();
    eventHandlers = new EventHandlers(app); // Corregido
  });

  afterEach(() => {
      vi.restoreAllMocks();
      global.window = undefined;
      global.document = undefined;
  });

  describe('handleUpdateClick', () => {
    it('debe llamar a la API y actualizar el estado cuando el bot no está ocupado', async () => {
        // Configurar el mock para simular que el bot está disponible
        app.botStatusManager.getState.mockReturnValue({ isUpdating: false });

        // Mockear fetchData que ahora es parte de app
        app.fetchData = vi.fn().mockResolvedValue({});
        
        // Simular clic
        await eventHandlers.handleUpdateClick(); // Corregido

        // Verificar que se llamó a getState
        expect(app.botStatusManager.getState).toHaveBeenCalledOnce();
        
        // Verificar que se intentó iniciar la actualización
        expect(app.botStatusManager.setUpdating).toHaveBeenCalledWith(true, 'Iniciando actualización...');
        
        // Verificar que se llamó a la API REST
        expect(app.fetchData).toHaveBeenCalledWith('/api/stocks/update', { method: 'POST' });
        
        // Verificar que se mostró feedback al usuario
        expect(app.uiManager.showFeedback).toHaveBeenCalledWith('info', 'Iniciando actualización manual...');
    });

    it('NO debe hacer nada si el bot ya se está actualizando', async () => {
        // Configurar el mock para simular que el bot está OCUPADO
        app.botStatusManager.getState.mockReturnValue({ isUpdating: true });
        app.fetchData = vi.fn();

        // Simular clic
        await eventHandlers.handleUpdateClick(); // Corregido

        // Verificar que se llamó a getState
        expect(app.botStatusManager.getState).toHaveBeenCalledOnce();

        // Verificar que NO se intentó actualizar de nuevo
        expect(app.botStatusManager.setUpdating).not.toHaveBeenCalled();
        expect(app.fetchData).not.toHaveBeenCalled();

        // Verificar que se notificó al usuario
        expect(app.uiManager.showFeedback).toHaveBeenCalledWith('info', 'El proceso de actualización ya está en marcha.');
    });

    it('debe manejar errores si la llamada a la API falla', async () => {
        // Configurar mocks
        app.botStatusManager.getState.mockReturnValue({ isUpdating: false });
        const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        app.fetchData = vi.fn().mockRejectedValue(new Error('API Error'));

        // Simular clic y esperar a que las promesas se resuelvan
        await eventHandlers.handleUpdateClick(); // Corregido

        // Verificar el flujo de inicio
        expect(app.botStatusManager.setUpdating).toHaveBeenCalledWith(false, 'Error al iniciar.');
        consoleErrorSpy.mockRestore();
    });
  });
}); 