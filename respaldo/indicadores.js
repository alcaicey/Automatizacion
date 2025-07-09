// src/static/js/pages/indicadores.js

import KpiManager from '../managers/kpiManager.js';
import DividendManager from '../managers/dividendManager.js';
import UIManager from '../managers/uiManager.js';

class MockApp {
    constructor() {
        this.uiManager = new UIManager(this);
        
        // --- INICIO DE LA CORRECCIÓN ---
        // Asegurarnos de que el socket SIEMPRE se inicialice aquí,
        // ya que tanto KpiManager como DividendManager lo necesitan.
        try {
            this.socket = io();
            console.log("[Indicadores MockApp] Socket.IO inicializado.");
        } catch (e) {
            console.error("[Indicadores MockApp] Error al inicializar Socket.IO. Asegúrate de que el script de socket.io esté cargado en el HTML.", e);
            // Proporcionar un objeto de socket falso para evitar que la app crashee
            this.socket = {
                on: () => {},
                emit: () => {}
            };
        }
        // --- FIN DE LA CORRECCIÓN ---
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
                // this.uiManager.showFeedback('No se pudo conectar al servidor.', 'danger');
            }
            throw error;
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('[Indicadores] Página cargada. Inicializando módulos...');

    const app = new MockApp();
    
    const kpiManager = new KpiManager(app);
    const dividendManager = new DividendManager(app);

    try {
        const kpiContainer = document.getElementById('module-financial-kpis');
        if (kpiContainer) {
            kpiManager.initializeWidget(kpiContainer);
            console.log("[Indicadores] Módulo 'KpiManager' inicializado.");
        }
        
        const dividendContainer = document.getElementById('module-dividends');
        if (dividendContainer) {
            dividendManager.initializeWidget(dividendContainer);
            console.log("[Indicadores] Módulo 'DividendManager' inicializado.");
        }
    } catch (error) {
        console.error('Error inicializando los módulos de la página de indicadores:', error);
    }
});