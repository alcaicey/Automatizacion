// tests/js/portfolioManager.test.js

/**
 * @jest-environment jsdom
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import PortfolioManager from '../../src/static/js/managers/portfolioManager.js';
import { createMockApp } from './utils/mockApp.js';

describe('PortfolioManager', () => {
  let mockApp;
  let manager;
  let dom;

    beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <body>
            <div id="portfolio-widget">
                <table id="portfolioTable"></table>
          <div id="totalPaid"></div>
          <div id="totalCurrentValue"></div>
          <div id="totalGainLoss"></div>
          <form id="portfolioColumnConfigForm"></form>
            </div>
      </body>
    `);
    
    global.document = dom.window.document;
    global.window = dom.window;
    
    // Mocks de librerías globales
    global.bootstrap = { Modal: vi.fn() };
    global.$ = require('jquery');
    $.fn.DataTable = vi.fn();

    mockApp = createMockApp();
    manager = new PortfolioManager(mockApp);
  });

  test('should instantiate without crashing', () => {
    expect(manager).toBeDefined();
    expect(manager.app).toBe(mockApp);
  });

  // --- INICIO DE LA CORRECCIÓN ---
  // El test se actualiza para reflejar la implementación real, que llama a
  // app.fetchData en lugar de a métodos locales inexistentes.
  test('initializeWidget debe llamar a fetchData para obtener columnas y holdings', async () => {
    // Configurar el mock de fetchData para que devuelva datos simulados
    const mockData = {
        columns: { all_columns: ['symbol'], visible_columns: ['symbol'] },
        holdings: { portfolio: [], summary: {} }
    };
    mockApp.fetchData
        .mockResolvedValueOnce(mockData.columns)  // Primera llamada devuelve columnas
        .mockResolvedValueOnce(mockData.holdings); // Segunda llamada devuelve holdings

    // Espiar el método fetchData en la instancia mock de la app
    const fetchDataSpy = vi.spyOn(mockApp, 'fetchData');

    await manager.initializeWidget();

    // Verificar que fetchData fue llamado dos veces
    expect(fetchDataSpy).toHaveBeenCalledTimes(2);

    // Verificar que fue llamado con los endpoints correctos
    expect(fetchDataSpy).toHaveBeenCalledWith('/api/portfolio/columns');
    expect(fetchDataSpy).toHaveBeenCalledWith('/api/portfolio/holdings');

    // Limpiar el espía
    fetchDataSpy.mockRestore();
  });
  // --- FIN DE LA CORRECCIÓN ---

    test('initializeWidget debe fallar con advertencia si getContainer no está definido', () => {
        const fakeApp = { uiManager: {} }; // uiManager sin getContainer
        const manager = new PortfolioManager(fakeApp);
        const consoleSpy = vi.spyOn(console, 'warn');
        
        manager.initializeWidget();
        
        expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('getContainer no disponible'));
        consoleSpy.mockRestore();
    });
}); 