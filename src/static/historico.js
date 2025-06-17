document.addEventListener('DOMContentLoaded', () => {
    let comparisonTable = null;

    function initDataTable(selector, options) {
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
                    order: [[1, 'desc']],
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
        (data.changes || []).forEach(c => {
            rows.push({
                ...c,
                symbol: c.new?.symbol || c.old?.symbol || 'N/A',
                type: 'cambio'
            });
        });
        (data.new || []).forEach(n => rows.push({ new: n, symbol: n.symbol || 'N/A', type: 'nueva' }));
        (data.removed || []).forEach(r => rows.push({ old: r, symbol: r.symbol || 'N/A', type: 'eliminada' }));
        (data.unchanged || []).forEach(u => rows.push({ old: u, new: u, symbol: u.symbol || 'N/A', type: 'sin_cambios' }));

        
        // Filtra filas inválidas antes de pasarlas a DataTable
        const safeRows = rows.filter(row =>
            row &&
            (row.type === 'nueva' || row.type === 'eliminada' || row.type === 'sin_cambios' ||
            (row.old && typeof row.old.price === 'number' && row.new && typeof row.new.price === 'number'))
        );
        console.warn(`[frontend] Filas válidas: ${safeRows.length}, descartadas: ${rows.length - safeRows.length}`);

        comparisonTable = initDataTable('#comparisonTable', {
            data: rows,
            columns: [
                { data: 'symbol', title: 'Símbolo' },
                { data: 'old.price', title: 'Precio Anterior', defaultContent: '<i>N/A</i>', render: $.fn.dataTable.render.number('.', ',', 2) },
                { data: 'new.price', title: 'Precio Nuevo', defaultContent: '<i>N/A</i>', render: $.fn.dataTable.render.number('.', ',', 2) },
                { data: 'new.variation', title: 'Variación', defaultContent: '', render: v => v ? `${v}%` : '' },
                { data: 'abs_diff', title: 'Diferencia', defaultContent: '', render: $.fn.dataTable.render.number('.', ',', 2) },
                { data: 'pct_diff', title: '% Cambio', defaultContent: '', render: v => v ? `${$.fn.dataTable.render.number('.', ',', 2).display(v)}%` : '' },
                { data: 'type', title: 'Tipo' }
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

    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
        if (settings.nTable.id !== 'comparisonTable') return true;
        const row = comparisonTable.row(dataIndex).data();
        const type = row?.type;
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

    document.querySelectorAll('.filter-checkbox').forEach(cb => {
        cb.addEventListener('change', () => {
            if (comparisonTable) comparisonTable.draw();
        });
    });

    loadHistory();
    loadComparison();
});
