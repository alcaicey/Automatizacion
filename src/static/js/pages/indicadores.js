// src/static/js/pages/indicadores.js

import KpiManager from '../managers/kpiManager.js';
import DividendManager from '../managers/dividendManager.js';
import UIManager from '../managers/uiManager.js';

/**
 * Crea una instancia mínima de la App para proporcionar dependencias
 * a los managers que se usan en esta página aislada.
 */
class MockApp {
    constructor() {
        this.uiManager = new UIManager(this);
    }

    async fetchData(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Error en la respuesta del servidor: ${response.status} ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error al realizar la petición a ${url}:`, error);
            if (this.uiManager) {
                this.uiManager.showFeedback('No se pudo conectar al servidor.', 'danger');
            }
            throw error;
        }
    }
}

// Punto de entrada para la página de Indicadores
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Indicadores] Página cargada. Inicializando módulos...');

    const app = new MockApp();
    
    // Instanciar los managers necesarios para esta página
    const kpiManager = new KpiManager(app);
    const dividendManager = new DividendManager(app);

    // Inicializar los widgets/módulos
    try {
        if (document.getElementById('kpi-table-widget')) {
            kpiManager.initializeWidget();
            console.log("[Indicadores] Módulo 'KpiManager' inicializado.");
        }
        
        if (document.getElementById('dividend-table-widget')) {
            dividendManager.initializeWidget();
            console.log("[Indicadores] Módulo 'DividendManager' inicializado.");
        }
    } catch (error) {
        console.error('Error inicializando los módulos de la página de indicadores:', error);
    }
});