// src/static/portfolioManager.js

const portfolioManager = {
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

    init() {
        console.log('[Portfolio] Módulo inicializado y en espera.');
        this.loadPortfolioColumnPreferences(); // Cargar preferencias al inicio
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

    render(stockPriceMap) {
        this.state.priceMap = stockPriceMap;
        const table = document.getElementById('portfolioTable');
        if (!table) return;

        // 1. Reconstruir el encabezado dinámicamente
        const thead = table.querySelector('thead');
        if (thead) {
            thead.innerHTML = `<tr>
                ${this.state.columnPrefs.visible.map(colId => {
                    const colDef = this.state.columnPrefs.all.find(c => c.id === colId);
                    return `<th>${colDef ? colDef.title : colId}</th>`;
                }).join('')}
            </tr>`;
        }

        // 2. Renderizar el cuerpo
        const tableBody = table.querySelector('tbody');
        if (!tableBody) return;

        let totalPaid = 0;
        let totalCurrentValue = 0;

        tableBody.innerHTML = this.state.holdings.map(h => {
            const stockData = this.state.priceMap.get(h.symbol) || {};
            const data = {
                symbol: h.symbol,
                quantity: h.quantity,
                purchase_price: h.purchase_price,
                total_paid: h.quantity * h.purchase_price,
                current_price: stockData.PRECIO_CIERRE || 0,
                daily_variation_percent: stockData.VARIACION || 0,
                current_value: h.quantity * (stockData.PRECIO_CIERRE || 0),
                get gain_loss_total() { return this.current_value - this.total_paid; },
                get gain_loss_percent() { return this.total_paid > 0 ? (this.gain_loss_total / this.total_paid) * 100 : 0; },
                actions: `<button class="btn btn-sm btn-danger delete-holding-btn" data-id="${h.id}"><i class="fas fa-trash"></i></button>`
            };
            
            totalPaid += data.total_paid;
            totalCurrentValue += data.current_value;

            return `<tr>
                ${this.state.columnPrefs.visible.map(colId => {
                    let cellContent = data[colId];
                    let cellClass = '';

                    if (['purchase_price', 'total_paid', 'current_price', 'current_value', 'gain_loss_total'].includes(colId)) {
                        cellContent = uiManager.createNumberRenderer() (cellContent, 'display');
                    } else if (['daily_variation_percent', 'gain_loss_percent'].includes(colId)) {
                        cellContent = uiManager.createNumberRenderer(true) (cellContent, 'display');
                    }

                    if (colId === 'gain_loss_total' || colId === 'gain_loss_percent') {
                        cellClass = data[colId] >= 0 ? 'text-success' : 'text-danger';
                    }
                    
                    return `<td class="${cellClass} fw-bold">${cellContent}</td>`;
                }).join('')}
            </tr>`;
        }).join('');
        
        this.updateTotals(totalPaid, totalCurrentValue);
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
            this.render(window.app.state.stockPriceMap); // Re-renderizar
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
            this.render(window.app.state.stockPriceMap); // Re-renderizar
        } catch (error) {
            console.error('Error en handleDelete de portafolio:', error);
        }
    },
};