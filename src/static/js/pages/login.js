// src/static/js/pages/login.js
export default class LoginPage {
    constructor(app) {
        this.app = app;
        this.form = document.getElementById('loginForm');
        this.errorContainer = document.getElementById('login-error');
    }

    initialize() {
        if (!this.form) return;
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
    }

    async handleSubmit(event) {
        event.preventDefault();
        this.app.uiManager.toggleLoading(true, 'Iniciando sesión...');
        this.errorContainer.classList.add('d-none');

        const formData = new FormData(this.form);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (response.ok) {
                window.location.href = '/'; // Redirigir al dashboard
            } else {
                const errorData = await response.json();
                this.showError(errorData.message || 'Error desconocido al iniciar sesión.');
            }
        } catch (error) {
            this.showError('No se pudo conectar con el servidor.');
        } finally {
            this.app.uiManager.toggleLoading(false);
        }
    }

    showError(message) {
        this.errorContainer.textContent = message;
        this.errorContainer.classList.remove('d-none');
    }
} 