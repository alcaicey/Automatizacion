// src/static/app.js

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. ESTADO DE LA APLICACIÓN ---
    let isUpdating = false;
    let isFirstRun = true;
    let dataTable = null;
    let autoUpdateTimer = null;
    let countdownInterval = null;
    let columnPreferences = { all: [], visible: [] };
    let stockFilters = { codes: [], all: true };

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
        countdownTimer: document.getElementById('countdownTimer')
    };

    // --- 3. FUNCIONES DE UI ---
    function updateStatus(message, type = 'info') {
        if (countdownInterval) {
            clearInterval(countdownInterval);
            countdownInterval = null;
            if (dom.countdownTimer) dom.countdownTimer.textContent = '';
        }
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
            dom.columnConfigForm.innerHTML += `<div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" value="${col}" id="col-check-${col}" ${isChecked ? 'checked' : ''}><label class="form-check-label" for="col-check-${col}">${col.replace(/_/g, ' ')}</label></div></div>`;
        });
    }

    function renderFilterInputs() {
        if (!dom.allStocksCheck || !dom.stockCodeInputs) return;
        dom.allStocksCheck.checked = stockFilters.all;
        dom.stockCodeInputs.forEach((input, index) => { input.value = stockFilters.codes[index] || ''; });
    }

    function renderTable(stocks, timestamp) {
        if (!dom.stocksTable) return;
        if (dataTable) dataTable.destroy();
        
        const tableContainer = dom.stocksTable.parentElement;
        tableContainer.innerHTML = '<table id="stocksTable" class="table table-striped table-hover"></table>';
        dom.stocksTable = document.getElementById('stocksTable');

        if (!stocks || stocks.length === 0) {
            updateStatus('No hay datos para mostrar con el filtro actual.', 'warning');
            return;
        }

        const headings = Object.keys(stocks[0]);
        let visibleHeadings = columnPreferences.visible.filter(h => headings.includes(h));
        if (visibleHeadings.length === 0) visibleHeadings = headings;

        const tableData = stocks.map(stock =>
            visibleHeadings.map(header => {
                const value = stock[header];
                if (typeof value === 'number') return value.toLocaleString('es-CL');
                return value !== undefined && value !== null ? value : 'N/A';
            })
        );
        
        dataTable = new simpleDatatables.DataTable(dom.stocksTable, {
            data: { headings: visibleHeadings.map(h => h.replace(/_/g, ' ')), data: tableData },
            perPage: 50, perPageSelect: [25, 50, 100],
            searchable: true, sortable: true, fixedHeight: true,
        });
        updateStatus(`Mostrando ${stocks.length} acciones. Última actualización: ${timestamp}`, 'success');
    }

    // --- 4. LÓGICA DE DATOS Y PREFERENCIAS ---
    async function loadPreferences() {
        try {
            const [colsRes, filtersRes] = await Promise.all([fetch('/api/columns'), fetch('/api/filters')]);
            if (!colsRes.ok || !filtersRes.ok) throw new Error('No se pudieron cargar las preferencias.');
            const colsData = await colsRes.json();
            const filtersData = await filtersRes.json();
            columnPreferences = { all: colsData.all_columns, visible: colsData.visible_columns };
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
            renderTable(result.data, result.timestamp);
        } catch (error) {
            console.error(error);
            updateStatus(`Error al cargar datos: ${error.message}`, 'danger');
        }
    }

    async function saveColumnPreferences() {
        columnPreferences.visible = Array.from(dom.columnConfigForm.querySelectorAll('input:checked')).map(input => input.value);
        try {
            await fetch('/api/columns', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ columns: columnPreferences.visible })
            });
            bootstrap.Modal.getInstance(dom.columnConfigModal).hide();
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
    async function handleUpdateClick() {
        autoUpdater.stop(); 
        if (isUpdating) return;
        isUpdating = true;
        updateRefreshButtonState();
        toggleLoading(true, isFirstRun ? 'Iniciando navegador...' : 'Actualizando datos...');
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

    function handleAutoUpdateChange() {
        autoUpdater.start(
            dom.autoUpdateSelect.value, 
            () => dom.refreshBtn.click(),
            (text) => { if(dom.countdownTimer) dom.countdownTimer.textContent = text; }
        );
    }

    // --- 6. INICIALIZACIÓN Y WEBSOCKETS ---
    async function initializeApp() {
        updateStatus('Inicializando...', 'info');
        updateRefreshButtonState();
        await loadPreferences();
        await fetchAndDisplayStocks();
    }

    const socket = io();
    socket.on('connect', () => updateStatus('Conectado al servidor.', 'success'));
    socket.on('disconnect', () => {
        autoUpdater.stop();
        updateStatus('Desconectado.', 'danger');
    });

    socket.on('initial_session_ready', () => {
        isUpdating = false;
        isFirstRun = false;
        toggleLoading(false);
        updateRefreshButtonState();
        updateStatus("Navegador listo. Presione 'Actualizar Ahora' para capturar datos.", 'warning');
        handleAutoUpdateChange();
    });

    socket.on('new_data', () => {
        updateStatus("¡Datos recibidos! Actualizando la página...", 'success');
        setTimeout(() => location.reload(), 1500);
    });

    socket.on('bot_error', (data) => {
        isUpdating = false;
        isFirstRun = true; 
        toggleLoading(false);
        updateRefreshButtonState();
        updateStatus(`Error del bot: ${data.message}`, 'danger');
    });

    // --- 7. ASIGNACIÓN DE EVENT LISTENERS ---
    if (dom.refreshBtn) dom.refreshBtn.addEventListener('click', handleUpdateClick);
    if (dom.stockFilterForm) dom.stockFilterForm.addEventListener('submit', handleFilterSubmit);
    if (dom.saveColumnPrefsBtn) dom.saveColumnPrefsBtn.addEventListener('click', saveColumnPreferences);
    if (dom.autoUpdateSelect) dom.autoUpdateSelect.addEventListener('change', handleAutoUpdateChange);
    if (dom.clearFilterBtn) {
        dom.clearFilterBtn.addEventListener('click', async () => {
            if(dom.stockFilterForm) dom.stockFilterForm.reset();
            if(dom.allStocksCheck) dom.allStocksCheck.checked = true;
            await handleFilterSubmit(new Event('submit', { bubbles: true, cancelable: true }));
        });
    }
    
    initializeApp();
});