// src/static/auto_updater.js

window.autoUpdater = {
    timerId: null,
    countdownInterval: null,

    start(intervalValue, updateFunction, countdownUpdateFunction) {
        this.stop(); 

        if (intervalValue === "off") {
            console.log('[AutoUpdater] Auto-Update desactivado.');
            return;
        }

        const [min, max] = intervalValue.split('-').map(Number);
        const randomSeconds = Math.floor(Math.random() * (max * 60 - min * 60 + 1)) + (min * 60);
        
        console.log(`[AutoUpdater] Próxima actualización en ${randomSeconds} segundos.`);
        this.startCountdown(randomSeconds, countdownUpdateFunction);

        this.timerId = setTimeout(() => {
            console.log('[AutoUpdater] ¡Tiempo cumplido! Disparando actualización.');
            updateFunction();
        }, randomSeconds * 1000);
    },

    stop() {
        if (this.timerId) {
            clearTimeout(this.timerId);
            this.timerId = null;
        }
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
        // Limpiar el texto de la cuenta regresiva
        const countdownTimerEl = document.getElementById('countdownTimer');
        if (countdownTimerEl) countdownTimerEl.textContent = '';
    },

    startCountdown(totalSeconds, countdownUpdateFunction) {
        let remaining = totalSeconds;
        
        const updateCountdown = () => {
            if (remaining <= 0) {
                clearInterval(this.countdownInterval);
                countdownUpdateFunction('Actualizando...');
                return;
            }
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            const paddedSeconds = seconds < 10 ? '0' + seconds : seconds;
            countdownUpdateFunction(`(Próxima en ${minutes}:${paddedSeconds})`);
            remaining--;
        };

        updateCountdown();
        this.countdownInterval = setInterval(updateCountdown, 1000);
    }
};