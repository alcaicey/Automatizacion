// static/dashboard.js

document.addEventListener('DOMContentLoaded', () => {
    // --- LÓGICA PARA EL GRÁFICO SIMPLE (EXISTENTE) ---
    const symbolInput = document.getElementById('symbolInput');
    const plotBtn = document.getElementById('plotBtn');
    const priceChartCtx = document.getElementById('priceChart').getContext('2d');
    let priceChart = null;

    async function plotSingleStock(symbol) {
        try {
            const res = await fetch(`/api/stocks/history/${encodeURIComponent(symbol)}`);
            if (!res.ok) throw new Error('Error al obtener datos');
            const data = await res.json();

            if (priceChart) {
                priceChart.destroy();
            }

            priceChart = new Chart(priceChartCtx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: `Precio de ${symbol}`,
                        data: data.data,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1,
                    }]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false // CORRECCIÓN: Evita que el gráfico crezca infinitamente
                }
            });
        } catch (error) {
            console.error("Error al graficar:", error);
            alert(error.message);
        }
    }

    plotBtn.addEventListener('click', () => {
        const symbol = symbolInput.value.trim().toUpperCase();
        if (symbol) plotSingleStock(symbol);
    });

    const socket = io();
    socket.on('new_data', () => {
        const symbol = symbolInput.value.trim().toUpperCase();
        if (symbol && priceChart) {
            plotSingleStock(symbol); // Refresca el gráfico si hay un símbolo activo
        }
    });

    // --- LÓGICA PARA GRÁFICO COMPARATIVO ---

    const stockSelector = document.getElementById('stockSelector');
    const metricSelector = document.getElementById('metricSelector');
    const daysSelector = document.getElementById('daysSelector');
    const plotHistoryBtn = document.getElementById('plotHistoryBtn');
    const comparisonChartCtx = document.getElementById('comparisonChart').getContext('2d');
    let comparisonChart = null;

    // Paleta de colores para los datasets
    const chartColors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#858796', '#5a5c69', '#f8f9fc', '#dddfeb', '#4e73df'
    ];

    async function initializeDashboardControls() {
        try {
            const res = await fetch('/api/filters');
            if (!res.ok) throw new Error('No se pudieron cargar los filtros');
            const filters = await res.json();
            
            if (filters.codes && filters.codes.filter(c => c).length > 0) {
                stockSelector.innerHTML = '';
                filters.codes.forEach(code => {
                    if (code) { // Asegurarse de no añadir opciones vacías
                        const option = new Option(code, code);
                        stockSelector.add(option);
                    }
                });
            } else {
                stockSelector.innerHTML = '<option disabled>No hay acciones en el filtro</option>';
            }
        } catch (error) {
            console.error("Error al inicializar controles:", error);
        }
    }

    async function plotComparisonChart() {
        const selectedStocks = Array.from(stockSelector.selectedOptions).map(opt => opt.value);
        const selectedMetric = metricSelector.value;
        const selectedDays = daysSelector.value;

        if (selectedStocks.length === 0) {
            if (comparisonChart) {
                comparisonChart.destroy();
                comparisonChart = null;
            }
            return;
        }

        try {
            const params = new URLSearchParams();
            selectedStocks.forEach(stock => params.append('stock', stock));
            params.append('metric', selectedMetric);
            params.append('days', selectedDays);

            const res = await fetch(`/api/dashboard/chart-data?${params.toString()}`);
            if (!res.ok) {
                throw new Error('El servidor respondió con un error al buscar datos del gráfico.');
            }
            const data = await res.json();

            const datasets = Object.keys(data).map((symbol, index) => ({
                label: symbol,
                data: data[symbol],
                borderColor: chartColors[index % chartColors.length],
                backgroundColor: chartColors[index % chartColors.length] + '33', // con transparencia
                fill: false,
                tension: 0.1
            }));

            if (comparisonChart) {
                comparisonChart.destroy();
            }

            comparisonChart = new Chart(comparisonChartCtx, {
                type: 'line',
                data: {
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                // CORRECCIÓN: Formatos explícitos para que el adaptador de fecha los use
                                tooltipFormat: 'dd/MM/yyyy HH:mm',
                                displayFormats: {
                                    day: 'dd MMM',
                                    week: 'dd MMM yyyy',
                                    month: 'MMM yyyy'
                                }
                            },
                            title: {
                                display: true,
                                text: 'Fecha'
                            },
                            ticks: {
                                autoSkip: true,
                                maxTicksLimit: 15 // Aumentar un poco el límite de etiquetas
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: metricSelector.options[metricSelector.selectedIndex].text
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error("Error al graficar comparación:", error);
            alert("No se pudieron cargar los datos para el gráfico comparativo.");
        }
    }

    plotHistoryBtn.addEventListener('click', plotComparisonChart);

    // Inicializar los controles al cargar la página
    initializeDashboardControls();
});