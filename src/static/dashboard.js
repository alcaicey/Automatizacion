// static/dashboard.js

document.addEventListener('DOMContentLoaded', () => {
    // --- LÓGICA PARA EL GRÁFICO SIMPLE (EXISTENTE) ---
    const symbolInput = document.getElementById('symbolInput');
    const plotBtn = document.getElementById('plotBtn');
    const singleStockStartDate = document.getElementById('singleStockStartDate');
    const singleStockEndDate = document.getElementById('singleStockEndDate');
    const singleStockGranularity = document.getElementById('singleStockGranularity');
    const priceChartCtx = document.getElementById('priceChart').getContext('2d');
    let priceChart = null;
    
    // Establecer fechas por defecto para el gráfico de una sola acción
    const s_endDate = new Date();
    const s_startDate = new Date();
    s_startDate.setDate(s_endDate.getDate() - 7);
    singleStockStartDate.value = s_startDate.toISOString().split('T')[0];
    singleStockEndDate.value = s_endDate.toISOString().split('T')[0];


    async function plotSingleStock() {
        const symbol = document.getElementById('symbolInput').value.toUpperCase();
        const startDate = document.getElementById('singleStockStartDate').value;
        const endDate = document.getElementById('singleStockEndDate').value;
        const granularity = document.getElementById('singleStockGranularity').value;
        const smaPeriod = document.getElementById('smaPeriod').value;

        if (!symbol) {
            alert('Por favor, ingrese un símbolo de acción.');
            return;
        }

        let url = `/api/stock_history/${symbol}?granularity=${granularity}`;
        if (startDate) url += `&start=${startDate}`;
        if (endDate) url += `&end=${endDate}`;
        if (smaPeriod) url += `&sma_period=${smaPeriod}`;

        try {
            const response = await fetch(url);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Error al cargar el historial');
            }

            const datasets = [{
                label: `Precio de ${symbol}`,
                data: data.map(d => ({ x: new Date(d.timestamp), y: d.price })),
                borderColor: 'rgba(75, 192, 192, 1)',
                tension: 0.1,
                borderWidth: 2,
                pointRadius: 1,
            }];

            if (smaPeriod && data.length > 0 && data[0][`sma_${smaPeriod}`] !== undefined) {
                datasets.push({
                    label: `SMA(${smaPeriod}) de ${symbol}`,
                    data: data.map(d => ({ x: new Date(d.timestamp), y: d[`sma_${smaPeriod}`] })),
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 2,
                    pointRadius: 0, // No mostrar puntos para la línea de SMA
                    tension: 0.1,
                });
            }

            if (priceChart) {
                priceChart.destroy();
            }

            priceChart = new Chart(priceChartCtx, {
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
                                tooltipFormat: 'dd/MM/yyyy HH:mm',
                                displayFormats: {
                                    hour: 'HH:mm',
                                    day: 'dd MMM',
                                    week: 'dd MMM yyyy'
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error("Error al graficar:", error);
            alert(error.message);
        }
    }

    plotBtn.addEventListener('click', plotSingleStock);

    const socket = io();
    socket.on('new_data', () => {
        // Solo refresca si ya hay un gráfico visible.
        if (priceChart && symbolInput.value.trim()) {
            plotSingleStock();
        }
    });

    // --- LÓGICA PARA GRÁFICO COMPARATIVO ---

    const stockSelector = document.getElementById('stockSelector');
    const metricSelector = document.getElementById('metricSelector');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const granularitySelector = document.getElementById('granularitySelector');
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
            
            // Rellenar el input del gráfico superior con la primera acción
            if (stockSelector.options.length > 0 && stockSelector.options[0].value) {
                symbolInput.value = stockSelector.options[0].value;
            }

            // Establecer fechas por defecto (últimos 30 días)
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(endDate.getDate() - 30);
            
            // Formato YYYY-MM-DD
            startDateInput.value = startDate.toISOString().split('T')[0];
            endDateInput.value = endDate.toISOString().split('T')[0];

        } catch (error) {
            console.error("Error al inicializar controles:", error);
        }
    }

    async function plotComparisonChart() {
        const selectedStocks = Array.from(stockSelector.selectedOptions).map(opt => opt.value);
        const selectedMetric = metricSelector.value;
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        const granularity = granularitySelector.value;

        if (selectedStocks.length === 0) {
            if (comparisonChart) {
                comparisonChart.destroy();
                comparisonChart = null;
            }
            return;
        }
        
        if (!startDate || !endDate) {
            alert('Por favor, seleccione una fecha de inicio y de fin.');
            return;
        }

        try {
            const params = new URLSearchParams();
            selectedStocks.forEach(stock => params.append('stock', stock));
            params.append('metric', selectedMetric);
            params.append('start_date', startDate);
            params.append('end_date', endDate);
            params.append('granularity', granularity);

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