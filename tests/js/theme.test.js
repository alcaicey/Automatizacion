import { describe, it, expect, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';
import { JSDOM } from 'jsdom';
import { ThemeManager } from '../../src/static/theme.modular.js';

describe('ThemeManager', () => {
    let dom;
    let themeManager;

    beforeAll(() => {
        dom = new JSDOM(`
            <!DOCTYPE html>
            <html data-bs-theme="light">
                <body>
                </body>
            </html>
        `);
        global.document = dom.window.document;
    });

    afterAll(() => {
        dom.window.close();
    });

    beforeEach(() => {
        // Resetear el atributo del tema antes de cada test
        document.documentElement.setAttribute('data-bs-theme', 'light');
        themeManager = new ThemeManager();
    });

    it('should set the dark theme on the document element', () => {
        themeManager.applyTheme('dark');
        expect(document.documentElement.getAttribute('data-bs-theme')).toBe('dark');
    });

    it('should set the light theme on the document element', () => {
        // Primero lo cambiamos a dark
        document.documentElement.setAttribute('data-bs-theme', 'dark');
        // Luego probamos que lo cambia a light
        themeManager.applyTheme('light');
        expect(document.documentElement.getAttribute('data-bs-theme')).toBe('light');
    });
}); 