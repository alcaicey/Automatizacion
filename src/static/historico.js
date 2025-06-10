document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    loadComparison();
    document.querySelectorAll('.filter-checkbox').forEach(cb => {
        cb.addEventListener('change', () => {
            if (window.comparisonTable) {
                window.comparisonTable.draw();
            }
        });
    });
});

function loadHistory() {
    fetch('/api/history')
        .then(r => r.json())
        .then(data => {
            $('#historyTable').DataTable({
                data: data,
                columns: [
                    { data: 'file' },
                    { data: 'timestamp' },
                    { data: 'total' },
                    { data: 'changes' },
                    { data: 'new' },
                    { data: 'removed' },
                    { data: 'error_count' },
                    { data: 'status' }
                ],
                order: [[0, 'desc']],
                dom: 'Bfrtip',
                buttons: ['excelHtml5', 'csvHtml5']
            });
        });
}

function loadComparison() {
    fetch('/api/history/compare')
        .then(r => r.json())
        .then(renderComparison);
}

function renderComparison(data) {
    let rows = [];
    let columns = [];

    // Si los datos son un arreglo simple proveniente de compare_history.py
    if (Array.isArray(data)) {
        rows = data.map(d => ({
            symbol: d.symbol,
            precio_anterior: d.precio_anterior,
            precio_nuevo: d.precio_nuevo,
            diferencia: d.diferencia,
            porcentaje: d.porcentaje,
        }));

        columns = [
            { data: 'symbol', title: 'Símbolo' },
            { data: 'precio_anterior', title: 'Precio Anterior' },
            { data: 'precio_nuevo', title: 'Precio Nuevo' },
            { data: 'diferencia', title: 'Diferencia' },
            { data: 'porcentaje', title: '% Cambio' },
        ];
    } else {
        // Formato detallado de /api/history/compare
        (data.changes || []).forEach(c => {
            rows.push({
                symbol: c.symbol,
                old_price: c.old.price,
                new_price: c.new.price,
                variation: c.new.variation,
                type: 'cambio',
                diferencia: c.abs_diff,
                porcentaje: c.pct_diff,
            });
        });
        (data.new || []).forEach(n => {
            rows.push({
                symbol: n.symbol,
                old_price: '',
                new_price: n.price,
                variation: n.variation,
                type: 'nueva',
                diferencia: null,
                porcentaje: null,
            });
        });
        (data.removed || []).forEach(r => {
            rows.push({
                symbol: r.symbol,
                old_price: r.price,
                new_price: '',
                variation: r.variation,
                type: 'eliminada',
                diferencia: null,
                porcentaje: null,
            });
        });
        (data.errors || []).forEach(e => {
            rows.push({
                symbol: e.symbol,
                old_price: '',
                new_price: '',
                variation: '',
                type: 'error',
                diferencia: null,
                porcentaje: null,
            });
        });
        (data.unchanged || []).forEach(u => {
            rows.push({
                symbol: u.symbol,
                old_price: u.price,
                new_price: u.price,
                variation: u.variation,
                type: 'sin_cambios',
                diferencia: null,
                porcentaje: null,
            });
        });

        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex, rowData) {
            if (settings.nTable.id !== 'comparisonTable') return true;
            if (!rowData.type) return true;
            const showChanges = document.getElementById('filterChanges').checked;
            const showNew = document.getElementById('filterNew').checked;
            const showRemoved = document.getElementById('filterRemoved').checked;
            const showErrors = document.getElementById('filterErrors').checked;
            const showUnchanged = document.getElementById('filterUnchanged').checked;
            if (rowData.type === 'cambio' && !showChanges) return false;
            if (rowData.type === 'nueva' && !showNew) return false;
            if (rowData.type === 'eliminada' && !showRemoved) return false;
            if (rowData.type === 'error' && !showErrors) return false;
            if (rowData.type === 'sin_cambios' && !showUnchanged) return false;
            return true;
        });

        columns = [
            { data: 'symbol', title: 'Símbolo' },
            { data: 'old_price', title: 'Precio Anterior' },
            { data: 'new_price', title: 'Precio Nuevo' },
            { data: 'variation', title: 'Variación' },
            { data: 'diferencia', title: 'Diferencia' },
            { data: 'porcentaje', title: '% Cambio' },
            { data: 'type', title: 'Tipo' },
        ];
    }

    window.comparisonTable = $('#comparisonTable').DataTable({
        data: rows,
        columns: columns,
        dom: 'Bfrtip',
        buttons: ['excelHtml5', 'csvHtml5'],
        createdRow: function(row, rowData) {
            if (rowData.type === 'nueva') {
                row.classList.add('table-primary');
            } else if (rowData.type === 'eliminada') {
                row.classList.add('table-secondary');
            } else if (rowData.type === 'error') {
                row.classList.add('table-warning');
            } else if (rowData.type === 'cambio') {
                if (rowData.diferencia > 0) row.classList.add('table-success');
                else if (rowData.diferencia < 0) row.classList.add('table-danger');
            }
        },
    });
}
