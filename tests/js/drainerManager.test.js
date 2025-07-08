import { describe, test, expect, beforeEach, vi, afterEach } from 'vitest';
import { JSDOM } from 'jsdom';
import DrainerManager from '../../src/static/js/managers/drainerManager.js';
import { createMockApp } from './utils/mockApp.js';

// Mock robusto para jQuery y DataTables
const mockDataTableInstance = {
  destroy: vi.fn(),
  clear: vi.fn().mockReturnThis(),
  rows: vi.fn().mockReturnThis(), // Simplificado para encadenamiento
  add: vi.fn().mockReturnThis(),
  draw: vi.fn().mockReturnThis(),
};

// 1. Crear UNA ÚNICA función mock para el plugin DataTable
const dataTableMock = vi.fn(() => mockDataTableInstance);

// 2. Simular el método estático que usa el manager
dataTableMock.isDataTable = vi.fn(() => false);

// 3. El mock principal de $ devuelve un objeto que usa el mock de DataTable
const $ = vi.fn(() => ({
  DataTable: dataTableMock,
}));

// 4. Asignar el mismo mock a $.fn para consistencia y para el espía del test
$.fn = {
  DataTable: dataTableMock,
};

global.$ = $;
global.jQuery = $;

describe('DrainerManager', () => {
  let mockApp;
  let manager;
  let dom;

  beforeEach(() => {
    // Mockear fetch para la llamada a /api/drainers/events
    vi.spyOn(global, 'fetch').mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([]), // Devolver un array vacío de eventos
    });
    
    dom = new JSDOM(`
      <!DOCTYPE html>
      <body>
        <div id="drainer-widget">
          <button id="runAnalysisBtn"></button>
          <table id="drainersTable"></table>
          <div id="drainerAlert"></div>
        </div>
      </body>
    `);
    
    global.document = dom.window.document;
    global.window = dom.window;
    
    vi.clearAllMocks(); // Limpiar mocks antes de cada test

    mockApp = createMockApp();
    manager = new DrainerManager(mockApp);
  });

  afterEach(() => {
    vi.restoreAllMocks(); // Restaurar mocks después de cada prueba
  });

  test('should instantiate without crashing', () => {
    expect(manager).toBeDefined();
  });

  test('initializeWidget should setup DataTable, attach listeners, and fetch events', () => {
    const widgetElement = document.getElementById('drainer-widget');
    
    // Espiar fetchEvents ya que realiza una llamada de red que no es el foco de este test.
    const fetchEventsSpy = vi.spyOn(manager, 'fetchEvents').mockResolvedValue(undefined);

    // Llamar al método a probar
    manager.initializeWidget(widgetElement);

    // Verificar el comportamiento esperado
    expect(manager.isInitialized).toBe(true);
    // La aserción clave: verificar que el plugin DataTable fue llamado
    expect(dataTableMock).toHaveBeenCalled();
    // Verificar que los listeners del widget también fueron adjuntados
    expect(widgetElement.querySelector('#runAnalysisBtn').onclick).toBeDefined();
    // Verificar que los datos iniciales fueron solicitados
    expect(fetchEventsSpy).toHaveBeenCalledTimes(1);

    fetchEventsSpy.mockRestore();
  });

  test('runAnalysisBtn click should call runAnalysis method', () => {
      const widgetElement = document.getElementById('drainer-widget');
      manager.initializeWidget(widgetElement); // Inicializar para que el botón exista

      const runAnalysisSpy = vi.spyOn(manager, 'runAnalysis').mockResolvedValue(undefined);
      
      manager.dom.runBtn.click();
      
      expect(runAnalysisSpy).toHaveBeenCalledTimes(1);
      
      runAnalysisSpy.mockRestore();
  });
}); 