// src/static/js/managers/botStatusManager.js

export default class BotStatusManager {
    constructor(app) {
        this.app = app;
        this.socket = app.socket;
        this.dom = {};
        this.updateInterval = null;
        this.nextUpdateTimer = null;
    }

    initializeWidget(container) {
        if (!container) {
            console.error('[BotStatusManager] Contenedor no proporcionado. Abortando inicialización.');
            return;
        }

        this.dom = {
            alert: container.querySelector('#bot-status-alert'),
            autoUpdateSelect: container.querySelector('#auto-update-select'),
            updateNowBtn: container.querySelector('#update-now-btn'),
            lastUpdateEl: container.querySelector('#last-update-time'),
            nextUpdateEl: container.querySelector('#next-update-time'),
            outsideHoursSwitch: container.querySelector('#update-outside-hours-switch')
        };

        if (!this.dom.alert || !this.dom.autoUpdateSelect || !this.dom.updateNowBtn || !this.dom.outsideHoursSwitch) {
            console.error('[BotStatusManager] No se encontraron todos los elementos DOM necesarios. Abortando inicialización.');
            return;
        }

        this.attachEventListeners();
        this.loadInitialState();
    }

    attachEventListeners() {
        this.dom.autoUpdateSelect.addEventListener('change', (e) => this.handleIntervalChange(e));
        this.dom.updateNowBtn.addEventListener('click', () => this.handleUpdateNow());
        this.dom.outsideHoursSwitch.addEventListener('change', (e) => this.handleOutsideHoursChange(e));

        this.socket.on('bot_status_update', (data) => this.updateStatus(data));
        this.socket.on('auto_update_interval_set', (data) => {
            this.app.uiManager.showToast(`Intervalo de auto-actualización fijado en ${data.interval} minutos.`);
            this.dom.autoUpdateSelect.value = data.interval;
        });
        
        // Respuesta del servidor tras cambiar la config de "fuera de horario"
        this.socket.on('setting_updated', (data) => {
            if (data.key === 'ALLOW_UPDATE_OUTSIDE_HOURS') {
                this.app.uiManager.showToast('Configuración de actualización fuera de horario guardada.');
                this.dom.outsideHoursSwitch.checked = data.value === 'true';
            }
        });
    }

    loadInitialState() {
        this.getStatus();
        this.getAutoUpdateInterval();
        this.getOutsideHoursSetting();
    }

    getStatus() {
        console.log('[BotStatusManager] Obteniendo estado del bot...');
        this.socket.emit('get_bot_status');
    }

    getAutoUpdateInterval() {
        console.log('[BotStatusManager] Obteniendo intervalo de auto-actualización...');
        this.socket.emit('get_auto_update_interval');
    }
    
    async getOutsideHoursSetting() {
        try {
            console.log('[BotStatusManager] Obteniendo configuración de actualización fuera de horario...');
            const setting = await this.app.fetchData('/api/config/bot_settings/ALLOW_UPDATE_OUTSIDE_HOURS');
            if (setting) {
                this.dom.outsideHoursSwitch.checked = setting.value === 'true';
            }
        } catch (error) {
            if (error.message.includes('404')) {
                console.log('[BotStatusManager] No se encontró configuración inicial para "fuera de horario". Se usará el valor por defecto (desactivado).');
                this.dom.outsideHoursSwitch.checked = false;
            } else {
                console.error('Error al obtener la configuración de actualización fuera de horario:', error);
            }
        }
    }

    handleIntervalChange(event) {
        const interval = parseInt(event.target.value, 10);
        console.log(`[BotStatusManager] Solicitando cambio de intervalo a ${interval} minutos.`);
        this.socket.emit('set_auto_update_interval', { interval });
    }

    handleUpdateNow() {
        console.log('[BotStatusManager] Solicitando actualización manual...');
        this.updateStatus({ status: 'running', message: 'Actualización manual solicitada...' });
        this.socket.emit('run_bot_manually');
    }

    async handleOutsideHoursChange(event) {
        const isChecked = event.target.checked;
        console.log(`[BotStatusManager] Cambiando configuración de actualización fuera de horario a: ${isChecked}`);
        try {
            await this.app.fetchData('/api/config/bot_settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    key: 'ALLOW_UPDATE_OUTSIDE_HOURS',
                    value: isChecked.toString() 
                })
            });
            this.app.uiManager.showToast('Configuración guardada. Se reflejará por socket.');
        } catch (error) {
            console.error('Error al guardar la configuración de actualización fuera de horario:', error);
            this.app.uiManager.showToast('No se pudo guardar la configuración.', 'danger');
            event.target.checked = !isChecked; // Revertir cambio en UI
        }
    }

    updateStatus(data) {
        const { status, message, last_update, next_update } = data;
        let alertClass = 'alert-secondary';
        let statusIcon = '<div class="spinner-border spinner-border-sm me-2" role="status"><span class="visually-hidden">Cargando...</span></div>';
        let statusMessage = message || 'Obteniendo estado...';

        switch (status) {
            case 'idle':
                alertClass = 'alert-primary';
                statusIcon = '<i class="fas fa-check-circle me-2"></i>';
                break;
            case 'running':
                alertClass = 'alert-info';
                statusIcon = '<div class="spinner-border spinner-border-sm me-2" role="status"></div>';
                break;
            case 'success':
                alertClass = 'alert-success';
                statusIcon = '<i class="fas fa-check-double me-2"></i>';
                break;
            case 'error':
                alertClass = 'alert-danger';
                statusIcon = '<i class="fas fa-exclamation-triangle me-2"></i>';
                break;
        }

        this.dom.alert.className = `alert ${alertClass} mb-0`;
        this.dom.alert.innerHTML = `<div class="d-flex align-items-center">${statusIcon}<span>${statusMessage}</span></div>`;

        this.dom.lastUpdateEl.textContent = last_update ? this.formatTime(last_update) : '--';
        this.dom.nextUpdateEl.textContent = next_update ? this.formatTime(next_update) : '--';
    }

    formatTime(isoString) {
        if (!isoString) return '--';
        try {
            return new Date(isoString).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return '--';
        }
    }

    async fetchInitialStatus() {
        this.showLoading();
        try {
            const setting = await this.app.fetchData('/api/config/bot_settings/ALLOW_UPDATE_OUTSIDE_HOURS');
            this.isUpdateAllowed = setting ? setting.value === 'true' : false;

            this.app.socket.emit('get_bot_status');
        } catch (error) {
            console.error('Error al obtener el estado inicial del bot:', error);
        }
    }

    async saveSettings(settings) {
        this.app.showToast('Guardando configuración...');
        try {
            await this.app.fetchData('/api/config/bot_settings', {
                method: 'POST',
                body: settings
            });
            this.app.showToast('Configuración guardada con éxito.', 'success');
        } catch (error) {
            console.error('Error al guardar la configuración del bot:', error);
            this.app.showToast('Error al guardar la configuración.', 'error');
        }
    }
}