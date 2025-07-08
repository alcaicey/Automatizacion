// src/static/js/managers/newsManager.js

export default class NewsManager {
    constructor(app) {
        this.app = app;
        this.newsList = null;
        this.newsLoading = null;
        this.newsRefreshBtn = null;
        this.state = {
            news: [],
        };
    }

    init() {
        console.log('[NewsManager] init() llamado. Redirigiendo a initializeWidget().');
        this.initializeWidget();
    }

    initializeWidget(container) {
        if (!container) {
            console.warn('[NewsManager] Contenedor del widget no definido. Cancelando inicialización.');
            return;
        }
        this.newsList = container.querySelector('#news-list');
        this.newsLoading = container.querySelector('#news-loading');
        this.newsRefreshBtn = container.querySelector('#newsRefreshBtn');
        
        if (this.newsRefreshBtn) {
            this.newsRefreshBtn.addEventListener('click', () => this.loadNews());
        }
        this.loadNews();
    }

    async loadNews() {
        if (!this.newsList || !this.newsLoading) return;

        this.newsLoading.classList.remove('d-none');
        this.newsList.classList.add('d-none');
        
        try {
            const newsData = await this.app.fetchData('/api/news'); 
            this.state.news = newsData;
            this.render();
        } catch (error) {
            console.error('Error al cargar noticias:', error);
        } finally {
            this.newsLoading.classList.add('d-none');
        }
    }

    render() {
        if (!this.newsList) return;

        this.newsList.innerHTML = ''; // Limpiar lista
        if (this.state.news.length === 0) {
            this.newsList.innerHTML = '<li class="list-group-item">No hay noticias disponibles.</li>';
        } else {
            this.state.news.forEach(item => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.innerHTML = `
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${item.headline}</h6>
                        <small>${new Date(item.timestamp).toLocaleTimeString()}</small>
                    </div>
                    <p class="mb-1 small">${item.source} - Sentimiento: ${item.sentiment}</p>
                `;
                this.newsList.appendChild(li);
            });
        }
        this.newsList.classList.remove('d-none');
    }
} 