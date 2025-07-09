// src/static/js/pages/dashboard.js

import BotStatusManager from '../managers/botStatusManager.js';
import NewsManager from '../managers/newsManager.js';
import AlertManager from '../managers/alertManager.js';

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

        this.socket.on('disconnect', (reason) => {
            console.warn('[Socket.IO] Desconectado del servidor:', reason);
            this.uiManager.updateStatus('Desconectado. Intentando reconectar...', 'warning');
            if (reason === 'io server disconnect') {
                // el servidor cerró la conexión, puedes intentar reconectar
                this.socket.connect();
            }
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

        this.socket.on('update_complete', (data) => {
            console.log('[Socket.IO] Evento "update_complete" recibido:', data);
            
            // 1. Notificar al usuario (opcional pero recomendado)
            this.app.uiManager.showFeedback('success', '¡Actualización completada!');
    
            // 2. Ordenar a los managers relevantes que se refresquen
            if (this.app.portfolioManager) {
                console.log('[Dashboard] Ordenando a PortfolioManager que se refresque.');
                this.app.portfolioManager.refresh(); 
            }
    
            if (this.app.botStatusManager && data.last_update_timestamp) {
                console.log('[Dashboard] Actualizando estado del bot.');
                // Le pasamos el timestamp directamente para que no tenga que hacer otra llamada a la API
                this.app.botStatusManager.updateStatus(
                    'Actualización completada.',
                    'success',
                    false, // No está cargando
                    data.last_update_timestamp
                );
            }
            
            // 3. Puedes añadir aquí llamadas a otros managers que necesiten refrescarse
            // if (this.app.newsManager) { this.app.newsManager.refresh(); }
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