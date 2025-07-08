import { describe, test, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import AlertManager from '../../src/static/js/managers/alertManager.js';
import { createMockApp } from './utils/mockApp.js';

describe('AlertManager', () => {
  let mockApp;
  let manager;
  let dom;

  beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <body>
        <div id="alert-widget">
          <form id="alertForm"></form>
          <ul id="alert-list"></ul>
          <div id="alert-loading"></div>
        </div>
      </body>
    `);
    
    global.document = dom.window.document;
    global.window = dom.window;

    mockApp = createMockApp();
    manager = new AlertManager(mockApp);
  });

  test('should instantiate without crashing', () => {
    expect(manager).toBeDefined();
  });

  test('initializeWidget should call loadAlerts', async () => {
    const widgetElement = document.getElementById('alert-widget');
    const loadAlertsSpy = vi.spyOn(manager, 'loadAlerts').mockImplementation(() => Promise.resolve());
    
    await manager.initializeWidget(widgetElement);
    
    expect(loadAlertsSpy).toHaveBeenCalled();
    
    loadAlertsSpy.mockRestore();
  });

  test('initializeWidget no debe lanzar error si el container es undefined', () => {
    expect(() => {
      manager.initializeWidget(undefined);
    }).not.toThrow();
  });
}); 