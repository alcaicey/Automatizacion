document.addEventListener('DOMContentLoaded', () => {
    let comparisonTable = null;

    function initDataTable(selector, options) {
        // Si la tabla ya fue inicializada, la destruye primero
        if ($.fn.dataTable.isDataTable(selector)) {
            $(selector).DataTable().destroy();
        }
        return $(selector).DataTable(options);
    }

    function loadHistory() {
        fetch('/api/history')
            .then(r => r.json())
            .then(data => {
                initDataTable('#historyTable', {
                    data: data,
                    columns: [
                        { data: 'file', title: 'Archivo/ID' },
                        { data: 'timestamp', title: 'Fecha' },
                        { data: 'total', title: 'Total' },
                        { data: 'changes', title: 'Cambios' },
                        { data: 'new', title: 'Nuevas' },
                        { data: 'removed', title: 'Eliminadas' },
                        { data: 'error_count', title: 'Errores' },
                        { data: 'status', title: 'Estado' }
                    ],
                    order: [[1, 'desc']], // Ordenar por fecha descendente
                    dom: 'Bfrtip',
                    buttons: ['excelHtml5', 'csvHtml5'],
                    responsive: true
                });
            });
    }

    function loadComparison() {
        fetch('/api/history/compare')
            .then(r => r.json())
            .then(renderComparison);
    }

    function renderComparison(data) {
        const rows = [];
        
        // Unificar todos los tipos de cambios en una sola estructura de filas
        (data.changes || []).forEach(c => rows.push({ ...c, type: 'cambio' }));
        (data.new || []).forEach(n => rows.push({ new: n, symbol: n.symbol, type: 'nueva' }));
        (data.removed || []).forEach(r => rows.push({ old: r, symbol: r.symbol, type: 'eliminada' }));
        (data.unchanged || []).forEach(u => rows.push({ old: u, new: u, symbol: u.symbol, type: 'sin_cambios' }));

        comparisonTable = initDataTable('#comparisonTable', {
            data: rows,
            columns: [
                { data: 'symbol', title: 'Símbolo' },
                { data: 'old.price', title: 'Precio Anterior', defaultContent: '<i>N/A</i>', render: $.fn.dataTable.render.number('.', ',', 2) },
                { data: 'new.price', title: 'Precio Nuevo', defaultContent: '<i>N/A</i>', render: $.fn.dataTable.render.number('.', ',', 2) },
                { data: 'new.variation', title: 'Variación', defaultContent: '', render: v => v ? `${v}%` : '' },
                { data: 'abs_diff', title: 'Diferencia', defaultContent: '', render: $.fn.dataTable.render.number('.', ',', 2) },
                { data: 'pct_diff', title: '% Cambio', defaultContent: '', render: v => v ? `${$.fn.dataTable.render.number('.', ',', 2).display(v)}%` : '' },
                { data: 'type', title: 'Tipo' },
            ],
            createdRow: function(row, data) {
                const typeClasses = {
                    'nueva': 'table-primary', 
                    'eliminada': 'table-secondary',
                    'error': 'table-warning', 
                    'cambio': data.abs_diff > 0 ? 'table-success' : 'table-danger'
                };
                if (typeClasses[data.type]) row.classList.add(typeClasses[data.type]);
            },
            dom: 'Bfrtip',
            buttons: ['excelHtml5', 'csvHtml5'],
            responsive: true
        });
    }

    // Filtro personalizado para la tabla de comparación
    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
        if (settings.nTable.id !== 'comparisonTable') return true;
        const type = comparisonTable.row(dataIndex).data().type;
        if (!type) return true;
        
        const filters = {
            'cambio': document.getElementById('filterChanges').checked,
            'nueva': document.getElementById('filterNew').checked,
            'eliminada': document.getElementById('filterRemoved').checked,
            'error': document.getElementById('filterErrors').checked,
            'sin_cambios': document.getElementById('filterUnchanged').checked
        };
        return filters[type];
    });

    // Añadir listeners a los checkboxes de filtro
    document.querySelectorAll('.filter-checkbox').forEach(cb => {
        cb.addEventListener('change', () => {
            if (comparisonTable) comparisonTable.draw();
        });
    });

    // Carga inicial de datos
    loadHistory();
    loadComparison();
});