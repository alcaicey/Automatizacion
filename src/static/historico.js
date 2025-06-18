document.addEventListener('DOMContentLoaded', () => {
    let comparisonTable = null;
    let isFilterInitialized = false; // Flag para controlar la inicialización del filtro

    function initDataTable(selector, options) {
        if ($.fn.dataTable.isDataTable(selector)) {
            $(selector).DataTable().destroy();
        }
        $(selector).empty(); // Limpiar la tabla antes de inicializar
        return $(selector).DataTable(options);
    }

    function initializeComparisonFilter() {
        if (isFilterInitialized) return;

        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
            // Aplicar este filtro solo a la tabla de comparación
            if (settings.nTable.id !== 'comparisonTable') return true;
            
            // Asegurarse de que la tabla y la fila existan antes de acceder a los datos
            if (!comparisonTable || !comparisonTable.row(dataIndex).any()) return true;

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

        isFilterInitialized = true; // Marcar como inicializado
        console.log("[Historico] Filtro de comparación inicializado.");
    }

    function loadHistory() {
        fetch('/api/history')
            .then(r => r.ok ? r.json() : Promise.reject('No se pudo cargar el historial'))
            .then(data => {
                if (!data || data.length === 0) {
                    console.warn("No hay datos de historial para mostrar.");
                    return;
                }
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
            })
            .catch(error => console.error("Error en loadHistory:", error));
    }

    function loadComparison() {
        fetch('/api/history/compare')
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
            console.warn("No hay datos de comparación para mostrar.");
            comparisonTable = initDataTable('#comparisonTable', {
                columns: columnsDefinition.map(c => ({ title: c.title })),
                data: [],
                dom: 'Bfrtip', buttons: ['excelHtml5', 'csvHtml5'], responsive: true
            });
            $('#comparisonTable tbody').html(`<tr><td colspan="${columnsDefinition.length}" class="text-center">No se encontraron diferencias en la última carga.</td></tr>`);
            return;
        }

        const rows = [];
        (data.changes || []).forEach(c => rows.push({ ...c, symbol: c.new?.symbol || c.old?.symbol, type: 'cambio' }));
        (data.new || []).forEach(n => rows.push({ new: n, symbol: n.symbol, type: 'nueva' }));
        (data.removed || []).forEach(r => rows.push({ old: r, symbol: r.symbol, type: 'eliminada' }));
        (data.unchanged || []).forEach(u => rows.push({ old: u, new: u, symbol: u.symbol, type: 'sin_cambios' }));

        comparisonTable = initDataTable('#comparisonTable', {
            data: rows,
            columns: columnsDefinition,
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
        
        initializeComparisonFilter();
    }
    
    document.querySelectorAll('.filter-checkbox').forEach(cb => {
        cb.addEventListener('change', () => {
            if (comparisonTable) comparisonTable.draw();
        });
    });

    loadHistory();
    loadComparison();
});