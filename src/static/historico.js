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
    const rows = [];
    (data.changes || []).forEach(c => {
        rows.push({
            symbol: c.symbol,
            old_price: c.old.price,
            new_price: c.new.price,
            variation: c.new.variation,
            type: 'cambio',
            delta: c.abs_diff,
            pct: c.pct_diff
        });
    });
    (data.new || []).forEach(n => {
        rows.push({
            symbol: n.symbol,
            old_price: '',
            new_price: n.price,
            variation: n.variation,
            type: 'nueva'
        });
    });
    (data.removed || []).forEach(r => {
        rows.push({
            symbol: r.symbol,
            old_price: r.price,
            new_price: '',
            variation: r.variation,
            type: 'eliminada'
        });
    });
    (data.errors || []).forEach(e => {
        rows.push({
            symbol: e.symbol,
            old_price: '',
            new_price: '',
            variation: '',
            type: 'error'
        });
    });
    (data.unchanged || []).forEach(u => {
        rows.push({
            symbol: u.symbol,
            old_price: u.price,
            new_price: u.price,
            variation: u.variation,
            type: 'sin_cambios'
        });
    });

    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex, rowData) {
        if (settings.nTable.id !== 'comparisonTable') return true;
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

    window.comparisonTable = $('#comparisonTable').DataTable({
        data: rows,
        columns: [
            { data: 'symbol' },
            { data: 'old_price' },
            { data: 'new_price' },
            { data: 'variation' },
            { data: 'delta' },
            { data: 'pct' },
            { data: 'type' }
        ],
        dom: 'Bfrtip',
        buttons: ['excelHtml5', 'csvHtml5'],
        createdRow: function(row, data) {
            if (data.type === 'nueva') {
                row.classList.add('table-primary');
            } else if (data.type === 'eliminada') {
                row.classList.add('table-secondary');
            } else if (data.type === 'error') {
                row.classList.add('table-warning');
            } else if (data.type === 'cambio') {
                if (data.delta > 0) row.classList.add('table-success');
                else if (data.delta < 0) row.classList.add('table-danger');
            }
        }
    });
}
