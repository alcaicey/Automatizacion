import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import DashboardLayout from '../../../src/static/js/utils/dashboardLayout.js';

// Mockear dependencias globales como GridStack si es necesario
const mockGridStack = {
    init: vi.fn(() => mockGridStack),
    addWidget: vi.fn(),
    on: vi.fn(),
};
global.GridStack = mockGridStack;

describe('DashboardLayout', () => {
    let app;

    beforeEach(() => {
        // Mockear una app básica con los managers necesarios
        app = {
            uiManager: { toggleLoading: vi.fn() },
            botStatusManager: { initializeWidget: vi.fn() },
            alertManager: { initializeWidget: vi.fn() },
            portfolioManager: { initializeWidget: vi.fn() },
            closingManager: { initializeWidget: vi.fn() },
            newsManager: { initializeWidget: vi.fn() },
            drainerManager: { initializeWidget: vi.fn() },
            dividendManager: { initializeWidget: vi.fn() },
            kpiManager: { initializeWidget: vi.fn() },
            getAllWidgetsInfo: vi.fn().mockReturnValue([
                { id: 'test-widget', name: 'Test Widget', manager: { initializeWidget: vi.fn() } }
            ]),
        };
        // Configurar el DOM necesario para las pruebas
        document.body.innerHTML = '<div id="widget-list"></div><template id="test-widgetTemplate"></template>';
    });

    it('no debe inicializar el manager si el widget se elimina antes del timeout', () => {
        vi.useFakeTimers();
        const layout = new DashboardLayout(app);
        layout.grid = mockGridStack; // Asignar el grid mockeado

        const fakeWidgetEl = document.createElement('div');
        fakeWidgetEl.id = 'test-widget';
        // Simular que el grid devuelve este elemento
        mockGridStack.addWidget.mockReturnValue(fakeWidgetEl);

        const mockManager = app.getAllWidgetsInfo()[0].manager;
        const consoleSpy = vi.spyOn(console, 'warn');

        // Acción: añadir el widget
        layout.addWidget('test-widget');

        // Simular que el elemento se añade al DOM por el grid y luego se elimina
        document.body.appendChild(fakeWidgetEl);
        document.body.removeChild(fakeWidgetEl);

        // Avanzar los timers para que se ejecute el setTimeout
        vi.runAllTimers();

        // Verificaciones
        expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("fue eliminado antes de que su manager pudiera inicializarse"));
        expect(mockManager.initializeWidget).not.toHaveBeenCalled();

        // Limpieza
        consoleSpy.mockRestore();
        vi.useRealTimers();
    });
}); 