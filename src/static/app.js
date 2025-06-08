// Funcionalidad principal de la aplicación

// Variables globales
let autoUpdateTimer = null;
let lastStockCodes = [];
let nextUpdateTime = null;
let updateStatusInterval = null;
let isUpdating = false;
let nextUpdateCountdownInterval = null;

async function logErrorToServer(message, stack = '', action = '') {
    try {
        await fetch('/api/logs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, stack, action })
        });
    } catch (e) {
        console.error('Error enviando log al servidor:', e);
    }
}

window.addEventListener('error', (e) => {
    logErrorToServer(e.message || 'Error', e.error ? e.error.stack : '', 'global');
});

window.addEventListener('unhandledrejection', (e) => {
    const reason = e.reason || {};
    logErrorToServer(reason.message || String(reason), reason.stack, 'global');
});

// Elementos DOM
const stockFilterForm = document.getElementById('stockFilterForm');
const stockCodeInputs = document.querySelectorAll('.stock-code');
const autoUpdateSelect = document.getElementById('autoUpdateSelect');
const clearBtn = document.getElementById('clearBtn');
const refreshBtn = document.getElementById('refreshBtn');
const configColumnsBtn = document.getElementById('configColumnsBtn');
const columnConfigForm = document.getElementById('columnConfigForm');
const saveColumnPrefsBtn = document.getElementById('saveColumnPrefs');
const statusMessage = document.getElementById('statusMessage');
const lastUpdate = document.getElementById('lastUpdate');
let stocksTable = document.getElementById('stocksTable');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingMessage = document.getElementById('loadingMessage');
const nextUpdateInfo = document.getElementById('nextUpdateInfo');
const sessionCountdown = document.getElementById('sessionCountdown');
const allStocksCheck = document.getElementById('allStocksCheck');

let sessionCountdownInterval = null;
let visibleColumns = [];
let dataTable = null;

const ALL_COLUMNS = [
    { key: 'NEMO', label: 'Acción' },
    { key: 'ISIN', label: 'ISIN' },
    { key: 'PRECIO_CIERRE', label: 'Precio' },
    { key: 'VARIACION', label: '$% Var' },
    { key: 'PRECIO_COMPRA', label: 'Compra' },
    { key: 'PRECIO_VENTA', label: 'Venta' },
    { key: 'MONTO', label: 'Monto M$' },
    { key: 'MONEDA', label: 'Moneda' },
    { key: 'UN_TRANSADAS', label: 'Volumen' },
    { key: 'BONO_VERDE', label: 'Bono Verde' },
    { key: 'VALORES_EXTRANJEROS', label: 'Valores Extr.' },
];

// Función para mostrar/ocultar el overlay de carga
function toggleLoading(show, message = '') {
    if (show) {
        loadingOverlay.classList.remove('d-none');
        if (message) {
            loadingMessage.textContent = message;
        }
    } else {
        loadingOverlay.classList.add('d-none');
    }
}

// Función para actualizar el mensaje de estado
function updateStatus(message, isError = false) {
    statusMessage.innerHTML = `<i class="fas fa-${isError ? 'exclamation-circle text-danger' : 'info-circle'}"></i> <span>${message}</span>`;
}

// Función para actualizar la información de última actualización
function updateLastUpdateTime(timestamp) {
    if (timestamp) {
        lastUpdate.innerHTML = `<i class="fas fa-clock me-1"></i> <span>Última actualización: ${timestamp}</span>`;
    } else {
        lastUpdate.innerHTML = `<i class="fas fa-clock me-1"></i> <span>Última actualización: --</span>`;
    }
}

// Función para formatear valores numéricos
function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) {
        return '--';
    }
    return Number(value).toLocaleString('es-CL', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// Crear los checkboxes de configuración
function renderColumnConfig() {
    columnConfigForm.innerHTML = '';
    ALL_COLUMNS.forEach(col => {
        const div = document.createElement('div');
        div.className = 'form-check col-6';
        div.innerHTML = `
            <input class="form-check-input column-checkbox" type="checkbox" value="${col.key}" id="chk_${col.key}">
            <label class="form-check-label" for="chk_${col.key}">${col.label}</label>
        `;
        columnConfigForm.appendChild(div);
    });
}

async function loadColumnPreferences() {
    try {
        const resp = await fetch('/api/column-preferences');
        const data = await resp.json();
        if (data.columns) {
            visibleColumns = JSON.parse(data.columns);
        } else {
            visibleColumns = ALL_COLUMNS.map(c => c.key);
        }
    } catch (e) {
        visibleColumns = ALL_COLUMNS.map(c => c.key);
    }
    // Marcar checkboxes
    document.querySelectorAll('.column-checkbox').forEach(chk => {
        chk.checked = visibleColumns.includes(chk.value);
    });
}

async function saveColumnPreferences() {
    const cols = Array.from(document.querySelectorAll('.column-checkbox'))
        .filter(c => c.checked)
        .map(c => c.value);
    visibleColumns = cols;
    await fetch('/api/column-preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ columns: cols })
    });
    fetchAndDisplayStocks();
}

// Función para obtener y mostrar los datos de acciones
async function fetchAndDisplayStocks() {
    try {
        toggleLoading(true, 'Cargando datos de acciones...');

        const allStocks = allStocksCheck.checked;

        // Obtener códigos de acciones no vacíos
        let stockCodes = Array.from(stockCodeInputs)
            .map(input => input.value.trim())
            .filter(code => code !== '');
        if (allStocks) {
            stockCodes = [];
        }

        // Guardar los códigos para futuras actualizaciones
        lastStockCodes = [...stockCodes];

        // Construir la URL con los parámetros de consulta
        let url = '/api/stocks';
        if (stockCodes.length > 0) {
            url += '?' + stockCodes.map(code => `code=${encodeURIComponent(code)}`).join('&');
        }
        
        // Realizar la petición
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.error) {
            updateStatus(`Error: ${data.error}`, true);
            toggleLoading(false);
            return;
        }
        
        // Actualizar la tabla con los datos
        updateStocksTable(data);
        
        // Actualizar información de última actualización
        updateLastUpdateTime(data.timestamp);
        updateStatus(`Datos cargados correctamente. ${stockCodes.length > 0 ? `Mostrando ${data.count || 0} acción(es).` : 'Mostrando todas las acciones.'}`);
        fetchSessionTime();
        
    } catch (error) {
        console.error('Error al obtener datos:', error);
        updateStatus(`Error al obtener datos: ${error.message}`, true);
        logErrorToServer(error.message, error.stack, 'fetchAndDisplayStocks');
    } finally {
        toggleLoading(false);
    }
}

// Función para actualizar la tabla de acciones
function updateStocksTable(data) {
    if (dataTable) {
        dataTable.destroy();
        dataTable = null;
        // destroy() replaces the table element, so refresh the reference
        stocksTable = document.getElementById('stocksTable');
    }

    const thead = stocksTable.querySelector('thead tr');
    const tbody = stocksTable.querySelector('tbody');
    thead.innerHTML = '';
    tbody.innerHTML = '';

    const cols = visibleColumns.length ? visibleColumns : ALL_COLUMNS.map(c => c.key);
    cols.forEach(key => {
        const def = ALL_COLUMNS.find(c => c.key === key);
        const th = document.createElement('th');
        th.textContent = def ? def.label : key;
        thead.appendChild(th);
    });

    const stocks = data.data || [];
    if (stocks.length === 0) {
        const row = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = cols.length;
        td.className = 'text-center py-4';
        td.innerHTML = '<div class="text-muted">No hay datos disponibles</div>';
        row.appendChild(td);
        tbody.appendChild(row);
    } else {
        stocks.forEach(stock => {
            const row = document.createElement('tr');
            cols.forEach(key => {
                let html = '--';
                if (key === 'NEMO') {
                    html = `<strong>${stock.NEMO || '--'}</strong>`;
                } else if (key === 'PRECIO_CIERRE') {
                    html = formatNumber(stock.PRECIO_CIERRE || 0);
                } else if (key === 'VARIACION') {
                    const val = parseFloat(stock.VARIACION || 0);
                    const isPos = val > 0;
                    const isNeg = val < 0;
                    const cls = isPos ? 'variation-positive' : (isNeg ? 'variation-negative' : '');
                    const icon = isPos ? 'fa-arrow-up arrow-up' : (isNeg ? 'fa-arrow-down arrow-down' : '');
                    html = `<span class="${cls}">${icon ? `<i class="fas ${icon} me-1"></i>` : ''}${formatNumber(stock.VARIACION || 0)} (${formatNumber(val,2)}%)</span>`;
                } else if (key === 'PRECIO_COMPRA') {
                    html = formatNumber(stock.PRECIO_COMPRA || 0);
                } else if (key === 'PRECIO_VENTA') {
                    html = formatNumber(stock.PRECIO_VENTA || 0);
                } else if (key === 'MONTO') {
                    html = formatNumber(stock.MONTO || 0, 0);
                } else if (key === 'UN_TRANSADAS') {
                    html = formatNumber(stock.UN_TRANSADAS || 0, 0);
                } else {
                    html = stock[key] ?? '--';
                }
                const td = document.createElement('td');
                td.innerHTML = html;
                row.appendChild(td);
            });
            tbody.appendChild(row);
        });
    }

    dataTable = new simpleDatatables.DataTable(stocksTable, {
        searchable: true,
        fixedHeight: true,
        perPageSelect: false,
    });
}

// Función para actualizar manualmente los datos
async function updateStocksData() {
    if (isUpdating) {
        updateStatus('Ya hay una actualización en curso, por favor espere...', true);
        return;
    }
    
    try {
        isUpdating = true;
        toggleLoading(true, 'Ejecutando script de actualización de datos...');
        updateStatus('Iniciando proceso de actualización de datos...');
        
        // Iniciar la actualización
        const response = await fetch('/api/stocks/update', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (!data.success) {
            updateStatus(`Error al iniciar actualización: ${data.message}`, true);
            toggleLoading(false);
            isUpdating = false;
            return;
        }
        
        // Esperar un tiempo para que el script se ejecute (puede tardar hasta 20 segundos)
        updateStatus('Ejecutando script de actualización. Esto puede tardar hasta 20 segundos...');
        
        // Esperar 20 segundos antes de intentar obtener los datos actualizados
        setTimeout(async () => {
            try {
                await fetchAndDisplayStocks();
                updateStatus('Datos actualizados correctamente');
            } catch (error) {
                console.error('Error al actualizar datos:', error);
                updateStatus(`Error al actualizar datos: ${error.message}`, true);
                logErrorToServer(error.message, error.stack, 'updateStocksData');
                toggleLoading(false);
            } finally {
                isUpdating = false;
            }
        }, 20000);
        
    } catch (error) {
        console.error('Error al actualizar datos:', error);
        updateStatus(`Error al actualizar datos: ${error.message}`, true);
        toggleLoading(false);
        logErrorToServer(error.message, error.stack, 'updateStocksData');
        isUpdating = false;
    }
}

// Función para configurar la actualización automática
async function setAutoUpdate(mode) {
    try {
        // Detener el temporizador actual si existe
        if (autoUpdateTimer) {
            clearInterval(autoUpdateTimer);
            autoUpdateTimer = null;
            nextUpdateTime = null;
            stopNextUpdateCountdown();
        }
        
        // Si el modo es "off", solo detener el temporizador
        if (mode === 'off') {
            updateStatus('Actualización automática desactivada');

            // Notificar al servidor
            await fetch('/api/stocks/auto-update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ mode: 'off' })
            });
            
            return;
        }
        
        // Configurar la actualización automática en el servidor
        const response = await fetch('/api/stocks/auto-update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mode })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            updateStatus(`Error al configurar actualización automática: ${data.message}`, true);
            autoUpdateSelect.value = 'off';
            return;
        }
        
        updateStatus(`Actualización automática configurada: ${mode === '1-3' ? '1-3 minutos' : '1-5 minutos'}`);
        
        // Configurar el temporizador en el cliente
        const minMinutes = mode === '1-3' ? 1 : 1;
        const maxMinutes = mode === '1-3' ? 3 : 5;
        
        // Función para programar la próxima actualización
        function scheduleNextUpdate() {
            // Calcular un tiempo aleatorio en el rango especificado
            const minMs = minMinutes * 60 * 1000;
            const maxMs = maxMinutes * 60 * 1000;
            const updateInterval = Math.floor(minMs + Math.random() * (maxMs - minMs));
            
            // Calcular la hora de la próxima actualización
            nextUpdateTime = new Date(Date.now() + updateInterval);
            
            // Actualizar la información de próxima actualización
            updateNextUpdateInfo();
            
            // Configurar el temporizador
            autoUpdateTimer = setTimeout(async () => {
                await updateStocksData();
                scheduleNextUpdate();
            }, updateInterval);
        }
        
        // Iniciar la programación
        scheduleNextUpdate();
        
    } catch (error) {
        console.error('Error al configurar actualización automática:', error);
        updateStatus(`Error al configurar actualización automática: ${error.message}`, true);
        autoUpdateSelect.value = 'off';
        logErrorToServer(error.message, error.stack, 'setAutoUpdate');
    }
}

// Función para actualizar la información de próxima actualización
function stopNextUpdateCountdown() {
    if (nextUpdateCountdownInterval) {
        clearInterval(nextUpdateCountdownInterval);
        nextUpdateCountdownInterval = null;
    }
    nextUpdateInfo.textContent = '';
}

function updateNextUpdateInfo() {
    stopNextUpdateCountdown();

    if (!nextUpdateTime) {
        return;
    }

    function updateCountdown() {
        const now = new Date();
        const diffMs = nextUpdateTime - now;

        const modeLabel = autoUpdateSelect.value === '1-3' ? '1-3 minutos' : '1-5 minutos';

        if (diffMs <= 0) {
            nextUpdateInfo.textContent = 'Actualizando...';
            updateStatus(`Actualización automática configurada: ${modeLabel} - actualizando...`);
            return;
        }

        const diffSecs = Math.floor(diffMs / 1000);
        const minutes = Math.floor(diffSecs / 60);
        const seconds = diffSecs % 60;

        nextUpdateInfo.textContent = `Próxima actualización en: ${minutes}m ${seconds}s`;
        updateStatus(`Actualización automática configurada: ${modeLabel} - próxima en ${minutes}m ${seconds}s`);
    }

    updateCountdown();
    nextUpdateCountdownInterval = setInterval(updateCountdown, 1000);
}

// Función para iniciar el contador de sesión
function startSessionCountdown(seconds) {
    if (sessionCountdownInterval) {
        clearInterval(sessionCountdownInterval);
        sessionCountdownInterval = null;
    }

    let remaining = parseInt(seconds, 10);
    if (isNaN(remaining) || remaining <= 0) {
        sessionCountdown.textContent = '';
        return;
    }

    function update() {
        if (remaining <= 0) {
            sessionCountdown.textContent = 'Sesión expirada';
            clearInterval(sessionCountdownInterval);
            sessionCountdownInterval = null;
            return;
        }

        const m = Math.floor(remaining / 60);
        const s = remaining % 60;
        sessionCountdown.textContent = `Sesión expira en: ${m}m ${s}s`;
        remaining -= 1;
    }

    update();
    sessionCountdownInterval = setInterval(update, 1000);
}

// Función para obtener el tiempo restante de la sesión desde el servidor
async function fetchSessionTime() {
    try {
        const response = await fetch('/api/session-time');
        const data = await response.json();
        if (data && data.remaining_seconds != null) {
            startSessionCountdown(data.remaining_seconds);
        } else {
            sessionCountdown.textContent = '';
        }
    } catch (error) {
        console.error('Error al obtener tiempo de sesión:', error);
        logErrorToServer(error.message, error.stack, 'fetchSessionTime');
    }
}

// Función para guardar los códigos de acciones en localStorage
async function saveStockCodes() {
    const codes = Array.from(stockCodeInputs).map(input => input.value.trim());
    const all = allStocksCheck.checked;
    localStorage.setItem('stockCodes', JSON.stringify({ codes, all }));
    try {
        await fetch('/api/stock-filter', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codes, all })
        });
    } catch (e) {
        console.error('Error saving stock codes', e);
    }
}

// Función para cargar los códigos de acciones desde localStorage
async function loadStockCodes() {
    let saved = null;
    try {
        const resp = await fetch('/api/stock-filter');
        const data = await resp.json();
        if (data.codes) {
            saved = { codes: JSON.parse(data.codes), all: data.all };
        }
    } catch (e) {
        console.error('Error loading codes from server', e);
    }
    if (!saved) {
        const local = localStorage.getItem('stockCodes');
        if (local) {
            saved = JSON.parse(local);
        }
    }
    if (saved) {
        const { codes = [], all = false } = saved;
        stockCodeInputs.forEach((input, index) => {
            input.value = codes[index] || '';
            input.disabled = all;
        });
        allStocksCheck.checked = all;
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/credentials')
        .then(r => r.json())
        .then(data => {
            if (!data.has_credentials) {
                window.location.href = '/login.html';
            }
        });
    // Conectar con el servidor vía WebSocket
    const socket = io();
    socket.on('new_data', () => {
        fetchAndDisplayStocks();
    });
    // Cargar códigos guardados
    loadStockCodes();
    fetchSessionTime();
    renderColumnConfig();
    loadColumnPreferences().then(fetchAndDisplayStocks);
    
    // Configurar event listeners
    stockFilterForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveStockCodes();
        await fetchAndDisplayStocks();
    });
    
    clearBtn.addEventListener('click', async () => {
        stockCodeInputs.forEach(input => {
            input.value = '';
        });
        allStocksCheck.checked = false;
        stockCodeInputs.forEach(input => {
            input.disabled = false;
        });
        await saveStockCodes();
    });
    
    refreshBtn.addEventListener('click', async () => {
        await updateStocksData();
    });

    configColumnsBtn.addEventListener('click', () => {
        loadColumnPreferences();
    });

    saveColumnPrefsBtn.addEventListener('click', async () => {
        await saveColumnPreferences();
        const modal = bootstrap.Modal.getInstance(document.getElementById('columnConfigModal'));
        modal.hide();
    });
    
    autoUpdateSelect.addEventListener('change', () => {
        setAutoUpdate(autoUpdateSelect.value);
    });

    allStocksCheck.addEventListener('change', async () => {
        const disabled = allStocksCheck.checked;
        stockCodeInputs.forEach(input => {
            input.disabled = disabled;
        });
        await saveStockCodes();
    });
    
    // Cargar datos iniciales si hay códigos guardados
    const hasInitialCodes = Array.from(stockCodeInputs).some(input => input.value.trim() !== '') || allStocksCheck.checked;
    if (hasInitialCodes) {
        fetchAndDisplayStocks();
    }
});
