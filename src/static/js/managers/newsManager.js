// src/static/js/managers/newsManager.js

export default class NewsManager {
    constructor(app) {
        this.app = app;
        this.container = null;
        this.dom = {}; // Centralizar elementos del DOM
        this.state = {
            news: [],
        };
    }

    initializeWidget(container) {
        if (!container) {
            console.warn('[NewsManager] Contenedor del widget no definido.');
            return;
        }
        this.container = container;
        this.dom = {
            list: this.container.querySelector('#news-list'),
            loading: this.container.querySelector('#news-loading'),
            refreshBtn: this.container.querySelector('#newsRefreshBtn'),
            // Usaremos el loading como contenedor de feedback
            feedbackContainer: this.container.querySelector('#news-widget-body'), 
        };
        
        if (this.dom.refreshBtn) {
            this.dom.refreshBtn.addEventListener('click', () => this.loadNews());
        }
        this.loadNews();
    }

    async loadNews() {
        if (!this.dom.list || !this.dom.loading) return;

        this.showFeedback('Cargando noticias...', 'info', true);
        
        try {
            const newsData = await this.app.fetchData('/api/news'); 
            this.state.news = newsData || [];
            this.render();
            // No mostramos mensaje de éxito para mantener la UI limpia
        } catch (error) {
            console.error('[NewsManager] Error al cargar noticias:', error);
            this.state.news = []; // Asegurar estado limpio
            this.render(); // Renderizar para mostrar el mensaje de "no hay noticias"
            this.showFeedback(`Error al cargar noticias: ${error.message}`, 'danger');
        }
    }

    render() {
        if (!this.dom.list) return;

        this.dom.list.innerHTML = '';
        if (this.state.news.length === 0) {
            this.dom.list.innerHTML = '<li class="list-group-item text-muted">No hay noticias disponibles en este momento.</li>';
        } else {
            this.state.news.forEach(item => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.innerHTML = `
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${item.headline}</h6>
                        <small>${new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small>
                    </div>
                    <p class="mb-1 small text-muted">${item.source} - Sentimiento: ${item.sentiment}</p>
                `;
                this.dom.list.appendChild(li);
            });
        }
        this.dom.list.classList.remove('d-none');
        this.dom.loading.classList.add('d-none'); // Ocultar el loader al final
    }

    showFeedback(message, type = 'info', isLoading = false) {
        if (!this.dom.loading && !this.dom.feedbackContainer) return;

        // Ocultar la lista mientras se carga o hay error
        if (this.dom.list) this.dom.list.classList.add('d-none');
        
        if (isLoading) {
            if (this.dom.loading) {
                this.dom.loading.innerHTML = `
                    <div class="spinner-border spinner-border-sm" role="status"></div>
                    <span class="ms-2">${message}</span>`;
                this.dom.loading.className = 'text-center p-4'; // Reset class
                this.dom.loading.classList.remove('d-none');
            }
        } else {
            // Si no estamos cargando, ocultamos el spinner
            if (this.dom.loading) this.dom.loading.classList.add('d-none');

            // Si hay un mensaje de error/éxito, podríamos mostrarlo en otro lugar
            // Por ahora, como no hay un alert dedicado, lo logueamos
            if (type === 'danger' || type === 'success') {
                console.log(`[NewsManager Feedback] ${type}: ${message}`);
                // Si la lista está vacía, el render() mostrará el mensaje adecuado
                if (this.dom.list) this.dom.list.classList.remove('d-none');
            }
        }
    }
} 