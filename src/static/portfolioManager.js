// src/static/portfolioManager.js

window.portfolioManager = {
    app: null,
    dataTable: null,
    state: {
        holdings: [],
        priceMap: new Map(),
        columnPrefs: {
            all: [
                { id: 'symbol', title: 'Símbolo' },
                { id: 'quantity', title: 'Cantidad' },
                { id: 'purchase_price', title: 'P. Compra' },
                { id: 'total_paid', title: 'Total Pagado' },
                { id: 'current_price', title: 'Precio Actual' },
                { id: 'daily_variation_percent', title: 'Var. % Día' },
                { id: 'current_value', title: 'Valor Actual' },
                { id: 'gain_loss_total', title: 'G/P ($)' },
                { id: 'gain_loss_percent', title: 'G/P (%)' },
                { id: 'actions', title: 'Acciones' }
            ],
            visible: ['symbol', 'quantity', 'purchase_price', 'current_price', 'gain_loss_total', 'gain_loss_percent', 'actions']
        }
    },

    init(appInstance) {
        this.app = appInstance;
        // No hacer nada aquí todavía. Esperar a que el widget esté listo.
        this.waitForWidget();
    },

    waitForWidget() {
        const checkInterval = setInterval(() => {
            if (document.getElementById('portfolioTable')) {
                clearInterval(checkInterval);
                console.log('[Portfolio] Widget de portafolio detectado en el DOM. Inicializando...');
                this.initialize();
            }
        }, 100); // Comprobar cada 100ms
    },

    initialize() {
        this.fetchPortfolioData();
        // Puedes añadir más lógica de inicialización aquí si es necesario
    },

    async fetchPortfolioData() {
        try {
            const response = await fetch('/api/portfolio/view');
            if (!response.ok) throw new Error('No se pudo cargar la vista del portafolio.');
            
            const result = await response.json();
            
            if(result.summary) {
                this.app.uiManager.updatePortfolioSummary(result.summary);
            }

            if(result.portfolio) {
                this.render(result.portfolio);
            }
            
        } catch (error) {
            console.error('[Portfolio] Error al cargar datos:', error);
            this.app.uiManager.updateStatus('Error al cargar portafolio.', 'danger');
        }
    },

    async loadHoldings() {
        try {
            const response = await fetch('/api/portfolio');
            if (!response.ok) throw new Error('Error al cargar portafolio');
            this.state.holdings = await response.json();
        } catch (error) {
            console.error('Error cargando holdings:', error);
        }
    },
    
    async loadPortfolioColumnPreferences() {
        try {
            const response = await fetch('/api/portfolio/columns');
            if (!response.ok) return;
            const data = await response.json();
            this.state.columnPrefs.visible = data.visible_columns;
            this.renderColumnModal(); // Renderizar el modal con los datos cargados
        } catch (error) {
            console.error('Error cargando preferencias de columnas del portafolio:', error);
        }
    },
    
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
    },

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
    },
    
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
    },

    render(data) {
        if (!this.app) return;

        const columns = [
            { data: 'symbol', title: 'Símbolo' },
            { data: 'quantity', title: 'Cantidad' },
            { data: 'purchase_price', title: 'Precio Compra', render: this.app.uiManager.createNumberRenderer() },
            { data: 'total_paid', title: 'Total Pagado', render: this.app.uiManager.createNumberRenderer() },
            { data: 'current_price', title: 'Precio Actual', render: this.app.uiManager.createNumberRenderer() },
            { data: 'current_value', title: 'Valor Actual', render: this.app.uiManager.createNumberRenderer() },
            { data: 'gain_loss_total', title: 'Ganancia/Pérdida', render: this.app.uiManager.createNumberRenderer() },
            { data: 'gain_loss_percent', title: '% Gan./Pérd.', render: this.app.uiManager.createNumberRenderer(true) },
            { data: 'actions', title: 'Acciones', orderable: false, defaultContent: '' }
        ];
        
        this.app.uiManager.renderTable('portfolioTable', data, columns);
    },

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
    },
    
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
    },

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
    },

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
    },
};