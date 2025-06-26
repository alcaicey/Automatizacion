// src/static/js/autoUpdater.js

window.autoUpdater = {
    timerId: null,
    countdownInterval: null,
    // Se elimina 'ui: null'
    
    init() { // Se elimina el argumento uiManager
        // Este listener se adjunta una vez, sin importar la página
        const autoUpdateSelect = document.getElementById('autoUpdateSelect');
        if (autoUpdateSelect) {
            autoUpdateSelect.addEventListener('change', () => this.handleAutoUpdateChange());

            // Restaurar el valor guardado en sessionStorage al cargar cualquier página
            const savedInterval = sessionStorage.getItem('autoUpdateInterval');
            if (savedInterval) {
                autoUpdateSelect.value = savedInterval;
            }
        }
        this.resume(); 
        console.log('[AutoUpdater] Módulo inicializado y reanudado si es necesario.');
    },
    // --- NUEVA FUNCIÓN ---
    handleAutoUpdateChange() {
        const select = document.getElementById('autoUpdateSelect');
        if (!select) return;

        const intervalValue = select.value;
        sessionStorage.setItem('autoUpdateInterval', intervalValue);
        
        // Solo la página del dashboard (donde existe `window.app`) puede iniciar la actualización.
        if (intervalValue === "off") {
            this.stop();
        } else if (window.app && typeof window.app.handleUpdateClick === 'function') {
            this.start(intervalValue, () => window.app.handleUpdateClick(true));
        }
    },

    isTradingHours() {
        const now = new Date();
        const hour = now.getHours();
        const minute = now.getMinutes();
        
        const isAfterOpen = (hour > 9) || (hour === 9 && minute >= 30);
        const isBeforeClose = hour < 16;
        
        const tradingHours = isAfterOpen && isBeforeClose;
        if (!tradingHours) {
            console.log('[AutoUpdater] Fuera de horario de mercado. No se programará actualización.');
            // Llamamos a la función interna para actualizar el texto
            this.updateCountdownText('(Fuera de horario)');
        }
        return tradingHours;
    },

    start(intervalValue, updateCallback) {
        this.stop();
        if (intervalValue === "off") return;
        if (!this.isTradingHours()) return;

        const [min, max] = intervalValue.split('-').map(Number);
        const randomSeconds = Math.floor(Math.random() * (max * 60 - min * 60 + 1)) + (min * 60);
        
        const targetTimestamp = Date.now() + randomSeconds * 1000;
        sessionStorage.setItem('autoUpdateTarget', targetTimestamp);

        console.log(`[AutoUpdater] Próxima actualización programada para ${new Date(targetTimestamp).toLocaleTimeString()}.`);
        
        this.schedule(targetTimestamp, updateCallback);
    },

    resume() {
        const targetTimestamp = sessionStorage.getItem('autoUpdateTarget');
        if (targetTimestamp && Date.now() < targetTimestamp && this.isTradingHours()) {
            console.log('[AutoUpdater] Reanudando temporizador de actualización pendiente.');
            this.schedule(parseInt(targetTimestamp), () => window.app.handleUpdateClick(true));
        } else {
            sessionStorage.removeItem('autoUpdateTarget');
        }
    },

    schedule(targetTimestamp, updateCallback) {
        this.stop();
        
        const remainingMs = targetTimestamp - Date.now();
        if (remainingMs <= 0) {
            sessionStorage.removeItem('autoUpdateTarget');
            return; 
        }

        this.timerId = setTimeout(() => {
            console.log('[AutoUpdater] Disparando actualización automática.');
            sessionStorage.removeItem('autoUpdateTarget');
            if (this.isTradingHours()) {
                updateCallback();
            } else {
                console.log('[AutoUpdater] Tiempo cumplido, pero ya estamos fuera de horario. Se cancela la ejecución.');
                const select = document.getElementById('autoUpdateSelect');
                const intervalValue = select ? select.value : 'off';
                if(intervalValue !== 'off') {
                    this.start(intervalValue, updateCallback);
                }
            }
        }, remainingMs);

        this.startCountdown(Math.ceil(remainingMs / 1000));
    },

    stop() {
        if (this.timerId) clearTimeout(this.timerId);
        if (this.countdownInterval) clearInterval(this.countdownInterval);
        this.timerId = null;
        this.countdownInterval = null;
        this.updateCountdownText(''); // Usamos la función interna
        sessionStorage.removeItem('autoUpdateTarget');
    },

    startCountdown(totalSeconds) {
        if (this.countdownInterval) clearInterval(this.countdownInterval);
        
        let remaining = totalSeconds;
        
        const update = () => {
            if (remaining <= 0) {
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;
                this.updateCountdownText('Actualizando...');
                return;
            }
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            this.updateCountdownText(`(Próxima en ${minutes}:${seconds < 10 ? '0' : ''}${seconds})`);
            remaining--;
        };
        
        update();
        this.countdownInterval = setInterval(update, 1000);
    },
    
    // --- NUEVA FUNCIÓN INTERNA ---
    updateCountdownText(text) {
        const countdownEl = document.getElementById('countdownTimer');
        if (countdownEl) {
            countdownEl.textContent = text;
        }
    }
};
// --- INICIO DE LA MODIFICACIÓN: Inicialización global ---
// Ahora se inicializa en todas las páginas para que el estado persista.
document.addEventListener('DOMContentLoaded', () => {
    // Solo inicializamos si el componente existe en el DOM (en el navbar)
    if (document.getElementById('globalAutoUpdater')) {
        autoUpdater.init();
    }
});
// --- FIN DE LA MODIFICACIÓN ---