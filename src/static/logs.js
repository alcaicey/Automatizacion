$(document).ready(function() {
    const table = $('#logsTable').DataTable({
        ajax: {
            url: '/api/logs',
            dataSrc: '' // La respuesta es un array de objetos JSON
        },
        columns: [
            { data: 'id', title: 'ID' },
            { data: 'timestamp', title: 'Fecha' },
            { data: 'action', title: 'Acción/Fuente' },
            { data: 'message', title: 'Mensaje' },
            {
                data: null,
                title: '',
                orderable: false,
                searchable: false,
                render: function(data, type, row) {
                    return `<button class="btn btn-sm btn-danger delete-btn" data-id="${row.id}">Borrar</button>`;
                }
            }
        ],
        order: [[1, 'desc']], // Ordenar por fecha descendente por defecto
        responsive: true,
        language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
        dom: 'frtip' // Layout simple: filtro y paginación
    });

    // Conectar el input de búsqueda personalizado con el buscador de DataTables
    $('#searchInput').on('keyup', function() {
        table.search(this.value).draw();
    });

    // Manejador de eventos delegado para los botones de borrado
    $('#logsTable tbody').on('click', '.delete-btn', async function() {
        const id = $(this).data('id');
        if (confirm(`¿Estás seguro de que quieres borrar el log con ID ${id}?`)) {
            await fetch('/api/logs/' + id, { method: 'DELETE' });
            table.ajax.reload(null, false); // Recargar datos sin resetear la paginación
        }
    });
});