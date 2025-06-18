document.addEventListener('DOMContentLoaded', () => {
    let comparisonTable = null;
    let isFilterInitialized = false; // Flag para controlar la inicialización del filtro

    function initDataTable(selector, options) {
        if ($.fn.dataTable.isDataTable(selector)) {
            $(selector).DataTable().destroy();
        }
        $(selector).empty();
        return $(selector).DataTable(options);
    }

    // --- INICIO DE LA CORRECCIÓN: Crear el filtro personalizado como una función ---
    function initializeComparisonFilter() {
        // Si el filtro ya se inicializó, no hacer nada.
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
    // --- FIN DE LA CORRECCIÓN ---

    function loadHistory() {
        fetch('/api/history')
            .then(r => r.json())
            .then(data => {
                if (!data || data.length === 0) return;
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
<<<<<<< HEAD
                    dom: 'Bfrtip', buttons: ['excelHtml5', 'csvHtml5'], responsive: true
=======
                    dom: 'Bfrtip',
                    buttons: ['excelHtml5', 'csvHtml5'],
                    responsive: true
>>>>>>> c2bff5f397a9027fdff0a2f96099180d03c4a2c1
                });
            });
    }

    function loadComparison() {
        fetch('/api/history/compare')
            .then(r => r.json())
            .then(renderComparison);
    }

    function renderComparison(data) {
        if (!data || Object.keys(data).length === 0) {
            comparisonTable = initDataTable('#comparisonTable', {
                columns: [
                    { title: 'Símbolo' }, { title: 'Precio Anterior' }, { title: 'Precio Nuevo' },
                    { title: 'Variación' }, { title: 'Diferencia' }, { title: '% Cambio' }, { title: 'Tipo' }
                ],
                data: [], dom: 'Bfrtip', buttons: ['excelHtml5', 'csvHtml5'], responsive: true
            });
            $('#comparisonTable tbody').html('<tr><td colspan="7" class="text-center">No se encontraron diferencias.</td></tr>');
            return;
        }

        const rows = [];
<<<<<<< HEAD
        (data.changes || []).forEach(c => rows.push({ ...c, type: 'cambio' }));
        (data.new || []).forEach(n => rows.push({ new: n, symbol: n.symbol, type: 'nueva' }));
        (data.removed || []).forEach(r => rows.push({ old: r, symbol: r.symbol, type: 'eliminada' }));
        (data.unchanged || []).forEach(u => rows.push({ old: u, new: u, symbol: u.symbol, type: 'sin_cambios' }));
=======
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
>>>>>>> c2bff5f397a9027fdff0a2f96099180d03c4a2c1

        comparisonTable = initDataTable('#comparisonTable', {
            data: rows,
            columns: [
                { data: 'symbol', title: 'Símbolo' },
                { data: 'old.price', title: 'Precio Anterior', defaultContent: '<i>N/A</i>', render: $.fn.dataTable.render.number('.', ',', 2) },
                { data: 'new.price', title: 'Precio Nuevo', defaultContent: '<i>N/A</i>', render: $.fn.dataTable.render.number('.', ',', 2) },
                { data: 'new.variation', title: 'Variación', defaultContent: '', render: v => v ? `${v}%` : '' },
                { data: 'abs_diff', title: 'Diferencia', defaultContent: '', render: $.fn.dataTable.render.number('.', ',', 2) },
<<<<<<< HEAD
                { data: 'pct_diff', title: '% Cambio', defaultContent: '', render: v => v ? `${v ? $.fn.dataTable.render.number('.', ',', 2).display(v) : ''}%` : '' },
                { data: 'type', title: 'Tipo' },
            ],
            createdRow: function(row, data) { /* ... (sin cambios) ... */ },
            dom: 'Bfrtip', buttons: ['excelHtml5', 'csvHtml5'], responsive: true
        });
        
        // --- INICIO DE LA CORRECCIÓN: Llamar a la inicialización del filtro aquí ---
        initializeComparisonFilter();
        // --- FIN DE LA CORRECCIÓN ---
    }
    
    // Añadir listeners a los checkboxes de filtro
=======
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

>>>>>>> c2bff5f397a9027fdff0a2f96099180d03c4a2c1
    document.querySelectorAll('.filter-checkbox').forEach(cb => {
        cb.addEventListener('change', () => {
            // Solo redibujar la tabla si ya ha sido creada
            if (comparisonTable) comparisonTable.draw();
        });
    });

    loadHistory();
    loadComparison();
});
