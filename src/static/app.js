// src/static/app.js

$(document).ready(function() {
    // --- 1. ESTADO DE LA APLICACIÓN ---
    let isUpdating = false;
    let isFirstRun = true;
    let dataTable = null;
    let autoUpdateTimer = null;
    let stockFilters = { codes: [], all: true };
    let portfolioHoldings = [];
    let stockPriceMap = new Map();

    // --- 2. REFERENCIAS A ELEMENTOS DEL DOM ---
    const dom = {
        statusMessage: document.getElementById('statusMessage'),
        loadingOverlay: document.getElementById('loadingOverlay'),
        loadingMessage: document.getElementById('loadingMessage'),
        refreshBtn: document.getElementById('refreshBtn'),
        stocksTable: document.getElementById('stocksTable'),
        stockFilterForm: document.getElementById('stockFilterForm'),
        columnConfigModal: document.getElementById('columnConfigModal'),
        columnConfigForm: document.getElementById('columnConfigForm'),
        saveColumnPrefsBtn: document.getElementById('saveColumnPrefs'),
        stockCodeInputs: document.querySelectorAll('.stock-code'),
        allStocksCheck: document.getElementById('allStocksCheck'),
        clearFilterBtn: document.getElementById('clearBtn'),
        autoUpdateSelect: document.getElementById('autoUpdateSelect'),
        countdownTimer: document.getElementById('countdownTimer'),
        lastUpdate: document.getElementById('lastUpdate'),
        portfolioForm: document.getElementById('portfolioForm'),
        portfolioTableBody: document.getElementById('portfolioTableBody')
    };

    // --- 2.5 LÓGICA DE PREFERENCIAS DE COLUMNAS ---
    let columnPreferences = {
        all: [],
        visible: [],
        config: {
            'NEMO': { title: 'Símbolo' },
            'PRECIO_CIERRE': { title: 'Precio', render: createNumberRenderer() },
            'VARIACION': { title: 'Var. %', render: createNumberRenderer(true) },
            'PRECIO_COMPRA': { title: 'P. Compra', render: createNumberRenderer() },
            'PRECIO_VENTA': { title: 'P. Venta', render: createNumberRenderer() },
            'MONTO': { title: 'Monto Transado', render: createNumberRenderer(false, 'es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }) },
            'UN_TRANSADAS': { title: 'Unidades', render: createNumberRenderer() },
            'MONEDA': { title: 'Moneda' },
            'ISIN': { title: 'ISIN' },
            'BONO_VERDE': { title: 'Bono Verde' },
            'timestamp': { title: 'Timestamp' }
        }
    };

    // --- 3. FUNCIONES DE UI ---
    function updateStatus(message, type = 'info') {
        if (!dom.statusMessage) return;
        const icons = { info: 'info-circle', success: 'check-circle', warning: 'exclamation-triangle', danger: 'x-circle' };
        const alertClass = `alert-${type}`;
        dom.statusMessage.innerHTML = `<i class="fas fa-${icons[type]} me-2"></i><span>${message}</span>`;
        dom.statusMessage.className = `alert ${alertClass} small py-2`;
    }
    function toggleLoading(show, message = 'Cargando...') {
        if (!dom.loadingOverlay || !dom.loadingMessage) return;
        dom.loadingMessage.textContent = message;
        dom.loadingOverlay.classList.toggle('d-none', !show);
    }

    function updateRefreshButtonState() {
        if (!dom.refreshBtn) return;
        if (isUpdating) {
            const text = isFirstRun ? 'Iniciando Navegador...' : 'Actualizando...';
            dom.refreshBtn.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${text}`;
            dom.refreshBtn.disabled = true;
        } else {
            const text = isFirstRun ? 'Iniciar Navegador' : 'Actualizar Ahora';
            dom.refreshBtn.innerHTML = `<i class="fas fa-sync-alt me-2"></i>${text}`;
            dom.refreshBtn.disabled = false;
        }
    }

    function renderColumnModal() {
        if (!dom.columnConfigForm) return;
        dom.columnConfigForm.innerHTML = '';
        columnPreferences.all.forEach(col => {
            const isChecked = columnPreferences.visible.includes(col);
            dom.columnConfigForm.innerHTML += `<div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" value="${col}" id="col-check-${col}" ${isChecked ? 'checked' : ''}><label class="form-check-label" for="col-check-${col}">${columnPreferences.config[col]?.title || col.replace(/_/g, ' ')}</label></div></div>`;
        });
    }

    function renderFilterInputs() {
        if (!dom.allStocksCheck || !dom.stockCodeInputs) return;
        dom.allStocksCheck.checked = stockFilters.all;
        dom.stockCodeInputs.forEach((input, index) => { input.value = stockFilters.codes[index] || ''; });
    }

    function formatColoredNumber(number, isCurrency = false) {
        if (isNaN(number) || number === null) return 'N/A';
        const options = isCurrency ? { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 } : {minimumFractionDigits: 2, maximumFractionDigits: 2};
        const colorClass = number > 0 ? 'text-success' : (number < 0 ? 'text-danger' : 'text-muted');
        return `<span class="fw-bold ${colorClass}">${number.toLocaleString('es-CL', options)}</span>`;
    }

    function renderPortfolioTable() {
        if (!dom.portfolioTableBody) return;
        dom.portfolioTableBody.innerHTML = '';

        if (portfolioHoldings.length === 0) {
            dom.portfolioTableBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">Aún no has añadido acciones a tu portafolio.</td></tr>';
            return;
        }

        portfolioHoldings.forEach(holding => {
            const currentPriceData = stockPriceMap.get(holding.symbol);
            let currentPrice = null;
            if(currentPriceData && currentPriceData.PRECIO_CIERRE !== undefined) {
                 currentPrice = parseFloat(String(currentPriceData.PRECIO_CIERRE).replace(",", "."));
            }
            
            const totalPaid = holding.quantity * holding.purchase_price;
            const currentValue = currentPrice !== null && !isNaN(currentPrice) ? holding.quantity * currentPrice : null;
            const gainLoss = currentValue !== null ? currentValue - totalPaid : null;
            let gainLossPercent = null;
            if (gainLoss !== null && totalPaid > 0) {
                gainLossPercent = (gainLoss / totalPaid) * 100;
            }

            const row = `
                <tr>
                    <td><strong>${holding.symbol}</strong></td>
                    <td>${holding.quantity.toLocaleString('es-CL')}</td>
                    <td>${holding.purchase_price.toLocaleString('es-CL', {style:'currency', currency:'CLP'})}</td>
                    <td>${totalPaid.toLocaleString('es-CL', {style:'currency', currency:'CLP'})}</td>
                    <td>${currentPrice !== null && !isNaN(currentPrice) ? currentPrice.toLocaleString('es-CL', {style:'currency', currency:'CLP'}) : '<em>Esperando datos...</em>'}</td>
                    <td>${currentValue !== null ? formatColoredNumber(currentValue, true) : 'N/A'}</td>
                    <td>${gainLoss !== null ? formatColoredNumber(gainLoss, true) : 'N/A'}</td>
                    <td>${gainLossPercent !== null ? formatColoredNumber(gainLossPercent) + '%' : 'N/A'}</td>
                    <td>
                        <button class="btn btn-danger btn-sm delete-holding-btn" data-id="${holding.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
            dom.portfolioTableBody.innerHTML += row;
        });
    }

    function renderTable(stocks, timestamp, source) {
        if (dataTable) {
            dataTable.destroy();
            $(dom.stocksTable).empty();
        }

        stockPriceMap.clear();
        if (!stocks || stocks.length === 0) {
            updateStatus('No hay datos para mostrar con el filtro actual.', 'warning');
            renderPortfolioTable();
            return;
        }
        
        stocks.forEach(stock => {
            stockPriceMap.set(stock.NEMO, stock);
        });

        const allHeadings = Object.keys(stocks[0]);
        let visibleHeadings = columnPreferences.visible.length > 0
            ? columnPreferences.visible.filter(h => allHeadings.includes(h))
            : allHeadings;

        if (visibleHeadings.length === 0) visibleHeadings = allHeadings;

        const dtColumns = visibleHeadings.map(key => ({
            data: key,
            title: columnPreferences.config[key]?.title || key.replace(/_/g, ' '),
            render: columnPreferences.config[key]?.render || null
        }));
        
        dataTable = $(dom.stocksTable).DataTable({
            data: stocks,
            columns: dtColumns,
            responsive: true,
            language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
            dom: 'Bfrtip',
            buttons: ['excelHtml5', 'csvHtml5'],
            order: []
        });

        updateStatus(`Mostrando ${stocks.length} acciones. Fuente: ${source}`, 'success');
        if (dom.lastUpdate) {
            dom.lastUpdate.innerHTML = `<i class="fas fa-clock me-1"></i>Última act: ${timestamp}`;
        }
        
        renderPortfolioTable();
    }

    // --- 4. LÓGICA DE DATOS Y PREFERENCIAS ---

    async function loadPortfolio() {
        try {
            const response = await fetch('/api/portfolio');
            if (!response.ok) throw new Error('Error al cargar el portafolio');
            portfolioHoldings = await response.json();
            renderPortfolioTable();
        } catch (error) {
            console.error(error);
            updateStatus('No se pudo cargar tu portafolio.', 'danger');
        }
    }

    async function loadPreferences() {
        try {
            const [colsRes, filtersRes] = await Promise.all([fetch('/api/columns'), fetch('/api/filters')]);
            if (!colsRes.ok || !filtersRes.ok) throw new Error('No se pudieron cargar las preferencias.');
            const colsData = await colsRes.json();
            const filtersData = await filtersRes.json();
            columnPreferences = {
                ...columnPreferences,
                all: colsData.all_columns,
                visible: colsData.visible_columns,
            };
            columnPreferences.visible = columnPreferences.visible.filter(c => columnPreferences.all.includes(c));
            if (columnPreferences.visible.length === 0) {
                columnPreferences.visible = ['NEMO', 'PRECIO_CIERRE', 'VARIACION'];
            }
            stockFilters = { codes: filtersData.codes, all: filtersData.all !== false };
            renderColumnModal();
            renderFilterInputs();
        } catch (error) {
            console.error(error);
            updateStatus('Error al cargar preferencias.', 'danger');
        }
    }

    async function fetchAndDisplayStocks() {
        const url = buildFilterUrl();
        try {
            const response = await fetch(url);
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Error del servidor');
            renderTable(result.data, result.timestamp, result.source);
        } catch (error) {
            console.error(error);
            updateStatus(`Error al cargar datos: ${error.message}`, 'danger');
        }
    }

    async function saveColumnPreferences() {
        const selectedColumns = Array.from(dom.columnConfigForm.querySelectorAll('input:checked')).map(input => input.value);
        try {
            await fetch('/api/columns', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ columns: selectedColumns })
            });
            columnPreferences.visible = selectedColumns;
            bootstrap.Modal.getInstance(dom.columnConfigModal)?.hide();
            await fetchAndDisplayStocks();
        } catch (error) {
            updateStatus('Error al guardar preferencias.', 'danger');
        }
    }

    async function saveFilterPreferences() {
        stockFilters.codes = Array.from(dom.stockCodeInputs).map(input => input.value.trim().toUpperCase()).filter(Boolean);
        stockFilters.all = dom.allStocksCheck.checked;
        try {
            await fetch('/api/filters', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(stockFilters)
            });
        } catch (error) { console.error('Error al guardar filtros:', error); }
    }

    // --- 5. LÓGICA DE CONTROL DEL BOT Y AUTO-UPDATE ---
    let countdownInterval = null;

    async function handleUpdateClick(isAutoUpdate = false) {
        if (isUpdating) return;
        isUpdating = true;
        if (!isAutoUpdate) stopAutoUpdate();
        updateRefreshButtonState();
        toggleLoading(true, isFirstRun ? 'Iniciando Navegador...' : 'Actualizando datos...');
        try {
            const response = await fetch('/api/stocks/update', { method: 'POST' });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'Fallo al iniciar el bot.');
            updateStatus(data.message, 'info');
        } catch (error) {
            updateStatus(`Error: ${error.message}`, 'danger');
            isUpdating = false;
            toggleLoading(false);
            updateRefreshButtonState();
            if (isAutoUpdate) scheduleNextUpdate();
        }
    }

    function buildFilterUrl() {
        if (stockFilters.all || !stockFilters.codes || stockFilters.codes.length === 0) return '/api/stocks';
        const queryParams = new URLSearchParams();
        stockFilters.codes.forEach(code => queryParams.append('code', code));
        return `/api/stocks?${queryParams.toString()}`;
    }

    async function handleFilterSubmit(event) {
        event.preventDefault();
        await saveFilterPreferences();
        await fetchAndDisplayStocks();
    }
    
    function startCountdown(totalSeconds) {
        if (countdownInterval) clearInterval(countdownInterval);
        let remaining = totalSeconds;
        
        const updateCountdown = () => {
            if (remaining <= 0) {
                clearInterval(countdownInterval);
                dom.countdownTimer.textContent = 'Actualizando...';
                return;
            }
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            dom.countdownTimer.textContent = `(Próxima en ${minutes}:${seconds < 10 ? '0' : ''}${seconds})`;
            remaining--;
        };

        updateCountdown();
        countdownInterval = setInterval(updateCountdown, 1000);
    }
    
    function stopAutoUpdate() {
        if (autoUpdateTimer) clearTimeout(autoUpdateTimer);
        if (countdownInterval) clearInterval(countdownInterval); countdownInterval = null;
        if (dom.countdownTimer) dom.countdownTimer.textContent = '';
        console.log('[AutoUpdater] Ciclo detenido.');
    }

    function scheduleNextUpdate() {
        const intervalValue = sessionStorage.getItem('autoUpdateInterval');
        if (!intervalValue || intervalValue === 'off') {
            return;
        }

        const [min, max] = intervalValue.split('-').map(Number);
        const randomSeconds = Math.floor(Math.random() * (max * 60 - min * 60 + 1)) + (min * 60);
        
        console.log(`[AutoUpdater] Próxima actualización programada en ${randomSeconds} segundos.`);
        startCountdown(randomSeconds);

        autoUpdateTimer = setTimeout(() => {
            console.log('[AutoUpdater] Disparando actualización automática.');
            if (!isUpdating) handleUpdateClick(true);
        }, randomSeconds * 1000);
    }
    
    function handleAutoUpdateChange() {
        const intervalValue = dom.autoUpdateSelect.value;
        sessionStorage.setItem('autoUpdateInterval', intervalValue);
        if (intervalValue === "off") {
            stopAutoUpdate();
            updateStatus('Auto-Update desactivado.', 'info');
        } else {
            if (!isFirstRun) {
                handleUpdateClick(true);
            }
        }
    }

    // --- 6. INICIALIZACIÓN Y WEBSOCKETS ---
    async function initializeApp() {
        updateStatus('Inicializando...', 'info');
        updateRefreshButtonState();
        await Promise.all([loadPreferences(), loadPortfolio()]);
        await fetchAndDisplayStocks();
        
        const savedInterval = sessionStorage.getItem('autoUpdateInterval');
        if (savedInterval) {
            dom.autoUpdateSelect.value = savedInterval;
            if (savedInterval !== 'off') {
                console.log('[Init] Intervalo de auto-update detectado en sesión. Reactivando ciclo...');
                handleAutoUpdateChange();
            }
        }
    }

    function setupWebSocket() {
        const socket = io();
        socket.on('connect', () => updateStatus('Conectado al servidor.', 'success'));
        socket.on('disconnect', () => updateStatus('Desconectado.', 'danger'));

        socket.on('initial_session_ready', () => {
            isUpdating = false;
            isFirstRun = false;
            toggleLoading(false);
            updateRefreshButtonState();
            updateStatus("Navegador listo. Presione 'Actualizar Ahora' para capturar datos.", 'success');
            
            if (dom.autoUpdateSelect.value !== 'off') {
                 console.log('[AutoUpdater] El backend está listo, iniciando el primer ciclo de auto-actualización.');
                 handleUpdateClick(true);
            }
        });
        
        socket.on('new_data', async () => {
            isUpdating = false;
            toggleLoading(false);
            updateRefreshButtonState();
            updateStatus("¡Datos recibidos! Actualizando tabla...", 'success');
            await fetchAndDisplayStocks();
            scheduleNextUpdate(); 
        });

        socket.on('bot_error', (data) => {
            isUpdating = false;
            toggleLoading(false);
            updateRefreshButtonState();
            updateStatus(`Error del bot: ${data.message}`, 'danger');
            scheduleNextUpdate();
        });
    }

    // --- 7. ASIGNACIÓN DE EVENT LISTENERS ---
    function attachEventListeners() {
        $(dom.refreshBtn).on('click', () => handleUpdateClick(false));
        $(dom.stockFilterForm).on('submit', handleFilterSubmit);
        $(dom.saveColumnPrefsBtn).on('click', saveColumnPreferences);
        $(dom.autoUpdateSelect).on('change', handleAutoUpdateChange);
        $(dom.clearFilterBtn).on('click', async () => {
            dom.stockFilterForm.reset();
            dom.allStocksCheck.checked = true;
            const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
            dom.stockFilterForm.dispatchEvent(submitEvent);
        });

        $(dom.portfolioForm).on('submit', async (e) => {
            e.preventDefault();
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

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Error del servidor');
                }

                dom.portfolioForm.reset();
                await loadPortfolio();

            } catch (error) {
                alert(`Error al añadir la acción: ${error.message}`);
            }
        });
        
        $(dom.portfolioTableBody).on('click', '.delete-holding-btn', async function() {
            const holdingId = $(this).data('id');
            if (confirm(`¿Estás seguro de que quieres eliminar esta acción de tu portafolio?`)) {
                try {
                    const response = await fetch(`/api/portfolio/${holdingId}`, { method: 'DELETE' });
                    if (!response.ok) throw new Error('No se pudo eliminar el registro.');
                    await loadPortfolio();
                } catch (error) {
                    alert(`Error: ${error.message}`);
                }
            }
        });
    }

    // --- Helper para renderizar números ---
    function createNumberRenderer(isPercent = false, locale = 'es-CL', options = {}) {
        return function(data, type, row) {
            if (type === 'display') {
                if (data === null || data === undefined || data === '') return 'N/A';
                const number = parseFloat(String(data).replace(",", "."));
                if (isNaN(number)) return data;
    
                const colorClass = number > 0 ? 'text-success' : (number < 0 ? 'text-danger' : '');
                let formattedNumber = number.toLocaleString(locale, options);
                if (isPercent) formattedNumber += '%';
                
                return `<span class="fw-bold ${colorClass}">${formattedNumber}</span>`;
            }
            return data;
        };
    }

    initializeApp();
    setupWebSocket();
    attachEventListeners();
});