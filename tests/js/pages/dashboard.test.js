import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { JSDOM } from 'jsdom';
import $ from 'jquery';
import Dashboard from '../../../src/static/js/pages/dashboard.js';
import { showToast } from '../../../src/static/js/utils/toast.js';

// Mockear el módulo de toast
vi.mock('../../../src/static/js/utils/toast', () => ({
  showToast: vi.fn(),
}));

describe('Dashboard WebSocket Event Handling', () => {
  let dashboard;
  let mockApp; // Declarada aquí
  let mockSocket;
  let dom, window, document; // Declaradas aquí

  beforeEach(() => {
    dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', { url: 'http://localhost' });
    window = dom.window;
    document = window.document;
    global.window = window;
    global.document = document;
    global.$ = $;
    global.io = vi.fn();

    // Mock de la instancia de socket.io-client
    mockSocket = {
      on: vi.fn(),
      emit: vi.fn(),
      connect: vi.fn(),
      disconnect: vi.fn(),
    };
    global.io.mockReturnValue(mockSocket);

    // Mock para simular la instancia global de la aplicación
    mockApp = {
      socket: mockSocket,
      uiManager: {
        updateLastUpdateTimestamp: vi.fn(),
      },
      portfolioManager: {
        render: vi.fn(),
      },
      state: {}, // Añadido para evitar el TypeError
    };

    dashboard = new Dashboard(mockApp);
    dashboard.setupSocketListeners(); // Llamar explícitamente para registrar listeners
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('WebSocket Listeners', () => {
    it("debe registrar los manejadores de socket correctos", () => {
      expect(mockSocket.on).toHaveBeenCalledWith('connect', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('disconnect', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('connect_error', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('last_update', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('stock_prices_updated', expect.any(Function));
    });

    it("debe manejar el evento 'last_update'", () => {
      const data = { timestamp: '2023-10-27T10:00:00Z', stocks: [{ symbol: 'TEST' }] };
      const lastUpdateCallback = mockSocket.on.mock.calls.find(call => call[0] === 'last_update')[1];
      
      lastUpdateCallback(data);
      
      expect(mockApp.uiManager.updateLastUpdateTimestamp).toHaveBeenCalledWith(data.timestamp);
      expect(mockApp.portfolioManager.render).toHaveBeenCalledWith(data.stocks);
    });
  });
}); 