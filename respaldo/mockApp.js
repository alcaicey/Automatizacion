// tests/js/utils/mockApp.js
import { vi } from 'vitest';

/**
 * Proporciona un objeto 'app' simulado para inyectar en los constructores 
 * de los diferentes managers durante las pruebas con Vitest.
 * 
 * Esto nos permite aislar los componentes y espiar las interacciones.
 */
export function createMockApp() {
  return {
    // Socket.IO mockeado para espiar eventos emit
    socket: {
        emit: vi.fn(),
        on: vi.fn(),
        off: vi.fn(),
    },
    // AutoUpdater mockeado
    autoUpdater: {
        init: vi.fn(),
        stop: vi.fn(),
        start: vi.fn()
    },
    // UIManager mockeado
    uiManager: {
        showFeedback: vi.fn(),
        toggleLoading: vi.fn(),
        renderTable: vi.fn(),
        updatePortfolioSummary: vi.fn(), // Corregido: movido dentro de uiManager
        getDataTablesLang: vi.fn(() => ({})), // Añadido para drainerManager
    },
    // BotStatusManager mockeado (versión simple)
    botStatusManager: {
        updateStatus: vi.fn(),
        setUpdating: vi.fn(),
        getState: vi.fn(() => ({ isUpdating: false })),
    },
    // Theme mockeado
    theme: {
        toggleDarkMode: vi.fn(),
    },
    // Mock de la función de fetch para controlar respuestas de API
    fetchData: vi.fn(),
    // Funciones de renderizado que podrían ser llamadas por otros managers
    applyColumnRenderers: vi.fn(),
    renderTable: vi.fn(),
  };
} 