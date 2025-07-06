// src/static/alertManager.js

class AlertManager {
    constructor(app) {
        this.app = app;
        this.widgetElement = null;
        this.alertForm = null;
        this.alertList = null;
        this.alertLoading = null;
        this.activeAlerts = [];
    }

    init(app, widgetElement) {
        this.widgetElement = widgetElement;
        this.alertForm = this.widgetElement.querySelector('#alertForm');
        this.alertList = this.widgetElement.querySelector('#alert-list');
        this.alertLoading = this.widgetElement.querySelector('#alert-loading');

        if (!this.alertForm) {
            console.warn("Módulo de Alertas no presente en esta vista o elementos no encontrados.");
            return;
        }
        
        console.log("Módulo de Alertas inicializado correctamente.");
        this.setupEventListeners();
        this.loadAlerts();
    }

    setupEventListeners() {
        if (!this.alertForm) return;
        this.alertForm.addEventListener('submit', this.handleCreateAlert.bind(this));
        
        // Usamos delegación de eventos para los botones de eliminar
        this.alertList.addEventListener('click', (e) => {
            if (e.target.classList.contains('cancel-alert-btn') || e.target.closest('.cancel-alert-btn')) {
                const button = e.target.closest('.cancel-alert-btn');
                const alertId = button.dataset.alertId;
                if (alertId) {
                    this.handleCancelAlert(alertId);
                }
            }
        });
    }

    async loadAlerts() {
        this.showLoading();
        try {
            const response = await fetch('/api/alerts');
            if (!response.ok) throw new Error(`Error del servidor: ${response.status}`);
            
            this.activeAlerts = await response.json();
            this.renderAlerts();
        } catch (error) {
            console.error('Error al cargar alertas:', error);
            this.app.showToast('Error al cargar las alertas.', 'error');
            this.renderError();
        } finally {
            this.hideLoading();
        }
    }

    async handleCreateAlert(event) {
        event.preventDefault();
        const symbol = this.alertForm.querySelector('#alertSymbol').value.toUpperCase();
        const targetPrice = this.alertForm.querySelector('#alertPrice').value;
        const condition = this.alertForm.querySelector('#alertCondition').value;

        if (!symbol || !targetPrice) {
            this.app.showToast('Debe ingresar un símbolo y un precio.', 'warning');
            return;
        }

        const newAlert = { symbol, target_price: parseFloat(targetPrice), condition };

        try {
            const response = await fetch('/api/alerts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newAlert)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error al crear la alerta');
            }
            
            this.app.showToast(`Alerta creada para ${symbol}.`, 'success');
            this.alertForm.reset();
            this.loadAlerts(); // Recargar la lista

        } catch (error) {
            console.error('Error al crear alerta:', error);
            this.app.showToast(error.message, 'error');
        }
    }
    
    async handleCancelAlert(alertId) {
        if (!confirm('¿Está seguro de que desea cancelar esta alerta?')) return;

        try {
            const response = await fetch(`/api/alerts/${alertId}`, { method: 'DELETE' });
            if (!response.ok) {
                 const errorData = await response.json();
                throw new Error(errorData.error || 'Error al cancelar la alerta');
            }
            this.app.showToast('Alerta cancelada correctamente.', 'success');
            this.loadAlerts(); // Recargar la lista
        } catch (error) {
            console.error(`Error al cancelar alerta ${alertId}:`, error);
            this.app.showToast(error.message, 'error');
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
        this.app.showToast(message, 'warning'); // Usamos 'warning' para que sea más visible

        // 2. Actualizar el estado de la alerta en el backend para no volver a dispararla.
        // Lo haremos "cancelándola", que la mueve a estado 'cancelled'
        try {
            const response = await fetch(`/api/alerts/${alert.id}`, { method: 'DELETE' });
             if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error al actualizar la alerta disparada');
            }
        } catch (error) {
            console.error(`Error al actualizar estado de alerta ${alert.id}:`, error);
            // No notificamos al usuario para no ser muy ruidosos, pero lo logueamos.
        }
    }

    renderAlerts() {
        this.alertList.innerHTML = '';
        if (this.activeAlerts.length === 0) {
            this.alertList.innerHTML = '<li class="list-group-item text-muted small">No hay alertas activas.</li>';
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
                this.alertList.appendChild(item);
            });
        }
    }

    renderError() {
        this.alertList.innerHTML = `
            <li class="list-group-item text-danger small">
                No se pudieron cargar las alertas. Intente recargar.
            </li>`;
    }

    showLoading() {
        if (!this.alertLoading) return;
        this.alertLoading.classList.remove('d-none');
        this.alertList.classList.add('d-none');
    }

    hideLoading() {
        if (!this.alertLoading) return;
        this.alertLoading.classList.add('d-none');
        this.alertList.classList.remove('d-none');
    }
} 