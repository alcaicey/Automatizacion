// src/static/js/managers/portfolioManager.js
export default class PortfolioManager {
    constructor(app) {
        this.app = app;
        this.uiManager = app.uiManager;
        this.container = null;
        this.dom = {}; // Para almacenar elementos del DOM
        this.state = {
            portfolio: [],
            columnPrefs: {
                all: [],
                visible: []
            },
            lastPriceMap: new Map()
        };
    }

    async initializeWidget(container) {
        if (!container) {
            console.warn('[PortfolioManager] Contenedor no definido.');
            return;
        }
        this.container = container;
        // Asignar elementos del DOM aquí para tenerlos disponibles
        this.dom.alertContainer = this.container.querySelector('.widget-feedback-alert'); // Asume que hay un <div class="widget-feedback-alert"> en la plantilla
        await this.fetchAndRender();
        this.attachEventListeners();
    }

    attachEventListeners() {
        // Ejemplo: si tuvieras un formulario para añadir activos en el widget
        const addAssetForm = this.container.querySelector('#portfolioForm'); // Asume un form con este id
        if (addAssetForm) {
            addAssetForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const symbol = this.container.querySelector('#portfolioSymbol').value;
                const quantity = this.container.querySelector('#portfolioQuantity').value;
                const price = this.container.querySelector('#portfolioPrice').value;
                await this.addAsset(symbol, quantity, price);
            });
        }
    }

    async fetchAndRender() {
        if (!this.container) return;
        this.showFeedback('Cargando portafolio...', 'info', true);
        try {
            const holdingsData = await this.app.fetchData('/api/portfolio/view'); 
            const columnsData = await this.app.fetchData('/api/portfolio/columns');

            this.state.columnPrefs.all = columnsData.all_columns.map(c => ({ id: c, title: c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) }));
            this.state.columnPrefs.visible = columnsData.visible_columns;
            this.state.portfolio = holdingsData.portfolio || [];

            this.render();
            this.app.uiManager.updatePortfolioSummary(holdingsData.summary);
            this.showFeedback('Portafolio cargado.', 'success');
        } catch (error) {
            console.error('[PortfolioManager] Error al refrescar datos:', error);
            this.showFeedback(`Error al cargar portafolio: ${error.message}`, 'danger');
            this.render(); // Renderizar tabla vacía
        }
    }

    async addAsset(symbol, quantity, price) {
        this.showFeedback('Añadiendo activo...', 'info', true);
        try {
            const newAsset = await this.app.fetchData('/api/portfolio/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, quantity, purchase_price: price })
            });
            this.showFeedback(`Activo ${newAsset.symbol} añadido con éxito.`, 'success');
            await this.fetchAndRender(); // Refrescar todo el portafolio
        } catch (error) {
            console.error('[PortfolioManager] Error al añadir activo:', error);
            this.showFeedback(`Error al añadir activo: ${error.message}`, 'danger');
        }
    }

    async deleteAsset(assetId) {
        this.showFeedback('Eliminando activo...', 'info', true);
        try {
            await this.app.fetchData(`/api/portfolio/delete/${assetId}`, { method: 'DELETE' });
            this.showFeedback('Activo eliminado con éxito.', 'success');
            await this.fetchAndRender();
        } catch (error) {
            console.error('[PortfolioManager] Error al eliminar activo:', error);
            this.showFeedback(`Error al eliminar activo: ${error.message}`, 'danger');
        }
    }

    async saveColumnPreferences(visibleColumns) {
        this.showFeedback('Guardando preferencias...', 'info', true);
        try {
            await this.app.fetchData('/api/portfolio/columns', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ visible_columns: visibleColumns })
            });
            this.showFeedback('Preferencias de columnas guardadas.', 'success');
        await this.fetchAndRender();
        } catch (error) {
            console.error('[PortfolioManager] Error al guardar preferencias:', error);
            this.showFeedback(`Error al guardar preferencias: ${error.message}`, 'danger');
        }
    }
    
    render() {
        if (!this.container) return; // No renderizar si no hay contenedor
        
        // Buscar la tabla DENTRO del contenedor del widget
        const tableElement = this.container.querySelector('#portfolioTable'); 
        if (!tableElement) {
             console.error('[PortfolioManager] No se encontró #portfolioTable dentro del widget.');
             return;
        }

        const columnMap = new Map(this.state.columnPrefs.all.map(c => [c.id, c.title]));
        const dtColumns = this.state.columnPrefs.visible.map(key => ({
            data: key,
            title: columnMap.get(key) || key
        }));
        const finalColumns = this.app.applyColumnRenderers(dtColumns);
        
        // Pasamos el ID real de la tabla al uiManager
        this.uiManager.renderTable(tableElement.id, this.state.portfolio, finalColumns, { order: [[0, 'asc']] });
    }

    showFeedback(message, type = 'info', isLoading = false) {
        // Asumimos que hay un elemento para mostrar feedback en la plantilla del widget
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

        if (!isLoading) {
            setTimeout(() => alert.classList.add('d-none'), 5000);
        }
    }
}