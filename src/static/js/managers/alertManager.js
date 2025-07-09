// src/static/js/managers/alertManager.js

export default class AlertManager {
    constructor(app) {
        this.app = app;
        this.dom = {}; // Centralizar elementos del DOM
        this.activeAlerts = [];
    }

    initializeWidget(container) {
        if (!container) return;
        
        this.dom = {
            form: container.querySelector('#alertForm'),
            list: container.querySelector('#alert-list'),
            loading: container.querySelector('#alert-loading'),
            // Usaremos el contenedor del widget para el feedback
            feedbackContainer: container.querySelector('.widget-body'),
        };

        if (!this.dom.form) return;
        
        this.setupEventListeners();
        this.loadAlerts();
    }

    setupEventListeners() {
        this.dom.form.addEventListener('submit', (e) => this.handleCreateAlert(e));
        
        this.dom.list.addEventListener('click', (e) => {
            const cancelButton = e.target.closest('.cancel-alert-btn');
            if (cancelButton) {
                this.handleCancelAlert(cancelButton.dataset.alertId);
            }
        });
    }

    async loadAlerts() {
        this.showFeedback('Cargando alertas...', 'info', true);
        try {
            this.activeAlerts = await this.app.fetchData('/api/data/alerts') || [];
            this.renderAlerts();
            // No mostramos feedback de éxito para mantener la UI limpia
        } catch (error) {
            console.error('[AlertManager] Error al cargar alertas:', error);
            this.showFeedback(`Error al cargar alertas.`, 'danger');
            this.renderAlerts(); // Renderizará la lista vacía con el mensaje adecuado
        }
    }

    async handleCreateAlert(event) {
        event.preventDefault();
        const symbol = this.dom.form.querySelector('#alertSymbol').value.toUpperCase();
        const targetPrice = this.dom.form.querySelector('#alertPrice').value;
        const condition = this.dom.form.querySelector('#alertCondition').value;

        if (!symbol || !targetPrice) {
            this.app.uiManager.showToast('Debe ingresar un símbolo y un precio.', 'warning');
            return;
        }

        const newAlert = { symbol, target_price: parseFloat(targetPrice), condition };

        this.showFeedback('Creando alerta...', 'info', true);
        try {
            await this.app.fetchData('/api/data/alerts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newAlert)
            });
            
            this.app.uiManager.showToast(`Alerta para ${symbol} creada con éxito.`, 'success');
            this.dom.form.reset();
            await this.loadAlerts();
        } catch (error) {
            console.error('[AlertManager] Error al crear alerta:', error);
            this.app.uiManager.showToast(`Error al crear alerta: ${error.message}`, 'danger');
            this.loadAlerts(); // Recargar para limpiar el estado
        }
    }
    
    async handleCancelAlert(alertId) {
        if (!confirm('¿Está seguro de que desea cancelar esta alerta?')) return;
        
        this.showFeedback('Cancelando alerta...', 'info', true);
        try {
            await this.app.fetchData(`/api/data/alerts/${alertId}`, { method: 'DELETE' });
            this.app.uiManager.showToast('Alerta cancelada correctamente.', 'success');
            await this.loadAlerts();
        } catch (error) {
            console.error(`[AlertManager] Error al cancelar alerta ${alertId}:`, error);
            this.app.uiManager.showToast(`Error al cancelar alerta: ${error.message}`, 'danger');
            this.loadAlerts(); // Recargar para limpiar el estado
        }
    }

    checkAlerts(marketData) {
        if (!marketData || !marketData.data || this.activeAlerts.length === 0) {
            return;
        }

        const triggeredAlerts = [];

        this.activeAlerts.forEach(alert => {
            const stock = marketData.data.find(d => d.NEMO === alert.symbol);
            if (!stock) return;

            const currentPrice = parseFloat(stock.PRECIO_CIERRE.replace(/[^0-9,-]+/g, "").replace(",", "."));
            if (isNaN(currentPrice)) return;
            
            const conditionMet = 
                (alert.condition === 'above' && currentPrice >= alert.target_price) ||
                (alert.condition === 'below' && currentPrice <= alert.target_price);

            if (conditionMet) {
                triggeredAlerts.push(alert);
            }
        });

        if (triggeredAlerts.length > 0) {
            triggeredAlerts.forEach(alert => {
                this.handleTriggeredAlert(alert);
            });
            // Recargar la lista de alertas activas ya que algunas se habrán disparado
            this.loadAlerts();
        }
    }

    async handleTriggeredAlert(alert) {
        console.log(`¡ALERTA DISPARADA! Símbolo: ${alert.symbol}, Condición: ${alert.condition}, Precio Obj: ${alert.target_price}`);
        
        // 1. Mostrar notificación visual al usuario
        const conditionText = alert.condition === 'above' ? 'alcanzó o superó' : 'alcanzó o cayó por debajo de';
        const message = `<strong>${alert.symbol}</strong> ${conditionText} los $${alert.target_price.toLocaleString('es-CL')}.`;
        this.app.uiManager.showToast(message, 'warning'); // Usamos 'warning' para que sea más visible

        // 2. Actualizar el estado de la alerta en el backend para no volver a dispararla.
        // Lo haremos "cancelándola", que la mueve a estado 'cancelled'
        try {
            await this.app.fetchData(`/api/data/alerts/${alert.id}`, { method: 'DELETE' });
        } catch (error) {
            console.error(`Error al actualizar estado de alerta ${alert.id}:`, error);
            // No notificamos al usuario para no ser muy ruidosos, pero lo logueamos.
        }
    }

    renderAlerts() {
        this.dom.list.innerHTML = '';
        if (this.activeAlerts.length === 0) {
            this.dom.list.innerHTML = '<li class="list-group-item text-muted small">No hay alertas activas.</li>';
        } else {
            this.activeAlerts.forEach(alert => {
                const conditionText = alert.condition === 'above' ? '&ge;' : '&le;';
                const item = document.createElement('li');
                item.className = 'list-group-item d-flex justify-content-between align-items-center small';
                item.innerHTML = `
                    <span>
                        <strong class="text-warning-emphasis">${alert.symbol}</strong>
                        <span class="text-muted">${conditionText}</span>
                        $${alert.target_price.toLocaleString('es-CL')}
                    </span>
                    <button class="btn btn-xs btn-outline-danger cancel-alert-btn" data-alert-id="${alert.id}" title="Cancelar Alerta">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                this.dom.list.appendChild(item);
            });
        }
        this.showFeedback('', 'info', false); // Ocultar el loader
    }

    showFeedback(message, type = 'info', isLoading = false) {
        if (this.dom.loading) {
            this.dom.loading.style.display = isLoading ? 'block' : 'none';
            this.dom.list.style.display = isLoading ? 'none' : 'block';
        }
        // Para errores, podríamos usar un toast global ya que este widget no tiene un alert dedicado
        if (type === 'danger') {
            this.app.uiManager.showToast(message, 'danger');
        }
    }
} 