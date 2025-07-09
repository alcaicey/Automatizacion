document.addEventListener('DOMContentLoaded', () => {
    let comparisonTable = null;
    let isFilterInitialized = false;
    
    // Referencias a los elementos del nuevo formulario de filtro
    const stockFilterForm = document.getElementById('stockFilterForm');
    const stockCodeInputs = document.querySelectorAll('.stock-code');
    const allStocksCheck = document.getElementById('allStocksCheck');
    const clearBtn = document.getElementById('clearBtn');

    function initDataTable(selector, options, toolbarSelector = null) {
        if ($.fn.dataTable.isDataTable(selector)) {
            $(selector).DataTable().destroy();
        }
        $(selector).empty();
        
        const defaultOptions = {
            dom: 'Bfrtip',
            buttons: ['excelHtml5', 'csvHtml5'],
            responsive: true,
            language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
            initComplete: function () {
                if (toolbarSelector) {
                    const dtContainer = $(this.api().table().container());
                    const toolbar = $(toolbarSelector);
                    if (toolbar.length) {
                        toolbar.find('.dt-buttons, .dataTables_filter').remove();
                        dtContainer.find('.dt-buttons').appendTo(toolbar);
                        dtContainer.find('.dataTables_filter').appendTo(toolbar);
                        toolbar.find('.dataTables_filter input').attr('id', `${$(selector).attr('id')}Search`);
                    }
                }
            }
        };

        return $(selector).DataTable({...defaultOptions, ...options});
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
        fetch('/api/data/history')
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
                    order: [[1, 'desc']]
                }, '#history-toolbar');
            }).catch(error => console.error("Error en loadHistory:", error));
    }

    function loadComparison(codes = []) {
        const queryParams = new URLSearchParams();
        if (codes && codes.length > 0) {
            codes.forEach(code => queryParams.append('code', code));
        }
        
        fetch(`/api/data/history/compare?${queryParams.toString()}`)
            .then(r => r.ok ? r.json() : Promise.reject('No se pudo cargar la comparación'))
            .then(renderComparison)
            .catch(error => console.error("Error en loadComparison:", error));
    }

    function coloredNumberRender(isPercent = false) {
        return function(data, type, row) {
            if (type === 'display') {
                if (data === null || data === undefined) return '<i>N/A</i>';
                const number = parseFloat(data);
                if (isNaN(number)) return '<i>N/A</i>';

                const colorClass = number > 0 ? 'text-success' : (number < 0 ? 'text-danger' : 'text-muted');
                let formatted = $.fn.dataTable.render.number('.', ',', 2, '', isPercent ? '%' : '').display(number);
                return `<span class="fw-bold ${colorClass}">${formatted}</span>`;
            }
            return data;
        };
    }
    function renderComparison(data) {
        const columnsDefinition = [
            { data: 'symbol', title: 'Símbolo' },
            { data: 'old.price', title: 'Precio Anterior', defaultContent: '<i>N/A</i>', render: coloredNumberRender() },
            { data: 'new.price', title: 'Precio Nuevo', defaultContent: '<i>N/A</i>', render: coloredNumberRender() },
            { data: 'new.variation', title: 'Variación', defaultContent: '<i>N/A</i>', render: coloredNumberRender(true) },
            { data: 'abs_diff', title: 'Diferencia', defaultContent: '<i>N/A</i>', render: coloredNumberRender() },
            { data: 'pct_diff', title: '% Cambio', defaultContent: '<i>N/A</i>', render: coloredNumberRender(true) },
            { data: 'type', title: 'Tipo' },
        ];

        if (!data || Object.keys(data).length === 0 || (!data.changes && !data.new && !data.removed)) {
            comparisonTable = initDataTable('#comparisonTable', {
                columns: columnsDefinition.map(c => ({ title: c.title })),
                data: []
            }, '#comparison-toolbar');
            $('#comparisonTable tbody').html(`<tr><td colspan="${columnsDefinition.length}" class="text-center">No se encontraron diferencias.</td></tr>`);
            return;
        }

        const rows = [];
        (data.changes || []).forEach(c => rows.push({ ...c, symbol: c.new.symbol, type: 'cambio' }));
        (data.new || []).forEach(n => rows.push({ new: n, symbol: n.symbol, type: 'nueva' }));
        (data.removed || []).forEach(r => rows.push({ old: r, symbol: r.symbol, type: 'eliminada' }));
        (data.unchanged || []).forEach(u => rows.push({ old: u, new: u, symbol: u.symbol, type: 'sin_cambios' }));

        comparisonTable = initDataTable('#comparisonTable', {
            data: rows, columns: columnsDefinition,
            createdRow: function(row, data) {
                const typeClasses = {'nueva': 'table-primary', 'eliminada': 'table-secondary', 'cambio': data.abs_diff > 0 ? 'table-success' : 'table-danger'};
                if (typeClasses[data.type]) $(row).addClass(typeClasses[data.type]);
            }
        }, '#comparison-toolbar');
        
        initializeComparisonFilter();
    }
    
    async function loadAndApplyFilters() {
        try {
            const response = await fetch('/api/data/filters');
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
        await fetch('/api/data/filters', {
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