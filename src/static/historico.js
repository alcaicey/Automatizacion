document.addEventListener('DOMContentLoaded', () => {
    let comparisonTable = null;
    let isFilterInitialized = false;
    
    // Referencias a los elementos del nuevo formulario de filtro
    const stockFilterForm = document.getElementById('stockFilterForm');
    const stockCodeInputs = document.querySelectorAll('.stock-code');
    const allStocksCheck = document.getElementById('allStocksCheck');
    const clearBtn = document.getElementById('clearBtn');

    function initDataTable(selector, options) {
        if ($.fn.dataTable.isDataTable(selector)) {
            $(selector).DataTable().destroy();
        }
        $(selector).empty();
        return $(selector).DataTable(options);
    }

    function initializeComparisonFilter() {
        if (isFilterInitialized) return;
        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
            if (settings.nTable.id !== 'comparisonTable' || !comparisonTable.row(dataIndex).any()) return true;
            const rowData = comparisonTable.row(dataIndex).data();
            if (!rowData || !rowData.type) return true;
            const type = rowData.type;
            const filters = {
                'cambio': document.getElementById('filterChanges').checked,
                'nueva': document.getElementById('filterNew').checked,
                'eliminada': document.getElementById('filterRemoved').checked,
                'error': document.getElementById('filterErrors').checked,
                'sin_cambios': document.getElementById('filterUnchanged').checked
            };
            return filters[type];
        });
        isFilterInitialized = true;
    }

    function loadHistory() {
        fetch('/api/history')
            .then(r => r.ok ? r.json() : Promise.reject('No se pudo cargar el historial'))
            .then(data => {
                if (!data || data.length === 0) return;
                initDataTable('#historyTable', {
                    data: data,
                    columns: [
                        { data: 'file', title: 'Archivo/ID' }, { data: 'timestamp', title: 'Fecha' },
                        { data: 'total', title: 'Total' }, { data: 'changes', title: 'Cambios' },
                        { data: 'new', title: 'Nuevas' }, { data: 'removed', title: 'Eliminadas' },
                        { data: 'error_count', title: 'Errores' }, { data: 'status', title: 'Estado' }
                    ],
                    order: [[1, 'desc']], dom: 'Bfrtip', buttons: ['excelHtml5', 'csvHtml5'], responsive: true
                });
            }).catch(error => console.error("Error en loadHistory:", error));
    }

    function loadComparison(codes = []) {
        const queryParams = new URLSearchParams();
        if (codes && codes.length > 0) {
            codes.forEach(code => queryParams.append('code', code));
        }
        
        fetch(`/api/history/compare?${queryParams.toString()}`)
            .then(r => r.ok ? r.json() : Promise.reject('No se pudo cargar la comparación'))
            .then(renderComparison)
            .catch(error => console.error("Error en loadComparison:", error));
    }

    function renderComparison(data) {
        const columnsDefinition = [
            { data: 'symbol', title: 'Símbolo' },
            { data: 'old.price', title: 'Precio Anterior', defaultContent: '<i>N/A</i>', render: $.fn.dataTable.render.number('.', ',', 2) },
            { data: 'new.price', title: 'Precio Nuevo', defaultContent: '<i>N/A</i>', render: $.fn.dataTable.render.number('.', ',', 2) },
            { data: 'new.variation', title: 'Variación', defaultContent: '', render: v => v ? `${v}%` : '' },
            { data: 'abs_diff', title: 'Diferencia', defaultContent: '', render: $.fn.dataTable.render.number('.', ',', 2) },
            { data: 'pct_diff', title: '% Cambio', defaultContent: '', render: v => v && typeof v === 'number' ? `${$.fn.dataTable.render.number('.', ',', 2).display(v)}%` : '' },
            { data: 'type', title: 'Tipo' },
        ];

        if (!data || Object.keys(data).length === 0 || (!data.changes && !data.new && !data.removed)) {
            comparisonTable = initDataTable('#comparisonTable', {
                columns: columnsDefinition.map(c => ({ title: c.title })),
                data: [], dom: 'Bfrtip', buttons: ['excelHtml5', 'csvHtml5'], responsive: true
            });
            $('#comparisonTable tbody').html(`<tr><td colspan="${columnsDefinition.length}" class="text-center">No se encontraron diferencias.</td></tr>`);
            return;
        }

        const rows = [];
        (data.changes || []).forEach(c => rows.push({ ...c, type: 'cambio' }));
        (data.new || []).forEach(n => rows.push({ new: n, symbol: n.symbol, type: 'nueva' }));
        (data.removed || []).forEach(r => rows.push({ old: r, symbol: r.symbol, type: 'eliminada' }));
        (data.unchanged || []).forEach(u => rows.push({ old: u, new: u, symbol: u.symbol, type: 'sin_cambios' }));

        comparisonTable = initDataTable('#comparisonTable', {
            data: rows, columns: columnsDefinition,
            createdRow: function(row, data) {
                const typeClasses = {'nueva': 'table-primary', 'eliminada': 'table-secondary', 'cambio': data.abs_diff > 0 ? 'table-success' : 'table-danger'};
                if (typeClasses[data.type]) row.classList.add(typeClasses[data.type]);
            },
            dom: 'Bfrtip', buttons: ['excelHtml5', 'csvHtml5'], responsive: true
        });
        
        initializeComparisonFilter();
    }
    
    async function loadAndApplyFilters() {
        try {
            const response = await fetch('/api/filters');
            const filters = await response.json();
            allStocksCheck.checked = filters.all;
            stockCodeInputs.forEach((input, index) => {
                input.value = filters.codes[index] || '';
            });
            loadComparison(filters.all ? [] : filters.codes);
        } catch (error) {
            console.error("Error al cargar filtros:", error);
            loadComparison([]);
        }
    }
    
    async function handleFilterSubmit(event) {
        event.preventDefault();
        const codes = Array.from(stockCodeInputs).map(input => input.value.trim().toUpperCase()).filter(Boolean);
        const showAll = allStocksCheck.checked;
        await fetch('/api/filters', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codes: showAll ? [] : codes, all: showAll })
        });
        loadComparison(showAll ? [] : codes);
    }
    
    document.querySelectorAll('.filter-checkbox').forEach(cb => {
        cb.addEventListener('change', () => {
            if (comparisonTable) comparisonTable.draw();
        });
    });

    if(stockFilterForm) stockFilterForm.addEventListener('submit', handleFilterSubmit);
    if(clearBtn) {
        clearBtn.addEventListener('click', () => {
            stockFilterForm.reset();
            allStocksCheck.checked = true;
        });
    }

    loadHistory();
    loadAndApplyFilters();
});