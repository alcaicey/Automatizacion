// src/static/js/autoUpdater.js

window.autoUpdater = {
    timerId: null,
    countdownInterval: null,
    ui: null,
    
    init(uiManager) {
        this.ui = uiManager;
        // Al iniciar, comprueba si hay una actualización pendiente en la sesión.
        this.resume(); 
        console.log('[AutoUpdater] Módulo inicializado y reanudado si es necesario.');
    },

    // --- INICIO DE CORRECCIÓN: Función para verificar horario de mercado ---
    isTradingHours() {
        const now = new Date();
        const hour = now.getHours();
        const minute = now.getMinutes();
        
        // Horario: 9:30 AM a 16:00 PM (4 PM)
        const isAfterOpen = (hour > 9) || (hour === 9 && minute >= 30);
        const isBeforeClose = hour < 16;
        
        const tradingHours = isAfterOpen && isBeforeClose;
        if (!tradingHours) {
            console.log('[AutoUpdater] Fuera de horario de mercado. No se programará actualización.');
            this.ui.updateCountdown('(Fuera de horario)');
        }
        return tradingHours;
    },
    // --- FIN DE CORRECCIÓN ---

    start(intervalValue, updateCallback) {
        this.stop(); // Detiene cualquier temporizador anterior
        sessionStorage.removeItem('autoUpdateTarget'); // Limpiar estado antiguo

        if (intervalValue === "off") return;
        
        // --- INICIO DE CORRECCIÓN: Verificar horario antes de empezar ---
        if (!this.isTradingHours()) {
            return;
        }
        // --- FIN DE CORRECCIÓN ---

        const [min, max] = intervalValue.split('-').map(Number);
        const randomSeconds = Math.floor(Math.random() * (max * 60 - min * 60 + 1)) + (min * 60);
        
        const targetTimestamp = Date.now() + randomSeconds * 1000;
        sessionStorage.setItem('autoUpdateTarget', targetTimestamp);

        console.log(`[AutoUpdater] Próxima actualización programada para ${new Date(targetTimestamp).toLocaleTimeString()}.`);
        
        this.schedule(targetTimestamp, updateCallback);
    },

    resume() {
        const targetTimestamp = sessionStorage.getItem('autoUpdateTarget');
        // --- INICIO DE CORRECCIÓN: Verificar horario también al reanudar ---
        if (targetTimestamp && Date.now() < targetTimestamp && this.isTradingHours()) {
            console.log('[AutoUpdater] Reanudando temporizador de actualización pendiente.');
            this.schedule(parseInt(targetTimestamp), () => window.app.handleUpdateClick(true));
        } else {
            // Si hay un target pero estamos fuera de horario, lo limpiamos.
            sessionStorage.removeItem('autoUpdateTarget');
        }
        // --- FIN DE CORRECCIÓN ---
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
            // --- INICIO DE CORRECCIÓN: Última verificación de horario antes de ejecutar ---
            if (this.isTradingHours()) {
                updateCallback();
            } else {
                console.log('[AutoUpdater] Tiempo cumplido, pero ya estamos fuera de horario. Se cancela la ejecución.');
                // Reinicia el ciclo para el día siguiente si es necesario (o simplemente no hace nada)
                const intervalValue = window.app ? window.app.uiManager.dom.autoUpdateSelect.value : 'off';
                if(intervalValue !== 'off') {
                    this.start(intervalValue, updateCallback);
                }
            }
            // --- FIN DE CORRECCIÓN ---
        }, remainingMs);

        this.startCountdown(Math.ceil(remainingMs / 1000));
    },

    stop() {
        if (this.timerId) clearTimeout(this.timerId);
        if (this.countdownInterval) clearInterval(this.countdownInterval);
        this.timerId = null;
        this.countdownInterval = null;
        this.ui.updateCountdown('');
        sessionStorage.removeItem('autoUpdateTarget');
    },

    startCountdown(totalSeconds) {
        if (this.countdownInterval) clearInterval(this.countdownInterval);
        
        let remaining = totalSeconds;
        
        const update = () => {
            if (remaining <= 0) {
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;
                this.ui.updateCountdown('Actualizando...');
                return;
            }
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            this.ui.updateCountdown(`(Próxima en ${minutes}:${seconds < 10 ? '0' : ''}${seconds})`);
            remaining--;
        };
        
        update();
        this.countdownInterval = setInterval(update, 1000);
    }
};