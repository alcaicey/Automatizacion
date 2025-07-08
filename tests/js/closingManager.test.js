import { describe, test, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import ClosingManager from '../../src/static/js/managers/closingManager.js';
import { createMockApp } from './utils/mockApp.js';

describe('ClosingManager', () => {
  let mockApp;
  let manager;
  let dom;

  beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <body>
        <div id="closing-widget">
          <table id="closingTable"></table>
        </div>
      </body>
    `);
    
    global.document = dom.window.document;
    global.window = dom.window;

    mockApp = createMockApp();
    manager = new ClosingManager(mockApp);
  });

  test('should instantiate without crashing', () => {
    expect(manager).toBeDefined();
  });

  test('initializeWidget should call loadData', async () => {
    const widgetElement = document.getElementById('closing-widget');
    const loadDataSpy = vi.spyOn(manager, 'loadData').mockImplementation(() => Promise.resolve());
    
    await manager.initializeWidget(widgetElement);
    
    expect(loadDataSpy).toHaveBeenCalled();
    
    loadDataSpy.mockRestore();
  });
}); 