// src/static/js/pages/dashboard.js

import UIManager from '../managers/uiManager.js';
import PortfolioManager from '../managers/portfolioManager.js';

export default class Dashboard {
    constructor(app) {
        this.app = app;
        this.uiManager = app.uiManager;
        this.portfolioManager = app.portfolioManager;
        this.socket = app.socket; // Corregido: Usar el socket de la app
    }

    initialize() {
        console.log('[Dashboard] Inicializando...');
        // En un entorno real, `io()` crea el socket. En los tests, ya lo hemos inyectado.
        this.socket = this.socket || io(); 
        this.setupSocketListeners();
        // Lógica de inicialización específica del dashboard
        // que no depende de un widget específico.
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('[Socket.IO] Conectado al servidor.');
            this.uiManager.updateStatus('Conectado al servidor.', 'success');
        });

        this.socket.on('disconnect', () => {
            console.warn('[Socket.IO] Desconectado del servidor.');
            this.uiManager.updateStatus('Desconectado. Intentando reconectar...', 'warning');
        });

        this.socket.on('connect_error', (err) => {
            console.error('[Socket.IO] Error de conexión:', err);
            this.uiManager.updateStatus(`Error de conexión: ${err.message}`, 'danger');
        });

        this.socket.on('last_update', (data) => {
            this.uiManager.updateLastUpdateTimestamp(data.timestamp);
            this.app.state.stocks = data.stocks;
            
            // Re-renderizar las tablas que dependen de estos datos
            this.app.portfolioManager.render(data.stocks);
        });
        
        this.socket.on('stock_prices_updated', (data) => {
            console.log('Nuevos precios recibidos:', data);
            this.uiManager.updateLastUpdateTimestamp(data.timestamp);
            
            // Aquí se podría añadir lógica para resaltar cambios en las tablas
            this.app.portfolioManager.render(data.stocks); // Re-render simple por ahora
        });
    }
}

// Esto no debería ser necesario si app.js se encarga de instanciarlo.
// Lo comento por ahora, para que se alinee con la arquitectura.
// document.addEventListener('DOMContentLoaded', () => {
//     const app = window.app; // Asume que app.js ya creó la instancia global
//     if (app) {
//         app.dashboard = new Dashboard(app);
//         app.dashboard.initialize();
//     } else {
//         console.error("La instancia principal de la App no fue encontrada. El Dashboard no puede inicializarse.");
//     }
// });