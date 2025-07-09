import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

const filesToCheck = [
  'src/static/js/app.js',
  'src/static/js/managers/alertManager.js',
  'src/static/js/managers/botStatusManager.js',
  'src/static/js/managers/closingManager.js',
  'src/static/js/managers/dividendManager.js',
  'src/static/js/managers/drainerManager.js',
  'src/static/js/managers/kpiManager.js',
  'src/static/js/managers/newsManager.js',
  'src/static/js/managers/portfolioManager.js',
  'src/static/js/managers/uiManager.js',
  'src/static/js/pages/dashboard.js',
  'src/static/js/pages/historico.js',
  'src/static/js/pages/indicadores.js',
  'src/static/js/pages/login.js',
  'src/static/js/pages/logs.js',
  'static/js/pages/mantenedores.js',
  'src/static/js/utils/api.js',
  'src/static/js/utils/autoUpdater.js',
  'src/static/js/utils/commandPalette.js',
  'src/static/js/utils/dashboardLayout.js',
  'src/static/js/utils/eventHandlers.js',
  'src/static/js/utils/theme.js',
  'src/static/js/utils/toast.js'
];

describe('Verifica imports válidos de JS', () => {
  filesToCheck.forEach((filePath) => {
    it(`debe usar importaciones válidas en ${filePath}`, () => {
      const content = fs.readFileSync(path.resolve(filePath), 'utf-8');
      const importRegex = /import\\s+.*?from\\s+['"](.*?)['"]/g;
      let match;

      while ((match = importRegex.exec(content)) !== null) {
        const importPath = match[1];
        
        const isValid = importPath.startsWith('./') ||
                        importPath.startsWith('../') ||
                        importPath.startsWith('/') ||
                        importPath.startsWith('http');
        
        if (!isValid) {
          console.error(`Error: Import inválido encontrado en ${filePath}: "${importPath}"`);
        }

        expect(isValid).toBe(true, `Import inválido: "${importPath}" en ${filePath}`);
      }
    });
  });
}); 