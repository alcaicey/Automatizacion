// src/static/autoUpdater.modular.js

// Refactorizado a una clase para un mejor aislamiento y testabilidad.
export class AutoUpdater {
    
    constructor(appInstance) {
        this.app = appInstance;
        this.timerId = null;
        this.countdownInterval = null;
    }
    
    // El 'init' que ata los eventos del DOM se mantendría en el script original.
    // Aquí nos centramos en la lógica pura.

    handleAutoUpdateChange(intervalValue) {
        if (intervalValue === "off") {
            this.stop();
        } else {
            this.start(intervalValue);
        }
    }

    isTradingHours() {
        const now = new Date();
        const hour = now.getHours();
        const minute = now.getMinutes();
        const isAfterOpen = (hour > 9) || (hour === 9 && minute >= 30);
        const isBeforeClose = hour < 16;
        return isAfterOpen && isBeforeClose;
    }

    start(intervalValue) {
        this.stop();
        if (intervalValue === "off" || !this.app) return;
        if (!this.isTradingHours()) return;

        const [min, max] = intervalValue.split('-').map(Number);
        const randomSeconds = Math.floor(Math.random() * (max * 60 - min * 60 + 1)) + (min * 60);
        
        this.schedule(Date.now() + randomSeconds * 1000);
    }

    schedule(targetTimestamp) {
        this.stop();
        const remainingMs = targetTimestamp - Date.now();
        if (remainingMs <= 0) return;

        this.timerId = setTimeout(() => {
            if (this.isTradingHours()) {
                this.app.fetchAndDisplayStocks();
                this.handleAutoUpdateChange(this.app.getAutoUpdateInterval());
            }
        }, remainingMs);

        this.startCountdown(Math.ceil(remainingMs / 1000));
    }

    stop() {
        if (this.timerId) clearTimeout(this.timerId);
        if (this.countdownInterval) clearInterval(this.countdownInterval);
        this.timerId = null;
        this.countdownInterval = null;
    }

    startCountdown(totalSeconds) {
        if (this.countdownInterval) clearInterval(this.countdownInterval);
        let remaining = totalSeconds;
        
        const update = () => {
            if (remaining <= 0) {
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;
            }
            // La actualización del texto del DOM se omite en la lógica pura
            remaining--;
        };
        
        update();
        this.countdownInterval = setInterval(update, 1000);
    }
} 