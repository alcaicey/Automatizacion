import { describe, it, expect, beforeEach } from 'vitest';
import { JSDOM } from 'jsdom';
import fs from 'fs';
import path from 'path';

describe('DOM inicial del dashboard', () => {
  let dom;
  let document;

  beforeEach(() => {
    // Cargar el HTML base del dashboard para simular un entorno de navegador real
    const html = fs.readFileSync(path.resolve(__dirname, '../../src/templates/dashboard.html'), 'utf8');
    dom = new JSDOM(html);
    document = dom.window.document;
  });

  it('debe tener el overlay de carga', () => {
    const overlay = document.querySelector('#loading-overlay');
    expect(overlay).not.toBeNull();
  });

  it('debe tener el botón "Actualizar Ahora"', () => {
    const btn = document.querySelector('#update-now-btn');
    expect(btn).not.toBeNull();
  });
  
  it('debe tener el contenedor para el status del bot', () => {
    const statusContainer = document.querySelector('#bot-status-alert');
    expect(statusContainer).not.toBeNull();
  });

  it('debe tener el contenedor para el grid del dashboard', () => {
    const grid = document.querySelector('.grid-stack');
    expect(grid).not.toBeNull();
  });
}); 