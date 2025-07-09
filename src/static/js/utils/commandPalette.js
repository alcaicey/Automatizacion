// src/static/js/utils/commandPalette.js
export default class CommandPalette {
    constructor(app) {
        this.app = app;
        this.modalElement = document.getElementById('commandPaletteModal');
        this.inputElement = document.getElementById('commandPaletteInput');
        this.resultsElement = document.getElementById('commandPaletteResults');
        if (!this.modalElement) return;

        this.modal = new bootstrap.Modal(this.modalElement);
        this.allSymbols = [];
        this.selectedIndex = -1;
    }

    initialize() {
        // La comprobación de !this.modalElement en el constructor ya previene errores si no existe.
        document.addEventListener('keydown', this.handleGlobalKeyDown.bind(this));
        
        this.modalElement.addEventListener('shown.bs.modal', async () => {
            this.inputElement.focus();
            if (this.allSymbols.length === 0) {
                await this.fetchSymbols();
            }
        });
        
        this.modalElement.addEventListener('hidden.bs.modal', () => {
            this.inputElement.value = '';
            this.resultsElement.innerHTML = '';
            this.selectedIndex = -1;
        });
        
        this.inputElement.addEventListener('input', this.handleInput.bind(this));
        this.inputElement.addEventListener('keydown', this.handleInputKeyDown.bind(this));
        console.log("[CommandPalette] Inicializado.");
    }

    handleGlobalKeyDown(e) {
        if (e.ctrlKey && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            this.modal.show();
        }
    }

    handleInputKeyDown(e) {
        const items = this.resultsElement.getElementsByTagName('li');
        if (items.length === 0 && e.key !== 'Escape') return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.updateSelection(1);
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.updateSelection(-1);
                break;
            case 'Enter':
                e.preventDefault();
                this.selectItem();
                break;
            case 'Escape':
                this.modal.hide();
                break;
        }
    }
    
    updateSelection(direction) {
        const items = this.resultsElement.getElementsByTagName('li');
        if (this.selectedIndex !== -1) items[this.selectedIndex]?.classList.remove('active');
        
        this.selectedIndex += direction;
        if (this.selectedIndex >= items.length) this.selectedIndex = 0;
        if (this.selectedIndex < 0) this.selectedIndex = items.length - 1;

        items[this.selectedIndex]?.classList.add('active');
        items[this.selectedIndex]?.scrollIntoView({ block: 'nearest' });
    }

    selectItem() {
        const selectedItem = this.resultsElement.querySelector('li.active');
        if (!selectedItem) return;
        
        this.executeAction(selectedItem.dataset.symbol);
    }
    
    executeAction(symbol) {
        console.log(`Acción ejecutada para: ${symbol}`);
        this.modal.hide();

        const symbolInput = document.getElementById('symbolInput');
        const plotBtn = document.getElementById('plotBtn');

        if (symbolInput && plotBtn) {
            symbolInput.value = symbol;
            plotBtn.click();
        } else {
            console.warn('No se encontró el gráfico de historial para autocompletar.');
            window.location.href = '/dashboard'; // Opcional: redirigir si no está en la página correcta
        }
    }

    async fetchSymbols() {
        try {
            const response = await fetch('/api/data/all_stock_symbols');
            if (!response.ok) throw new Error('Error al cargar símbolos');
            this.allSymbols = await response.json();
            this.renderResults(); // Mostrar todos los símbolos al principio
        } catch (error) {
            console.error('Error fetching symbols for command palette:', error);
            this.resultsElement.innerHTML = '<li class="list-group-item text-danger">Error al cargar símbolos.</li>';
        }
    }

    handleInput() {
        this.renderResults();
    }
    
    renderResults() {
        const query = this.inputElement.value.toLowerCase();
        this.resultsElement.innerHTML = '';
        this.selectedIndex = -1;

        const filteredSymbols = this.allSymbols
            .filter(symbol => symbol && symbol.toLowerCase().includes(query))
            .slice(0, 10);

        if (filteredSymbols.length === 0 && query) {
            this.resultsElement.innerHTML = '<li class="list-group-item text-muted">No se encontraron resultados.</li>';
            return;
        }
        
        filteredSymbols.forEach(symbol => {
            const li = document.createElement('li');
            li.className = 'list-group-item list-group-item-action';
            li.textContent = symbol;
            li.dataset.symbol = symbol;
            li.style.cursor = 'pointer';
            li.addEventListener('click', () => this.executeAction(symbol));
            this.resultsElement.appendChild(li);
        });
    }
} 