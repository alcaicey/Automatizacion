// src/static/js/portfolioManager.js

window.portfolioManager = {
    holdings: [],
    dom: {},

    init() {
        this.dom = {
            tableBody: document.getElementById('portfolioTableBody'),
            form: document.getElementById('portfolioForm'),
            totalPaid: document.getElementById('totalPaid'),
            totalCurrentValue: document.getElementById('totalCurrentValue'),
            totalGainLoss: document.getElementById('totalGainLoss'),
            totalGainLossPercent: document.getElementById('totalGainLossPercent'),
        };
        this.loadHoldings();
        console.log('[Portfolio] Módulo inicializado.');
    },

    async loadHoldings() {
        try {
            const response = await fetch('/api/portfolio');
            if (!response.ok) throw new Error('Error al cargar el portafolio');
            this.holdings = await response.json();
            // No renderizamos aquí, esperamos a que el orquestador nos dé los precios
        } catch (error) {
            console.error(error);
        }
    },

    formatColoredNumber(number, isCurrency = false) {
        if (isNaN(number) || number === null) return 'N/A';
        const options = isCurrency ? { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 } : {minimumFractionDigits: 2, maximumFractionDigits: 2};
        const colorClass = number > 0 ? 'text-success' : (number < 0 ? 'text-danger' : 'text-muted');
        return `<span class="fw-bold ${colorClass}">${number.toLocaleString('es-CL', options)}</span>`;
    },

    render(stockPriceMap) {
        console.log('[Portfolio] Renderizando tabla de portafolio.');
        this.dom.tableBody.innerHTML = '';
        
        let totalPaid = 0;
        let totalCurrentValue = 0;

        if (this.holdings.length === 0) {
            this.dom.tableBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">Aún no has añadido acciones a tu portafolio.</td></tr>';
            $(this.dom.totalPaid).add(this.dom.totalCurrentValue).add(this.dom.totalGainLoss).add(this.dom.totalGainLossPercent).html('');
            return;
        }

        this.holdings.forEach(holding => {
            const priceData = stockPriceMap.get(holding.symbol);
            const currentPrice = priceData ? parseFloat(String(priceData.PRECIO_CIERRE).replace(',', '.')) : null;

            const holdingTotalPaid = holding.quantity * holding.purchase_price;
            const holdingCurrentValue = (currentPrice !== null && !isNaN(currentPrice)) ? holding.quantity * currentPrice : null;
            const holdingGainLoss = (holdingCurrentValue !== null) ? holdingCurrentValue - holdingTotalPaid : null;
            const holdingGainLossPercent = (holdingGainLoss !== null && holdingTotalPaid > 0) ? (holdingGainLoss / holdingTotalPaid) * 100 : null;

            totalPaid += holdingTotalPaid;
            if (holdingCurrentValue !== null) {
                totalCurrentValue += holdingCurrentValue;
            }

            const row = `
                <tr>
                    <td><strong>${holding.symbol}</strong></td>
                    <td>${holding.quantity.toLocaleString('es-CL')}</td>
                    <td>${holding.purchase_price.toLocaleString('es-CL', {style:'currency', currency:'CLP'})}</td>
                    <td>${holdingTotalPaid.toLocaleString('es-CL', {style:'currency', currency:'CLP'})}</td>
                    <td>${(currentPrice !== null && !isNaN(currentPrice)) ? currentPrice.toLocaleString('es-CL', {style:'currency', currency:'CLP'}) : '<em>Esperando...</em>'}</td>
                    <td>${(holdingCurrentValue !== null) ? this.formatColoredNumber(holdingCurrentValue, true) : 'N/A'}</td>
                    <td>${(holdingGainLoss !== null) ? this.formatColoredNumber(holdingGainLoss, true) : 'N/A'}</td>
                    <td>${(holdingGainLossPercent !== null) ? this.formatColoredNumber(holdingGainLossPercent) + '%' : 'N/A'}</td>
                    <td><button class="btn btn-danger btn-sm delete-holding-btn" data-id="${holding.id}"><i class="fas fa-trash"></i></button></td>
                </tr>`;
            this.dom.tableBody.innerHTML += row;
        });

        const totalGainLoss = totalCurrentValue - totalPaid;
        const totalGainLossPercent = (totalPaid > 0) ? (totalGainLoss / totalPaid) * 100 : 0;
        
        $(this.dom.totalPaid).html(`<strong>${totalPaid.toLocaleString('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 })}</strong>`);
        $(this.dom.totalCurrentValue).html(`<strong>${this.formatColoredNumber(totalCurrentValue, true)}</strong>`);
        $(this.dom.totalGainLoss).html(`<strong>${this.formatColoredNumber(totalGainLoss, true)}</strong>`);
        $(this.dom.totalGainLossPercent).html(`<strong>${this.formatColoredNumber(totalGainLossPercent) + '%'}</strong>`);
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
            // Le pedimos al orquestador que vuelva a renderizar con los precios actuales
            window.app.renderAllTables();
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
            } catch (error) {
                alert(`Error al eliminar: ${error.message}`);
            }
        }
    }
};