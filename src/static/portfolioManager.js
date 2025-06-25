// src/static/js/portfolioManager.js

window.portfolioManager = {
    holdings: [],
    dom: {},
    columnPrefs: { // <-- AÑADIDO
        all: [],
        visible: [],
    },
    columnConfig: { // <-- AÑADIDO
        'symbol': { title: 'Símbolo' },
        'quantity': { title: 'Cantidad', render: (d) => d.toLocaleString('es-CL') },
        'purchase_price': { title: 'P. Compra', render: (d) => d.toLocaleString('es-CL', {style:'currency', currency:'CLP'}) },
        'total_paid': { title: 'Pagado Total', render: (d) => d.toLocaleString('es-CL', {style:'currency', currency:'CLP'}) },
        'current_price': { title: 'P. Actual', render: (d) => (d !== null && !isNaN(d)) ? d.toLocaleString('es-CL', {style:'currency', currency:'CLP'}) : '<em>Esperando...</em>' },
        'daily_variation_percent': { title: 'Var. % Día', render: (d) => (d !== null && !isNaN(d)) ? portfolioManager.formatColoredNumber(d, { isPercent: true }) : 'N/A' },
        'current_value': { title: 'Valor Actual', render: (d) => (d !== null) ? portfolioManager.formatColoredNumber(d, { isCurrency: true }) : 'N/A' },
        'gain_loss_total': { title: 'Gan/Pérd Total', render: (d) => (d !== null) ? portfolioManager.formatColoredNumber(d, { isCurrency: true }) : 'N/A' },
        'gain_loss_percent': { title: 'Gan/Pérd %', render: (d) => (d !== null) ? portfolioManager.formatColoredNumber(d, { isPercent: true }) : 'N/A' },
        'actions': { title: 'Acciones', render: (d, t, r) => `<button class="btn btn-danger btn-sm delete-holding-btn" data-id="${r.id}"><i class="fas fa-trash"></i></button>` }
    },

    init() {
        this.dom = {
            table: document.getElementById('portfolioTable'), // <-- AÑADIDO
            tableBody: document.getElementById('portfolioTableBody'),
            form: document.getElementById('portfolioForm'),
            totalPaid: document.getElementById('totalPaid'),
            totalCurrentValue: document.getElementById('totalCurrentValue'),
            totalGainLoss: document.getElementById('totalGainLoss'),
            footerTotalPaid: document.getElementById('footerTotalPaid'),
            footerTotalCurrentValue: document.getElementById('footerTotalCurrentValue'),
            footerTotalGainLoss: document.getElementById('footerTotalGainLoss'),
            footerTotalGainLossPercent: document.getElementById('footerTotalGainLossPercent'),
            columnBtn: document.getElementById('portfolioColumnBtn'), // <-- AÑADIDO
            columnModal: new bootstrap.Modal(document.getElementById('portfolioColumnConfigModal')), // <-- AÑADIDO
            columnForm: document.getElementById('portfolioColumnConfigForm'), // <-- AÑADIDO
            saveColumnPrefsBtn: document.getElementById('savePortfolioColumnPrefs'), // <-- AÑADIDO
        };
        console.log('[Portfolio] Módulo inicializado.');
        this.attachEventListeners();
    },
    
    // --- INICIO DE NUEVAS FUNCIONES ---
    attachEventListeners() {
        if (this.dom.saveColumnPrefsBtn) {
            this.dom.saveColumnPrefsBtn.addEventListener('click', () => this.handleSavePrefs());
        }
    },
    
    async loadPreferences() {
        try {
            const res = await fetch('/api/portfolio/columns');
            if (!res.ok) throw new Error('No se pudieron cargar las preferencias de columnas del portafolio.');
            const data = await res.json();
            this.columnPrefs.all = data.all_columns;
            this.columnPrefs.visible = data.visible_columns;
            this.renderColumnModal();
        } catch (error) {
            console.error(error);
        }
    },

    renderColumnModal() {
        this.dom.columnForm.innerHTML = '';
        this.columnPrefs.all.forEach(colKey => {
            const isChecked = this.columnPrefs.visible.includes(colKey);
            const label = this.columnConfig[colKey]?.title || colKey.replace(/_/g, ' ');
            this.dom.columnForm.innerHTML += `
                <div class="col-6"><div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${colKey}" id="port-col-${colKey}" ${isChecked ? 'checked' : ''}>
                    <label class="form-check-label" for="port-col-${colKey}">${label}</label>
                </div></div>`;
        });
    },

    async handleSavePrefs() {
        const selected = Array.from(this.dom.columnForm.querySelectorAll('input:checked')).map(i => i.value);
        this.columnPrefs.visible = selected;
        
        await fetch('/api/portfolio/columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns: selected })
        });

        this.dom.columnModal.hide();
        window.app.renderAllTables(); // Llama a renderizar de nuevo
    },
    // --- FIN DE NUEVAS FUNCIONES ---

    async loadHoldings() {
        try {
            const response = await fetch('/api/portfolio');
            if (!response.ok) throw new Error('Error al cargar el portafolio');
            this.holdings = await response.json();
            await this.loadPreferences(); // Cargar preferencias después de los holdings
        } catch (error) {
            console.error(error);
        }
    },

    formatColoredNumber(number, options = {}) {
        const { isCurrency = false, isPercent = false } = options;
        if (isNaN(number) || number === null) return '--';
        
        const currencyOptions = { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 };
        const percentOptions = { minimumFractionDigits: 2, maximumFractionDigits: 2 };
        const regularOptions = {minimumFractionDigits: 2, maximumFractionDigits: 2};

        let displayOptions = regularOptions;
        if (isCurrency) displayOptions = currencyOptions;
        if (isPercent) displayOptions = percentOptions;

        const colorClass = number > 0 ? 'text-success' : (number < 0 ? 'text-danger' : 'text-muted');
        let formattedNumber = number.toLocaleString('es-CL', displayOptions);

        if (isPercent) {
            return `<span class="fw-bold ${colorClass}">${formattedNumber}%</span>`;
        }
        return `<span class="fw-bold ${colorClass}">${formattedNumber}</span>`;
    },

    render(stockPriceMap) {
        if (!this.dom.tableBody) return;

        // Renderizar encabezado de la tabla dinámicamente
        let headerHtml = '<tr>';
        this.columnPrefs.visible.forEach(colKey => {
            headerHtml += `<th>${this.columnConfig[colKey]?.title || colKey}</th>`;
        });
        headerHtml += '</tr>';
        this.dom.table.querySelector('thead').innerHTML = headerHtml;

        this.dom.tableBody.innerHTML = '';
        
        let portfolioTotalPaid = 0;
        let portfolioTotalCurrentValue = 0;

        if (this.holdings.length === 0) {
            this.dom.tableBody.innerHTML = `<tr><td colspan="${this.columnPrefs.visible.length}" class="text-center text-muted">Aún no has añadido acciones a tu portafolio.</td></tr>`;
            $(this.dom.totalPaid).add(this.dom.totalCurrentValue).add(this.dom.totalGainLoss).html('--');
            $(this.dom.footerTotalPaid).add(this.dom.footerTotalCurrentValue).add(this.dom.footerTotalGainLoss).add(this.dom.footerTotalGainLossPercent).html('');
            return;
        }

        this.holdings.forEach(holding => {
            const priceData = stockPriceMap.get(holding.symbol);
            const currentPrice = priceData ? parseFloat(String(priceData.PRECIO_CIERRE).replace(',', '.')) : null;
            const dailyVariation = priceData ? parseFloat(String(priceData.VARIACION).replace(',', '.')) : null;
            const holdingTotalPaid = holding.quantity * holding.purchase_price;
            const holdingCurrentValue = (currentPrice !== null && !isNaN(currentPrice)) ? holding.quantity * currentPrice : null;
            const holdingGainLoss = (holdingCurrentValue !== null) ? holdingCurrentValue - holdingTotalPaid : null;
            const holdingGainLossPercent = (holdingGainLoss !== null && holdingTotalPaid > 0) ? (holdingGainLoss / holdingTotalPaid) * 100 : null;
            
            portfolioTotalPaid += holdingTotalPaid;
            if (holdingCurrentValue !== null) {
                portfolioTotalCurrentValue += holdingCurrentValue;
            }

            const rowData = {
                id: holding.id,
                symbol: `<strong>${holding.symbol}</strong>`,
                quantity: holding.quantity,
                purchase_price: holding.purchase_price,
                total_paid: holdingTotalPaid,
                current_price: currentPrice,
                daily_variation_percent: dailyVariation,
                current_value: holdingCurrentValue,
                gain_loss_total: holdingGainLoss,
                gain_loss_percent: holdingGainLossPercent,
                actions: '' // El renderizador se encargará del botón
            };

            let rowHtml = '<tr>';
            this.columnPrefs.visible.forEach(colKey => {
                const renderer = this.columnConfig[colKey]?.render;
                const value = renderer ? renderer(rowData[colKey], 'display', rowData) : rowData[colKey];
                rowHtml += `<td>${value}</td>`;
            });
            rowHtml += '</tr>';
            this.dom.tableBody.innerHTML += rowHtml;
        });

        const totalGainLoss = portfolioTotalCurrentValue - portfolioTotalPaid;
        const totalGainLossPercent = (portfolioTotalPaid > 0) ? (totalGainLoss / portfolioTotalPaid) * 100 : 0;
        
        $(this.dom.totalPaid).html(`<strong>${portfolioTotalPaid.toLocaleString('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 })}</strong>`);
        $(this.dom.totalCurrentValue).html(`<strong>${this.formatColoredNumber(portfolioTotalCurrentValue, { isCurrency: true })}</strong>`);
        $(this.dom.totalGainLoss).html(`<strong>${this.formatColoredNumber(totalGainLoss, { isCurrency: true })}</strong>`);
        
        $(this.dom.footerTotalPaid).html(`<strong>${portfolioTotalPaid.toLocaleString('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 })}</strong>`);
        $(this.dom.footerTotalCurrentValue).html(`<strong>${this.formatColoredNumber(portfolioTotalCurrentValue, { isCurrency: true })}</strong>`);
        $(this.dom.footerTotalGainLoss).html(`<strong>${this.formatColoredNumber(totalGainLoss, { isCurrency: true })}</strong>`);
        $(this.dom.footerTotalGainLossPercent).html(`<strong>${this.formatColoredNumber(totalGainLossPercent, { isPercent: true })}</strong>`);
    },
    
    async handleAdd(event) {
        event.preventDefault();
        const symbol = $('#portfolioSymbol').val().trim().toUpperCase();
        const quantity = $('#portfolioQuantity').val();
        const price = $('#portfolioPrice').val();
        if (!symbol || !quantity || !price) {
            alert('Todos los campos son obligatorios.');
            return;
        }

        try {
            const response = await fetch('/api/portfolio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, quantity: parseFloat(quantity), purchase_price: parseFloat(price) })
            });
            if (!response.ok) throw new Error((await response.json()).error);
            this.dom.form.reset();
            await this.loadHoldings();
            window.app.renderAllTables();
            
            if (window.closingManager && typeof window.closingManager.loadClosings === 'function') {
                console.log('[Portfolio] Refrescando tabla de Cierre Bursátil tras añadir activo.');
                window.closingManager.loadClosings();
            }
        } catch (error) {
            alert(`Error al añadir: ${error.message}`);
        }
    },

    async handleDelete(holdingId) {
        if (confirm('¿Eliminar esta acción del portafolio?')) {
            try {
                const response = await fetch(`/api/portfolio/${holdingId}`, { method: 'DELETE' });
                if (!response.ok) throw new Error('No se pudo eliminar.');
                await this.loadHoldings();
                window.app.renderAllTables();

                if (window.closingManager && typeof window.closingManager.loadClosings === 'function') {
                    console.log('[Portfolio] Refrescando tabla de Cierre Bursátil tras eliminar activo.');
                    window.closingManager.loadClosings();
                }

            } catch (error) {
                alert(`Error al eliminar: ${error.message}`);
            }
        }
    }
};