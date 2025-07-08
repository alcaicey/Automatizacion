import { describe, test, expect, beforeEach, vi, afterEach } from 'vitest';
import { JSDOM } from 'jsdom';
import DividendManager from '../../src/static/js/managers/dividendManager.js';
import { createMockApp } from './utils/mockApp.js';

// Mock global de jQuery y DataTables
const $ = vi.fn(() => ({
    on: vi.fn(),
    DataTable: vi.fn(() => ({
        destroy: vi.fn(),
        clear: vi.fn(() => ({
            draw: vi.fn(),
        })),
        rows: vi.fn(() => ({
            every: vi.fn(),
        })),
        cell: vi.fn(),
        data: vi.fn(),
    })),
    empty: vi.fn(),
    html: vi.fn(),
    closest: vi.fn(),
    find: vi.fn(() => ({
        appendTo: vi.fn(),
    })),
    appendTo: vi.fn(),
}));
$.fn = {
    DataTable: vi.fn(() => ({
        destroy: vi.fn(),
    }))
};
global.$ = $;
global.jQuery = $; // A veces DataTables busca jQuery con mayúscula


describe('DividendManager', () => {
  let mockApp;
  let manager;
  let dom;

  beforeEach(() => {
    // Mockear fetch globalmente para todas las pruebas de este archivo
    vi.spyOn(global, 'fetch').mockImplementation((url) => {
        if (url.includes('/api/dividends/columns')) {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve({
                    // Devolver claves que SÍ existen en el columnConfig del manager
                    all_columns: ['symbol', 'name', 'payment_date', 'dividend_rate'],
                    visible_columns: ['symbol', 'payment_date']
                }),
            });
        }
        if (url.includes('/api/dividends')) {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve([]), // Devolver un array vacío de dividendos
            });
        }
        return Promise.reject(new Error(`URL no mockeada: ${url}`));
    });

    dom = new JSDOM(`
      <!DOCTYPE html>
      <body>
        <div id="dividend-widget">
            <div id="dividend-alert-container"></div>
            <div id="loadingOverlayDividends"></div>
            
            <input id="dividendTextFilter">
            <input id="dividendDateFrom">
            <input id="dividendDateTo">
            <select id="dividendColumnFilter"></select>
            <button id="applyDividendFiltersBtn"></button>
            <button id="clearDividendFiltersBtn"></button>

            <table id="dividendTable"></table>
            <button id="updateDividendsBtn"></button>

            <!-- Modal -->
            <div id="dividendColumnConfigModal"></div>
            <div id="dividendColumnConfigForm"></div>
            <button id="saveDividendColumnPrefs"></button>
        </div>
      </body>
    `);
    
    global.document = dom.window.document;
    global.window = dom.window;

    mockApp = createMockApp();
    manager = new DividendManager(mockApp);
    manager.socket = { on: vi.fn(), emit: vi.fn() }; // Mock socket
  });

  afterEach(() => {
      vi.restoreAllMocks(); // Limpiar mocks después de cada test
  });

  test('should instantiate without crashing', () => {
    expect(manager).toBeDefined();
  });

  test('initializeWidget should find all DOM elements and attach listeners', () => {
    const attachListenersSpy = vi.spyOn(manager, 'attachEventListeners');
    const loadInitialDataSpy = vi.spyOn(manager, 'loadInitialData').mockResolvedValue(undefined);

    manager.initializeWidget();
    
    // Verificar que los elementos principales del DOM se hayan asignado
    expect(manager.dom.table).not.toBeNull();
    expect(manager.dom.updateBtn).not.toBeNull();
    expect(manager.dom.savePrefsBtn).not.toBeNull();
    expect(manager.dom.applyFiltersBtn).not.toBeNull();

    // Verificar que los métodos de inicialización fueron llamados
    expect(attachListenersSpy).toHaveBeenCalledTimes(1);
    expect(loadInitialDataSpy).toHaveBeenCalledTimes(1);
    
    attachListenersSpy.mockRestore();
    loadInitialDataSpy.mockRestore();
  });
  
  test('attachEventListeners should bind events correctly', () => {
      manager.initializeWidget(); // para popular this.dom

      const updateBtnSpy = vi.spyOn(manager, 'handleUpdateClick');
      const savePrefsSpy = vi.spyOn(manager, 'handleSavePrefs');
      const loadDividendsSpy = vi.spyOn(manager, 'loadDividends');
      
      manager.dom.updateBtn.click();
      expect(updateBtnSpy).toHaveBeenCalledTimes(1);
      
      manager.dom.savePrefsBtn.click();
      expect(savePrefsSpy).toHaveBeenCalledTimes(1);

      manager.dom.applyFiltersBtn.click();
      expect(loadDividendsSpy).toHaveBeenCalledTimes(1); // loadDividends se llama dentro del listener

      // La llamada inicial a loadDividends es asíncrona, necesitamos esperarla
      // pero como está mockeada en el test anterior, aquí la llamamos de nuevo para verificar
      // el comportamiento del listener.

      updateBtnSpy.mockRestore();
      savePrefsSpy.mockRestore();
      loadDividendsSpy.mockRestore();
  });
}); 