const newsManager = {
    app: null, // Referencia a la instancia principal de la App
    dom: {
        widget: null,
        loading: null,
        list: null,
    },

    state: {
        news: [],
    },

    init(appInstance) {
        this.app = appInstance;
        // Este método será llamado cuando el widget de noticias se añada al DOM.
        this.dom.widget = document.getElementById('news-widget-body');
        if (!this.dom.widget) return;

        this.dom.loading = this.dom.widget.querySelector('#news-loading');
        this.dom.list = this.dom.widget.querySelector('#news-list');
        
        const refreshButton = document.getElementById('newsRefreshBtn');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.fetchNews());
        }

        console.log('[NewsManager] Módulo inicializado.');
        this.fetchNews();
    },

    async fetchNews() {
        this.showLoading(true);

        try {
            // Futuro: pasar símbolos del portafolio para filtrar noticias.
            // const portfolioSymbols = portfolioManager.getSymbols();
            // const params = new URLSearchParams();
            // portfolioSymbols.forEach(s => params.append('symbol', s));
            // const response = await fetch(`/api/news?${params.toString()}`);
            
            const response = await fetch('/api/news');
            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.statusText}`);
            }
            this.state.news = await response.json();
            this.render();
        } catch (error) {
            console.error('Error al cargar noticias:', error);
            this.showError(error.message);
        } finally {
            this.showLoading(false);
        }
    },

    render() {
        if (!this.dom.list) return;

        if (this.state.news.length === 0) {
            this.dom.list.innerHTML = `<li class="list-group-item text-muted text-center">No hay noticias relevantes en este momento.</li>`;
            return;
        }

        const sentimentStyles = {
            positive: { icon: 'fa-arrow-up', color: 'text-success' },
            negative: { icon: 'fa-arrow-down', color: 'text-danger' },
            neutral: { icon: 'fa-minus', color: 'text-warning' },
        };

        this.dom.list.innerHTML = this.state.news.map(item => `
            <li class="list-group-item d-flex justify-content-between align-items-start">
                <div class="ms-2 me-auto">
                    <div class="fw-bold">${item.headline}</div>
                    <small class="text-muted">${item.source} - ${this.timeAgo(item.timestamp)}</small>
                </div>
                <span class="badge rounded-pill ${sentimentStyles[item.sentiment]?.color || 'bg-secondary'}">
                    <i class="fas ${sentimentStyles[item.sentiment]?.icon || 'fa-circle'}"></i>
                </span>
            </li>
        `).join('');
    },

    showLoading(isLoading) {
        if (!this.dom.loading || !this.dom.list) return;
        this.dom.loading.classList.toggle('d-none', !isLoading);
        this.dom.list.classList.toggle('d-none', isLoading);
        // Limpiar errores si estamos cargando de nuevo
        if (isLoading && this.dom.widget.querySelector('.alert')) {
            this.dom.widget.querySelector('.alert').remove();
        }
    },

    showError(message) {
        if (!this.dom.widget) return;
        this.dom.list.classList.add('d-none');
        this.dom.loading.classList.add('d-none');
        
        const errorHtml = `<div class="alert alert-danger m-2">${message}</div>`;
        // Evitar múltiples mensajes de error
        const existingError = this.dom.widget.querySelector('.alert');
        if (existingError) {
            existingError.innerHTML = message;
        } else {
            this.dom.widget.insertAdjacentHTML('afterbegin', errorHtml);
        }
    },

    timeAgo(isoString) {
        const date = new Date(isoString);
        const seconds = Math.floor((new Date() - date) / 1000);
        let interval = seconds / 31536000;
        if (interval > 1) return `hace ${Math.floor(interval)} años`;
        interval = seconds / 2592000;
        if (interval > 1) return `hace ${Math.floor(interval)} meses`;
        interval = seconds / 86400;
        if (interval > 1) return `hace ${Math.floor(interval)} días`;
        interval = seconds / 3600;
        if (interval > 1) return `hace ${Math.floor(interval)} horas`;
        interval = seconds / 60;
        if (interval > 1) return `hace ${Math.floor(interval)} min`;
        return `hace ${Math.floor(seconds)} seg`;
    }
}; 