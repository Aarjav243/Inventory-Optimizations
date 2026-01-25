document.addEventListener('DOMContentLoaded', () => {
    // API URL - empty string means use relative path (same server)
    const API_BASE = '';

    // UI Elements
    const form = document.getElementById('optimizerForm');
    const storeSelect = document.getElementById('storeSelect');
    const deptSelect = document.getElementById('deptSelect');
    const serviceLevelInput = document.getElementById('serviceLevel');
    const serviceLevelDisplay = document.getElementById('serviceLevelValue');
    const apiStatus = document.getElementById('apiStatus');
    const loader = document.getElementById('loader');

    // Result displays
    const stats = {
        avgDemand: document.getElementById('avgDemand'),
        safetyStock: document.getElementById('safetyStock'),
        costSavings: document.getElementById('costSavings'),
        savingsPercent: document.getElementById('savingsPercent'),
        reorderPoint: document.getElementById('reorderPoint'),
        dailyDemand: document.getElementById('dailyDemand'),
        leadTimeDisplay: document.getElementById('leadTimeDisplay'),
        dataPoints: document.getElementById('dataPoints'),
        cov: document.getElementById('cov'),
        stdDev: document.getElementById('stdDev'),
        forecastDisplay: document.getElementById('forecastDisplay')
    };

    let forecastChart = null;
    let storeData = null;

    // Initialize - Check API and fetch stores
    checkApiStatus();
    fetchStores();

    // Event Listeners
    serviceLevelInput.addEventListener('input', (e) => {
        serviceLevelDisplay.textContent = `${Math.round(e.target.value * 100)}%`;
    });

    storeSelect.addEventListener('change', () => {
        const storeId = parseInt(storeSelect.value);
        updateDeptOptions(storeId);
    });

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        runOptimization();
    });

    // Functions
    async function checkApiStatus() {
        try {
            const response = await fetch(`${API_BASE}/health`);
            if (response.ok) {
                apiStatus.className = 'status-badge online';
                apiStatus.querySelector('.status-text').textContent = 'API Online';
            } else {
                throw new Error();
            }
        } catch (err) {
            apiStatus.className = 'status-badge offline';
            apiStatus.querySelector('.status-text').textContent = 'API Offline';
            console.error('API disconnection:', err);
        }
    }

    async function fetchStores() {
        try {
            const response = await fetch(`${API_BASE}/stores`);
            const data = await response.json();
            storeData = data;

            // Populate store dropdown
            storeSelect.innerHTML = '<option value="" disabled selected>Choose a store</option>';
            data.stores.forEach(storeId => {
                const option = document.createElement('option');
                option.value = storeId;
                option.textContent = `Store #${storeId}`;
                storeSelect.appendChild(option);
            });
        } catch (err) {
            console.error('Error fetching stores:', err);
            storeSelect.innerHTML = '<option value="" disabled>Error loading stores</option>';
        }
    }

    function updateDeptOptions(storeId) {
        if (!storeData) return;

        const depts = storeData.combinations
            .filter(c => c.Store === storeId)
            .map(c => c.Dept)
            .sort((a, b) => a - b);

        deptSelect.disabled = false;
        deptSelect.innerHTML = '<option value="" disabled selected>Choose a department</option>';
        depts.forEach(deptId => {
            const option = document.createElement('option');
            option.value = deptId;
            option.textContent = `Dept #${deptId}`;
            deptSelect.appendChild(option);
        });
    }

    async function runOptimization() {
        // Show loader
        loader.classList.remove('hidden');

        const payload = {
            store_id: parseInt(storeSelect.value),
            dept_id: parseInt(deptSelect.value),
            forecast_periods: parseInt(document.getElementById('forecastPeriods').value),
            lead_time_days: parseInt(document.getElementById('leadTime').value),
            service_level: parseFloat(serviceLevelInput.value)
        };

        try {
            const response = await fetch(`${API_BASE}/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Optimization failed');
            }

            const data = await response.json();
            displayResults(data);

        } catch (err) {
            alert(`Error: ${err.message}`);
            console.error(err);
        } finally {
            loader.classList.add('hidden');
        }
    }

    function displayResults(data) {
        // Update stats
        stats.avgDemand.textContent = formatCurrency(data.summary.avg_weekly_sales);
        stats.safetyStock.textContent = formatNumber(data.safety_stock.safety_stock) + ' Units';
        stats.costSavings.textContent = formatCurrency(data.cost_savings.reduction);
        stats.savingsPercent.textContent = `${data.cost_savings.reduction_percentage.toFixed(1)}% Reduction`;

        stats.reorderPoint.textContent = formatNumber(data.safety_stock.reorder_point) + ' Units';
        stats.dailyDemand.textContent = formatNumber(data.safety_stock.average_daily_demand) + ' Units';
        stats.leadTimeDisplay.textContent = `${data.safety_stock.lead_time_days} Days`;

        stats.dataPoints.textContent = data.summary.data_points;
        stats.cov.textContent = `${data.summary.coefficient_of_variation.toFixed(1)}%`;
        stats.stdDev.textContent = formatNumber(data.summary.std_weekly_sales) + ' Units';
        stats.forecastDisplay.textContent = data.parameters.forecast_periods;

        // Update Chart
        updateChart(data.forecast);

        // Scroll to results on mobile
        if (window.innerWidth < 1100) {
            document.querySelector('.results-panel').scrollIntoView({ behavior: 'smooth' });
        }
    }

    function updateChart(forecastData) {
        const ctx = document.getElementById('forecastChart').getContext('2d');

        if (forecastChart) {
            forecastChart.destroy();
        }

        const labels = forecastData.forecast.map((_, i) => `Wk ${i + 1}`);

        forecastChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Forecasted Demand',
                        data: forecastData.forecast,
                        borderColor: '#6366f1',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
                        fill: false,
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 4,
                        pointBackgroundColor: '#6366f1'
                    },
                    {
                        label: 'Upper Confidence Bound',
                        data: forecastData.upper_bound,
                        borderColor: 'transparent',
                        backgroundColor: 'rgba(99, 102, 241, 0.05)',
                        fill: '+1',
                        pointRadius: 0,
                        tension: 0.4
                    },
                    {
                        label: 'Lower Confidence Bound',
                        data: forecastData.lower_bound,
                        borderColor: 'transparent',
                        backgroundColor: 'rgba(99, 102, 241, 0.05)',
                        fill: false,
                        pointRadius: 0,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#94a3b8',
                            font: { family: 'Outfit' }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleFont: { family: 'Outfit', size: 14 },
                        bodyFont: { family: 'Outfit', size: 13 },
                        padding: 12,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            color: '#94a3b8',
                            callback: value => `$${value >= 1000 ? value / 1000 + 'k' : value}`
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    }
                }
            }
        });
    }

    // Helpers
    function formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            maximumFractionDigits: 0
        }).format(value);
    }

    function formatNumber(value) {
        return new Intl.NumberFormat('en-US', {
            maximumFractionDigits: 0
        }).format(value);
    }
});
