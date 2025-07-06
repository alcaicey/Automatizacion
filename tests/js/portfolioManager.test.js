// tests/js/portfolioManager.test.js

/**
 * @jest-environment jsdom
 */

require('@testing-library/jest-dom/extend-expect');
const portfolioManager = require('../../src/static/portfolioManager').portfolioManager;

// Mock del objeto 'app' y sus dependencias que necesita portfolioManager
const mockApp = {
    uiManager: {
        renderTable: jest.fn(),
        updatePortfolioSummary: jest.fn(),
        updateStatus: jest.fn(),
    },
};

describe('portfolioManager', () => {
    beforeEach(() => {
        // Reset mocks before each test
        jest.clearAllMocks();
        
        // Simular el DOM que el portfolioManager espera encontrar
        document.body.innerHTML = `
            <div id="portfolio-widget">
                <table id="portfolioTable"></table>
            </div>
            <div id="status-bar"></div>
        `;
        
        // Adjuntar el mock de la app al manager
        portfolioManager.app = mockApp;
    });

    afterEach(() => {
        // Limpiar el mock de fetch
        jest.restoreAllMocks();
    });

    test('debería cargar y renderizar los datos del portafolio exitosamente', async () => {
        const mockPortfolioData = {
            portfolio: [
                { symbol: 'AAPL', quantity: 10, purchase_price: 150, current_price: 170 },
                { symbol: 'GOOG', quantity: 5, purchase_price: 2800, current_price: 2900 },
            ],
            summary: {
                total_paid: 15500,
                current_value: 16200,
            }
        };

        // Mock de la función fetch para devolver datos exitosos
        jest.spyOn(global, 'fetch').mockResolvedValue({
            ok: true,
            json: jest.fn().mockResolvedValue(mockPortfolioData),
        });

        await portfolioManager.fetchPortfolioData();

        // Verificar que el resumen se haya actualizado
        expect(mockApp.uiManager.updatePortfolioSummary).toHaveBeenCalledWith(mockPortfolioData.summary);
        
        // Verificar que la tabla se haya renderizado
        expect(mockApp.uiManager.renderTable).toHaveBeenCalledWith(
            'portfolioTable', 
            mockPortfolioData.portfolio,
            expect.any(Array) // Comprobar que se pasaron las columnas
        );

        // Verificar que no se llamó al estado de error
        expect(mockApp.uiManager.updateStatus).not.toHaveBeenCalled();
    });

    test('debería manejar un error cuando la carga de datos del portafolio falla', async () => {
        // Mock de la función fetch para simular un error de red
        jest.spyOn(global, 'fetch').mockRejectedValue(new Error('Error de red simulado'));
        
        await portfolioManager.fetchPortfolioData();

        // Verificar que no se llamó a las funciones de renderizado
        expect(mockApp.uiManager.updatePortfolioSummary).not.toHaveBeenCalled();
        expect(mockApp.uiManager.renderTable).not.toHaveBeenCalled();

        // Verificar que se mostró un mensaje de error
        expect(mockApp.uiManager.updateStatus).toHaveBeenCalledWith(
            'Error al cargar portafolio.',
            'danger'
        );
    });

    test('debería manejar una respuesta no-OK del servidor', async () => {
        // Mock de la función fetch para simular una respuesta de error del servidor (p.ej. 500)
        jest.spyOn(global, 'fetch').mockResolvedValue({
            ok: false,
        });

        await portfolioManager.fetchPortfolioData();

        // Verificar que no se llamó a las funciones de renderizado
        expect(mockApp.uiManager.updatePortfolioSummary).not.toHaveBeenCalled();
        expect(mockApp.uiManager.renderTable).not.toHaveBeenCalled();

        // Verificar que se mostró un mensaje de error
        expect(mockApp.uiManager.updateStatus).toHaveBeenCalledWith(
            'Error al cargar portafolio.',
            'danger'
        );
    });
}); 