// src/static/js/managers/closingManager.js

export default class ClosingManager {
    constructor(app) {
        this.app = app;
        this.uiManager = app.uiManager;
        this.dom = {};
        this.state = {
            closings: [],
            columnPrefs: {
                all: [],
                visible: []
            }
        };
        this.dataTable = null;
    }

    initializeWidget(container) {
        if (!container) return;
        this.dom = {
            table: container.querySelector('.closing-table'), // Asume que la tabla tiene esta clase
            alertContainer: container.querySelector('.widget-feedback-alert'),
        };
        this.loadData();
    }

    async loadData() {
        this.showFeedback('Cargando datos de cierre...', 'info', true);
        try {
            const data = await this.app.fetchData('/api/data/closing');
            this.state.closings = data || [];
            this.render();
            this.showFeedback(`Se cargaron ${this.state.closings.length} registros de cierre.`, 'success');
        } catch (error) {
            console.error("[ClosingManager] Error al cargar datos de cierre:", error);
            this.state.closings = [];
            this.render();
            this.showFeedback(`Error al cargar datos: ${error.message}`, 'danger');
        }
    }

    render() {
        if (!this.dom.table) return;
        // Lógica de renderizado de la tabla con this.uiManager.renderTable
        // Ejemplo:
        const columns = Object.keys(this.state.closings[0] || {}).map(key => ({
            data: key,
            title: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ')
        }));
        
        this.uiManager.renderTable(this.dom.table.id, this.state.closings, columns, {});
    }

    showFeedback(message, type = 'info', isLoading = false) {
        if (!this.dom.alertContainer) return;
        const alert = this.dom.alertContainer;
        alert.className = `widget-feedback-alert alert alert-${type} d-flex align-items-center`;
        
        let content = '';
        if (isLoading) {
            content += '<div class="spinner-border spinner-border-sm me-2" role="status"></div>';
        }
        content += `<span>${message}</span>`;
        
        alert.innerHTML = content;
        alert.classList.remove('d-none');

        if (!isLoading && type !== 'info') {
            setTimeout(() => alert.classList.add('d-none'), 5000);
        }
    }
}