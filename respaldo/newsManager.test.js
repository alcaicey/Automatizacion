import { describe, test, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import NewsManager from '../../src/static/js/managers/newsManager.js';
import { createMockApp } from './utils/mockApp.js';

describe('NewsManager', () => {
  let mockApp;
  let manager;
  let dom;

  beforeEach(() => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <body>
        <div id="news-widget">
          <ul id="news-list"></ul>
          <div id="news-loading"></div>
          <button id="newsRefreshBtn"></button>
        </div>
      </body>
    `);
    
    global.document = dom.window.document;
    global.window = dom.window;

    mockApp = createMockApp();
    manager = new NewsManager(mockApp);
  });

  test('should instantiate without crashing', () => {
    expect(manager).toBeDefined();
  });

  test('initializeWidget should call loadNews', async () => {
    const widgetElement = document.getElementById('news-widget');
    const loadNewsSpy = vi.spyOn(manager, 'loadNews').mockImplementation(() => Promise.resolve());
    
    await manager.initializeWidget(widgetElement);
    
    expect(loadNewsSpy).toHaveBeenCalled();
    
    loadNewsSpy.mockRestore();
  });
}); 