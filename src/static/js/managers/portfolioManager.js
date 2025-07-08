// src/static/js/managers/portfolioManager.js

export default class PortfolioManager {
    constructor(app) {
        this.app = app;
        this.uiManager = app.uiManager;
        this.state = {
            portfolio: [],
            columnPrefs: {
                all: [],
                visible: []
            },
            lastPriceMap: new Map()
        };
        this.grid = null; // Se establecerá en initialize
    }

    init() {
        console.log('[PortfolioManager] init() llamado. Redirigiendo a initializeWidget().');
        this.initializeWidget();
    }

    async initializeWidget(container) {
        if (!container) {
            console.warn('[PortfolioManager] Contenedor del widget de portafolio no definido. Cancelando inicialización.');
            return;
        }

        console.log('[PortfolioManager] Ejecutando initializeWidget()');
        this.uiManager.toggleLoading(true, 'Cargando datos del portafolio...');

        try {
            const [columnsData, holdingsData] = await Promise.all([
                this.app.fetchData('/api/portfolio/columns'),
                this.app.fetchData('/api/portfolio/holdings')
            ]);
            
            console.log('[PortfolioManager] Datos de columnas recibidos:', columnsData);
            console.log('[PortfolioManager] Datos de holdings recibidos:', holdingsData);

            if (!columnsData || !holdingsData) {
                throw new Error("La respuesta de la API no es válida.");
            }

            this.state.columnPrefs.all = columnsData.all_columns.map(c => ({ 
                id: c, 
                title: c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) 
            }));
            this.state.columnPrefs.visible = columnsData.visible_columns;
            
            this.state.portfolio = holdingsData.portfolio || [];

            console.log('[PortfolioManager] Holdings para la tabla:');
            console.table(this.state.portfolio);

            this.render();
            this.uiManager.updatePortfolioSummary(holdingsData.summary);
            
        } catch (error) {
            console.error('[PortfolioManager] Error al inicializar widget:', error);
            this.uiManager.showFeedback('danger', 'Error al inicializar el widget de portafolio.');
        } finally {
            this.uiManager.toggleLoading(false);
        }
    }
    
    render() {
        if (!this.app || !this.state.portfolio) {
            console.warn('[PortfolioManager] No se puede renderizar: Faltan datos o la app no está lista.');
            return;
        }

        const columnMap = new Map(this.state.columnPrefs.all.map(c => [c.id, c.title]));
        
        const dtColumns = this.state.columnPrefs.visible.map(key => ({
            data: key,
            title: columnMap.get(key) || key
        }));
        
        const finalColumns = this.app.applyColumnRenderers(dtColumns);

        console.log('[PortfolioManager] Renderizando tabla con columnas:', finalColumns);
        
        this.uiManager.renderTable(
            'portfolioTable',
            this.state.portfolio,
            finalColumns,
            {
                order: [[0, 'asc']]
            }
        );
    }

    getDisplayData(allStocks) {
        const stockPriceMap = new Map(allStocks.map(s => [s.NEMO, s]));

        return this.state.holdings.map(h => {
            const stockData = stockPriceMap.get(h.symbol) || {};
            const currentPrice = stockData.PRECIO_CIERRE || 0;
            const quantity = h.quantity;
            const purchasePrice = h.purchase_price;
            const totalPaid = quantity * purchasePrice;
            const currentValue = quantity * currentPrice;
            const gainLossTotal = currentValue - totalPaid;
            const gainLossPercent = totalPaid > 0 ? (gainLossTotal / totalPaid) * 100 : 0;

            return {
                id: h.id, // Importante para la eliminación
                symbol: h.symbol,
                quantity: quantity,
                purchase_price: purchasePrice,
                total_paid: totalPaid,
                current_price: currentPrice,
                daily_variation_percent: stockData.VARIACION || 0,
                current_value: currentValue,
                gain_loss_total: gainLossTotal,
                gain_loss_percent: gainLossPercent,
                actions: `<button class="btn btn-sm btn-danger delete-holding-btn" data-id="${h.id}"><i class="fas fa-trash"></i></button>`
            };
        });
    }

    renderSummary(displayData) {
        let totalPaid = 0;
        let totalCurrentValue = 0;

        displayData.forEach(d => {
            totalPaid += d.total_paid;
            totalCurrentValue += d.current_value;
        });

        const totalGainLoss = totalCurrentValue - totalPaid;

        const formatCurrency = (val) => new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }).format(val);

        document.getElementById('totalPaid').textContent = formatCurrency(totalPaid);
        document.getElementById('totalCurrentValue').textContent = formatCurrency(totalCurrentValue);
        
        const totalGainLossEl = document.getElementById('totalGainLoss');
        totalGainLossEl.innerHTML = formatCurrency(totalGainLoss);
        totalGainLossEl.className = totalGainLoss >= 0 ? 'h5 mb-0 text-success' : 'h5 mb-0 text-danger';
    }
    
    renderColumnModal() {
        const form = document.getElementById('portfolioColumnConfigForm');
        if (!form) return;
        form.innerHTML = this.state.columnPrefs.all.map(col => `
            <div class="col-6">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${col.id}" id="pcol_${col.id}" ${this.state.columnPrefs.visible.includes(col.id) ? 'checked' : ''}>
                    <label class="form-check-label" for="pcol_${col.id}">${col.title}</label>
                </div>
            </div>
        `).join('');
    }

    updateTotals(totalPaid, totalCurrentValue) {
        const totalGainLoss = totalCurrentValue - totalPaid;
        const totalGainLossPercent = totalPaid > 0 ? (totalGainLoss / totalPaid) * 100 : 0;

        const formatCurrency = (val) => new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }).format(val);
        const formatPercent = (val) => `<span class="${val >= 0 ? 'text-success' : 'text-danger'} fw-bold">${val.toFixed(2)}%</span>`;
        
        document.getElementById('totalPaid').textContent = formatCurrency(totalPaid);
        document.getElementById('totalCurrentValue').textContent = formatCurrency(totalCurrentValue);
        // Aplicar color al resumen superior
        const totalGainLossEl = document.getElementById('totalGainLoss');
        totalGainLossEl.innerHTML = formatCurrency(totalGainLoss);
        totalGainLossEl.className = totalGainLoss >= 0 ? 'h5 mb-0 text-success' : 'h5 mb-0 text-danger';

        // Actualizar pie de tabla
        const footerPaid = document.getElementById('footerTotalPaid');
        if (footerPaid) footerPaid.textContent = formatCurrency(totalPaid);
        const footerCurrentValue = document.getElementById('footerTotalCurrentValue');
        if (footerCurrentValue) footerCurrentValue.textContent = formatCurrency(totalCurrentValue);
        const footerGainLoss = document.getElementById('footerTotalGainLoss');
        if (footerGainLoss) footerGainLoss.textContent = formatCurrency(totalGainLoss);
        const footerGainLossPercent = document.getElementById('footerTotalGainLossPercent');
        if (footerGainLossPercent) footerGainLossPercent.innerHTML = formatPercent(totalGainLossPercent);
    }
    
    async saveColumnPreferences() {
        const form = document.getElementById('portfolioColumnConfigForm');
        if (!form) return;
        this.state.columnPrefs.visible = Array.from(form.querySelectorAll('input:checked')).map(i => i.value);
        await fetch('/api/portfolio/columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns: this.state.columnPrefs.visible })
        });
        bootstrap.Modal.getInstance(document.getElementById('portfolioColumnConfigModal')).hide();
        this.render(this.state.priceMap); // Re-renderizar con las nuevas columnas
    }

    async handleAdd(event) {
        event.preventDefault();
        const form = event.target;
        const symbol = form.querySelector('#portfolioSymbol').value.toUpperCase();
        const quantity = form.querySelector('#portfolioQuantity').value;
        const price = form.querySelector('#portfolioPrice').value;

        try {
            const response = await fetch('/api/portfolio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, quantity, purchase_price: price })
            });
            if (!response.ok) throw new Error('Error al añadir al portafolio');
            form.reset();
            await this.loadHoldings();
            this.render(this.app.state.stockPriceMap); // Re-renderizar
        } catch (error) {
            console.error('Error en handleAdd de portafolio:', error);
        }
    }

    async handleDelete(id) {
        if (!confirm('¿Estás seguro de que quieres eliminar este activo del portafolio?')) return;
        try {
            const response = await fetch(`/api/portfolio/${id}`, { method: 'DELETE' });
            if (!response.ok) throw new Error('Error al eliminar del portafolio');
            await this.loadHoldings();
            this.render(this.app.state.stockPriceMap); // Re-renderizar
        } catch (error) {
            console.error('Error en handleDelete de portafolio:', error);
        }
    }
}