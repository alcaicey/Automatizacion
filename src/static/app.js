// Funcionalidad principal de la aplicación

// Variables globales
let autoUpdateTimer = null;
let lastStockCodes = [];
let nextUpdateTime = null;
let updateStatusInterval = null;
let isUpdating = false;

// Elementos DOM
const stockFilterForm = document.getElementById('stockFilterForm');
const stockCodeInputs = document.querySelectorAll('.stock-code');
const autoUpdateSelect = document.getElementById('autoUpdateSelect');
const clearBtn = document.getElementById('clearBtn');
const refreshBtn = document.getElementById('refreshBtn');
const statusMessage = document.getElementById('statusMessage');
const lastUpdate = document.getElementById('lastUpdate');
const stocksTable = document.getElementById('stocksTable');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingMessage = document.getElementById('loadingMessage');
const nextUpdateInfo = document.getElementById('nextUpdateInfo');
const sessionCountdown = document.getElementById('sessionCountdown');

let sessionCountdownInterval = null;

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

// Función para obtener y mostrar los datos de acciones
async function fetchAndDisplayStocks() {
    try {
        toggleLoading(true, 'Cargando datos de acciones...');
        
        // Obtener códigos de acciones no vacíos
        const stockCodes = Array.from(stockCodeInputs)
            .map(input => input.value.trim())
            .filter(code => code !== '');
        
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
    } finally {
        toggleLoading(false);
    }
}

// Función para actualizar la tabla de acciones
function updateStocksTable(data) {
    const tbody = stocksTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    // Verificar si hay datos para mostrar
    const stocks = data.data || [];
    
    if (stocks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4">
                    <div class="text-muted">No hay datos disponibles</div>
                </td>
            </tr>
        `;
        return;
    }
    
    // Crear filas para cada acción
    stocks.forEach(stock => {
        // Determinar si la variación es positiva o negativa
        const variationValue = parseFloat(stock.VARIACION || 0);
        const isPositive = variationValue > 0;
        const isNegative = variationValue < 0;
        const variationClass = isPositive ? 'variation-positive' : (isNegative ? 'variation-negative' : '');
        const arrowIcon = isPositive ? 'fa-arrow-up arrow-up' : (isNegative ? 'fa-arrow-down arrow-down' : '');
        
        // Crear la fila
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${stock.NEMO || '--'}</strong></td>
            <td>${formatNumber(stock.PRECIO_CIERRE || 0)}</td>
            <td class="${variationClass}">
                ${arrowIcon ? `<i class="fas ${arrowIcon} me-1"></i>` : ''}
                ${formatNumber(stock.VARIACION || 0)} (${formatNumber(variationValue, 2)}%)
            </td>
            <td>${formatNumber(stock.PRECIO_COMPRA || 0)}</td>
            <td>${formatNumber(stock.PRECIO_VENTA || 0)}</td>
            <td>${formatNumber(stock.MONTO || 0, 0)}</td>
            <td>${stock.MONEDA || '--'}</td>
            <td>${formatNumber(stock.UN_TRANSADAS || 0, 0)}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Aplicar animación de actualización
    tbody.querySelectorAll('tr').forEach(row => {
        row.classList.add('highlight-update');
        setTimeout(() => {
            row.classList.remove('highlight-update');
        }, 2000);
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
                toggleLoading(false);
            } finally {
                isUpdating = false;
            }
        }, 20000);
        
    } catch (error) {
        console.error('Error al actualizar datos:', error);
        updateStatus(`Error al actualizar datos: ${error.message}`, true);
        toggleLoading(false);
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
            nextUpdateInfo.textContent = '';
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
    }
}

// Función para actualizar la información de próxima actualización
function updateNextUpdateInfo() {
    if (!nextUpdateTime) {
        nextUpdateInfo.textContent = '';
        return;
    }
    
    function updateCountdown() {
        const now = new Date();
        const diffMs = nextUpdateTime - now;
        
        if (diffMs <= 0) {
            nextUpdateInfo.textContent = 'Actualizando...';
            return;
        }
        
        const diffSecs = Math.floor(diffMs / 1000);
        const minutes = Math.floor(diffSecs / 60);
        const seconds = diffSecs % 60;
        
        nextUpdateInfo.textContent = `Próxima actualización en: ${minutes}m ${seconds}s`;
    }
    
    // Actualizar inmediatamente y luego cada segundo
    updateCountdown();
    const countdownInterval = setInterval(updateCountdown, 1000);
    
    // Limpiar el intervalo cuando se actualice
    if (autoUpdateTimer) {
        const originalClearTimeout = window.clearTimeout;
        const wrappedClearTimeout = function(id) {
            if (id === autoUpdateTimer) {
                clearInterval(countdownInterval);
            }
            return originalClearTimeout(id);
        };
        window.clearTimeout = wrappedClearTimeout;
    }
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
    }
}

// Función para guardar los códigos de acciones en localStorage
function saveStockCodes() {
    const codes = Array.from(stockCodeInputs).map(input => input.value.trim());
    localStorage.setItem('stockCodes', JSON.stringify(codes));
}

// Función para cargar los códigos de acciones desde localStorage
function loadStockCodes() {
    const savedCodes = localStorage.getItem('stockCodes');
    if (savedCodes) {
        const codes = JSON.parse(savedCodes);
        stockCodeInputs.forEach((input, index) => {
            if (codes[index]) {
                input.value = codes[index];
            }
        });
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Cargar códigos guardados
    loadStockCodes();
    fetchSessionTime();
    
    // Configurar event listeners
    stockFilterForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        saveStockCodes();
        await fetchAndDisplayStocks();
    });
    
    clearBtn.addEventListener('click', () => {
        stockCodeInputs.forEach(input => {
            input.value = '';
        });
        saveStockCodes();
    });
    
    refreshBtn.addEventListener('click', async () => {
        await updateStocksData();
    });
    
    autoUpdateSelect.addEventListener('change', () => {
        setAutoUpdate(autoUpdateSelect.value);
    });
    
    // Cargar datos iniciales si hay códigos guardados
    const hasInitialCodes = Array.from(stockCodeInputs).some(input => input.value.trim() !== '');
    if (hasInitialCodes) {
        fetchAndDisplayStocks();
    }
});
