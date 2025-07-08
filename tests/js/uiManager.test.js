import { describe, test, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import UIManager from '../../src/static/js/managers/uiManager.js';
import { createMockApp } from './utils/mockApp.js';

describe('UIManager', () => {
  let mockApp;
  let manager;
  let dom;

  beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <body>
        <div id="loading-overlay"></div>
        <div id="loadingMessage"></div>
        <table id="testTable"></table>
      </body>
    `);
    
    global.document = dom.window.document;
    global.window = dom.window;

    global.$ = require('jquery');
    
    const mockDataTable = vi.fn(() => ({
      clear: vi.fn().mockReturnThis(),
      rows: vi.fn().mockReturnThis(),
      add: vi.fn().mockReturnThis(),
      columns: vi.fn().mockReturnThis(),
      adjust: vi.fn().mockReturnThis(),
      draw: vi.fn().mockReturnThis(),
    }));

    // Simular tanto .DataTable como .dataTable para cubrir el uso en el código
    $.fn.DataTable = mockDataTable;
    $.fn.dataTable = {
      isDataTable: vi.fn(() => false)
    };

    mockApp = createMockApp();
    manager = new UIManager(mockApp);
    manager.app = mockApp; // Asignar la app al manager
  });

  test('should instantiate without crashing', () => {
    expect(manager).toBeDefined();
  });

  test('initializeWidget should log an initialization message', () => {
    const consoleSpy = vi.spyOn(console, 'log');
    manager.initializeWidget();
    expect(consoleSpy).toHaveBeenCalledWith('[UIManager] Inicializado y listo.');
    consoleSpy.mockRestore();
  });

  test('toggleLoading should show and hide the overlay', () => {
    const overlay = document.getElementById('loading-overlay');
    manager.toggleLoading(true, 'Testing...');
    expect(overlay.style.display).toBe('flex');
    
    manager.toggleLoading(false);
    expect(overlay.style.display).toBe('none');
  });

  test('renderTable should initialize DataTable if not already present', () => {
    manager.renderTable('testTable', [], []);
    expect($.fn.DataTable).toHaveBeenCalled();
  });
}); 