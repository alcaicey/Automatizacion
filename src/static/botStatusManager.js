// src/static/botStatusManager.js
// Este archivo controlará la lógica del widget de estado del bot. 

class BotStatusManager {
    constructor() {
        this.statusAlert = document.getElementById('bot-status-alert');
        this.statusSpinner = this.statusAlert.querySelector('.spinner-border');
        this.statusSpan = this.statusAlert.querySelector('span');
        this.updateButton = document.getElementById('update-now-btn');
        this.lastUpdateTime = document.getElementById('last-update-time');
    }

    init() {
        if (!this.statusAlert || !this.updateButton) {
            console.error("Elementos de la interfaz de estado del bot no encontrados.");
            return;
        }
        this.statusSpan.textContent = 'Obteniendo estado...';
        this.updateButton.addEventListener('click', () => this.handleUpdateClick());
    }

    updateStatus(message, type = 'secondary', loading = false) {
        this.statusAlert.className = `alert alert-${type}`;
        this.statusSpan.textContent = message;
        this.statusSpinner.style.display = loading ? 'inline-block' : 'none';
        this.updateButton.disabled = loading;
    }

    async handleUpdateClick() {
        this.updateStatus('Actualizando...', 'info', true);
        try {
            const response = await fetch('/api/stocks/update', { method: 'POST' });
            const data = await response.json();
            if (response.ok && data.success) {
                this.updateStatus(data.message, 'success', false);
            } else {
                this.updateStatus(data.message || 'Error desconocido', 'danger', false);
            }
        } catch (error) {
            console.error('Error en la comunicación con el servidor:', error);
            this.updateStatus('Error de conexión con el servidor.', 'danger', false);
            // Propagar el error para que los llamadores (como los tests) sepan que algo falló
            throw error;
        }
    }
}

export default BotStatusManager; 