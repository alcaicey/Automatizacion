// src/static/js/managers/botStatusManager.js
// Este archivo controlará la lógica del widget de estado del bot. 

import { format, parseISO } from 'https://cdn.skypack.dev/date-fns';

export default class BotStatusManager {
    constructor(app) {
        this.app = app;
        this.socket = app.socket; // Usar el socket de la app
        this.autoUpdater = app.autoUpdater;

        // --- INICIO DE LA CORRECCIÓN ---
        // Estado interno para el manager
        this.state = {
            isUpdating: false,
            lastUpdate: null,
            message: 'No inicializado.',
            errorMessage: null // Añadido para un estado inicial completo
        };
        // --- FIN DE LA CORRECCIÓN ---

        // Referencias al DOM se asignan en initializeWidget
        this.alertElement = null;
        this.lastUpdateElement = null;
        this.updateNowBtn = null;
    }

    // --- INICIO DE LA CORRECCIÓN ---
    // Métodos para gestionar el estado
    getState() {
        return this.state;
    }

    setUpdating(isUpdating, message = '') {
        this.state.isUpdating = isUpdating;
        if (message) {
            this.state.message = message;
        }
        // Reflejar el estado en la UI
        this.updateNowBtn.disabled = isUpdating;
        if (isUpdating) {
            this.updateStatus(message || 'Actualización en curso...', 'info', true);
        }
    }
    // --- FIN DE LA CORRECCIÓN ---

    initializeWidget(widgetElement) {
        if (!widgetElement) {
            console.warn('[BotStatusManager] Contenedor del widget no definido. Cancelando inicialización.');
            return;
        }

        this.alertElement = widgetElement.querySelector('#bot-status-alert');
        this.lastUpdateElement = widgetElement.querySelector('#last-update-time');
        this.updateNowBtn = widgetElement.querySelector('#update-now-btn');
        
        if (!this.alertElement || !this.updateNowBtn) {
            console.error("Elementos de la interfaz de estado del bot no encontrados dentro del widget.");
            return;
        }

        this.setupSocketListeners();
        // El event listener se asigna aquí directamente para garantizar que el botón existe.
        this.updateNowBtn.addEventListener('click', () => this.handleManualRefresh());
        this.requestInitialStatus();
    }

    setupSocketListeners() {
        this.socket.on('connect', () => this.updateStatus('Conectado al servidor.', 'success'));
        this.socket.on('disconnect', () => this.updateStatus('Desconectado del servidor.', 'danger'));
        this.socket.on('bot_status', (data) => this.handleBotStatus(data));
        this.socket.on('bot_error', (data) => this.updateStatus(data.message, 'danger'));
    }

    requestInitialStatus() {
        this.updateStatus('Obteniendo estado...', 'secondary', true);
        this.socket.emit('request_bot_status');
    }

    handleBotStatus(data) {
        const { is_running, last_update, message, error } = data;
        // --- INICIO DE LA CORRECCIÓN ---
        this.state.isUpdating = is_running;
        this.state.lastUpdate = last_update;
        this.state.message = message;
        this.state.errorMessage = error || null;
        // --- FIN DE LA CORRECCIÓN ---

        const color = is_running ? 'info' : (error ? 'danger' : 'success');
        this.updateStatus(message, color, is_running);
        
        if(this.updateNowBtn) {
            this.updateNowBtn.disabled = is_running;
        }
        if(this.lastUpdateElement) {
            this.lastUpdateElement.textContent = last_update ? new Date(last_update).toLocaleString() : 'Nunca';
        }
    }

    updateStatus(message, type = 'secondary', loading = false) {
        if (!this.alertElement) return;
        const spinner = this.alertElement.querySelector('.spinner-border');
        const span = this.alertElement.querySelector('span');

        this.alertElement.className = `alert alert-${type}`;
        if(span) span.textContent = message;
        if(spinner) spinner.style.display = loading ? 'inline-block' : 'none';
    }

    handleManualRefresh() {
        console.log('[BotStatusManager] Botón "Actualizar Ahora" presionado. Emitiendo evento "manual_update".');
        this.socket.emit('manual_update');
        this.setUpdating(true, 'Iniciando actualización manual...');
    }
} 