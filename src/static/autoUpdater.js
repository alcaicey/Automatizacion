// src/static/js/autoUpdater.js

window.autoUpdater = {
    app: null, // Se asignará en init
    timerId: null,
    countdownInterval: null,
    
    init(appInstance) {
        this.app = appInstance;
        const autoUpdateSelect = document.getElementById('autoUpdateSelect');
        if (autoUpdateSelect) {
            autoUpdateSelect.addEventListener('change', () => this.handleAutoUpdateChange());
            const savedInterval = sessionStorage.getItem('autoUpdateInterval');
            if (savedInterval) {
                autoUpdateSelect.value = savedInterval;
            }
        }
        this.resume();
    },

    handleAutoUpdateChange() {
        const select = document.getElementById('autoUpdateSelect');
        if (!select) return;

        const intervalValue = select.value;
        sessionStorage.setItem('autoUpdateInterval', intervalValue);
        
        if (intervalValue === "off") {
            this.stop();
        } else if (this.app) {
            this.start(intervalValue);
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
            this.updateCountdownText('(Fuera de horario)');
        }
        return tradingHours;
    },

    start(intervalValue) {
        this.stop();
        if (intervalValue === "off" || !this.app) return;
        if (!this.isTradingHours()) return;

        const [min, max] = intervalValue.split('-').map(Number);
        const randomSeconds = Math.floor(Math.random() * (max * 60 - min * 60 + 1)) + (min * 60);
        
        const targetTimestamp = Date.now() + randomSeconds * 1000;
        sessionStorage.setItem('autoUpdateTarget', targetTimestamp);
        
        console.log(`[AutoUpdater] Próxima actualización programada para ${new Date(targetTimestamp).toLocaleTimeString()}.`);
        this.schedule(targetTimestamp);
    },

    resume() {
        const targetTimestamp = sessionStorage.getItem('autoUpdateTarget');
        if (targetTimestamp && Date.now() < targetTimestamp && this.isTradingHours()) {
            console.log('[AutoUpdater] Reanudando temporizador de actualización pendiente.');
            this.schedule(parseInt(targetTimestamp));
        } else {
            sessionStorage.removeItem('autoUpdateTarget');
        }
    },

    schedule(targetTimestamp) {
        this.stop();
        
        const remainingMs = targetTimestamp - Date.now();
        if (remainingMs <= 0) {
            sessionStorage.removeItem('autoUpdateTarget');
            return;
        }

        this.timerId = setTimeout(async () => {
            sessionStorage.removeItem('autoUpdateTarget');
            if (this.isTradingHours()) {
                console.log('[AutoUpdater] Disparando actualización automática.');
                await this.app.fetchAndDisplayStocks(); // Llama directamente a la app principal
                this.handleAutoUpdateChange(); // Reprogramar la siguiente
            } else {
                this.updateCountdownText('(Fuera de horario)');
            }
        }, remainingMs);

        this.startCountdown(Math.ceil(remainingMs / 1000));
    },

    stop() {
        if (this.timerId) clearTimeout(this.timerId);
        if (this.countdownInterval) clearInterval(this.countdownInterval);
        this.timerId = null;
        this.countdownInterval = null;
        this.updateCountdownText('');
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
    
    updateCountdownText(text) {
        const countdownEl = document.getElementById('countdownTimer');
        if (countdownEl) {
            countdownEl.textContent = text;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // El autoUpdater se adjunta al navbar global, por lo que puede
    // y debe inicializarse en todas las páginas para mantener el estado
    // del intervalo seleccionado por el usuario en sessionStorage.
    if (document.getElementById('autoUpdateSelect')) {
        // Se llama sin la instancia de la app. El app se asignará
        // dinámicamente solo en la página del dashboard.
        autoUpdater.init(window.app || null);
    }
});