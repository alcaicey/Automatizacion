// src/static/app.js

$(document).ready(function() {
    // --- 1. ESTADO DE LA APLICACIÓN ---
    let isUpdating = false;
    let isFirstRun = true;
    let dataTable = null;
    let autoUpdateTimer = null;
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
        countdownTimer: document.getElementById('countdownTimer'),
        lastUpdate: document.getElementById('lastUpdate')
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

    function renderTable(stocks, timestamp, source) {
        if (dataTable) {
            dataTable.destroy();
            $(dom.stocksTable).empty();
        }

        if (!stocks || stocks.length === 0) {
            updateStatus('No hay datos para mostrar con el filtro actual.', 'warning');
            return;
        }

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
    }

    // --- 4. LÓGICA DE DATOS Y PREFERENCIAS ---

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
        // --- INICIO DE CORRECCIÓN: Se elimina la condición 'isFirstRun' ---
        if (!intervalValue || intervalValue === 'off') {
            return;
        }
        // --- FIN DE CORRECCIÓN ---

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
            // --- INICIO DE CORRECCIÓN: Inicia el ciclo inmediatamente si es posible ---
            // Si el bot ya está listo, inicia la actualización.
            // Si no, se iniciará cuando llegue el evento 'initial_session_ready'.
            if (!isFirstRun) {
                handleUpdateClick(true);
            }
            // --- FIN DE CORRECCIÓN ---
        }
    }

    // --- 6. INICIALIZACIÓN Y WEBSOCKETS ---
    async function initializeApp() {
        updateStatus('Inicializando...', 'info');
        updateRefreshButtonState();
        await loadPreferences();
        await fetchAndDisplayStocks();
        
        const savedInterval = sessionStorage.getItem('autoUpdateInterval');
        if (savedInterval) {
            dom.autoUpdateSelect.value = savedInterval;
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
            // --- INICIO DE CORRECCIÓN: Activa el ciclo si hay un intervalo seleccionado ---
            if (dom.autoUpdateSelect.value !== 'off') {
                 handleUpdateClick(true);
            }
            // --- FIN DE CORRECCIÓN ---
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
            isFirstRun = false;
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