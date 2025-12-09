document.addEventListener('DOMContentLoaded', () => {
    displayStats();
});

function displayStats() {
    document.title = 'Time Statistics - Developer Distractor Destroyer';

    const timeStatsList = document.getElementById('statsList');
    const timeChartCanvas = document.getElementById('timeChart').getContext('2d');
    const clearTimeStatsBtn = document.getElementById('clearTimeStats');
    const timeFilterControls = document.getElementById('timeFilterControls');
    let timeChart = null;

    const gotchaStatsList = document.getElementById('gotchaList');
    const gotchaChartCanvas = document.getElementById('gotchaChart').getContext('2d');
    const clearGotchaStatsBtn = document.getElementById('clearGotchaStats');
    const gotchaFilterControls = document.getElementById('gotchaFilterControls');
    let gotchaChart = null;

    let intervalId = null;
    let currentTimeFilter = 'day'; // Default filter
    let currentGotchaFilter = 'day'; // Default filter
    let currentTimeChartType = 'pie'; // Default chart type for time stats

    function formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    function updateStats(filterType = currentTimeFilter) {
        chrome.storage.local.get(['timeData', 'gotchaStats'], (result) => {
            // Time Stats
            timeStatsList.innerHTML = '';
            let timeData = result.timeData || {};
            let filteredTimeData = filterData(timeData, filterType);
            const sortedTimeSites = Object.entries(filteredTimeData).sort((a, b) => b[1] - a[1]);

            if (sortedTimeSites.length === 0) {
                timeStatsList.innerHTML = '<div class="stat-item">No time tracking data yet.</div>';
                document.getElementById('timeChart').style.display = 'none';
            } else {
                document.getElementById('timeChart').style.display = 'block';
                sortedTimeSites.forEach(([site, time]) => {
                    const statItem = createStatItem(site, formatTime(time), timeChart, timeStatsList);
                    timeStatsList.appendChild(statItem);
                });
                renderTimeChart(sortedTimeSites, currentTimeChartType);
            }

            // Gotcha Stats
            gotchaStatsList.innerHTML = '';
            let gotchaData = result.gotchaStats || {};
            let filteredGotchaData = filterData(gotchaData, currentGotchaFilter);
            const sortedGotchaSites = Object.entries(filteredGotchaData).sort((a, b) => b[1] - a[1]);

            if (sortedGotchaSites.length === 0) {
                gotchaStatsList.innerHTML = '<div class="stat-item">No "gotcha" data yet.</div>';
                document.getElementById('gotchaChart').style.display = 'none';
            } else {
                document.getElementById('gotchaChart').style.display = 'block';
                sortedGotchaSites.forEach(([site, count]) => {
                    const statItem = createStatItem(site, `${count} times`, gotchaChart, gotchaStatsList);
                    gotchaStatsList.appendChild(statItem);
                });
                renderGotchaChart(sortedGotchaSites, 'bar'); // Always bar chart for gotcha stats for now
            }
        });
    }

    function filterData(data, filterType) {
        const now = Date.now();
        const oneDay = 24 * 60 * 60 * 1000;
        const oneWeek = 7 * oneDay;
        const oneMonth = 30 * oneDay; // Approximation for a month

        let filtered = {};

        for (const site in data) {
            if (Array.isArray(data[site])) {
                filtered[site] = data[site].filter(entry => {
                    const entryTime = entry.timestamp || 0;
                    if (filterType === 'day') {
                        return (now - entryTime) < oneDay;
                    } else if (filterType === 'week') {
                        return (now - entryTime) < oneWeek;
                    } else if (filterType === 'month') {
                        return (now - entryTime) < oneMonth;
                    }
                    return true; // No filter, return all
                }).reduce((sum, entry) => sum + entry.time, 0);
            } else if (typeof data[site] === 'object' && data[site] !== null && 'timestamp' in data[site]) {
                // Handle objects with timestamp and value (e.g., gotchaStats might store an object {count: N, timestamp: T})
                const entryTime = data[site].timestamp || 0;
                let isValid = false;
                if (filterType === 'day') {
                    isValid = (now - entryTime) < oneDay;
                } else if (filterType === 'week') {
                    isValid = (now - entryTime) < oneWeek;
                } else if (filterType === 'month') {
                    isValid = (now - entryTime) < oneMonth;
                }

                if (isValid) {
                    filtered[site] = data[site].count; // Assuming 'count' for gotchaStats
                }
            } else {
                // If data format is just site: value (no timestamp), include all (no filtering applied)
                filtered[site] = data[site];
            }
        }
        return filtered;
    }

    function removeStatEntry(statType, siteToRemove) {
        chrome.storage.local.get([statType], (result) => {
            const stats = result[statType];
            if (stats && stats[siteToRemove]) {
                delete stats[siteToRemove];
                let dataToSet = {};
                dataToSet[statType] = stats;
                chrome.storage.local.set(dataToSet, () => {
                    updateStats();
                });
            }
        });
    }

    function createStatItem(site, value, chart, listElement) {
        const statItem = document.createElement('div');
        statItem.className = 'stat-item';
        statItem.dataset.site = site;

        if (chart) {
            const index = chart.data.labels.indexOf(site);
            if (index !== -1 && !chart.getDataVisibility(index)) {
                statItem.classList.add('disabled');
            }
        }

        const siteText = document.createElement('span');
        siteText.textContent = site;

        const valueContainer = document.createElement('div');
        valueContainer.className = 'value-container';

        const valueText = document.createElement('span');
        valueText.textContent = value;

        const deleteBtn = document.createElement('span');
        deleteBtn.className = 'delete-stat-btn';
        deleteBtn.textContent = '❌';

        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const statType = listElement.id === 'statsList' ? 'timeData' : 'gotchaStats';
            if (confirm(`Are you sure you want to delete stats for "${site}"?`)) {
                removeStatEntry(statType, site);
            }
        });

        valueContainer.appendChild(valueText);
        valueContainer.appendChild(deleteBtn);

        statItem.appendChild(siteText);
        statItem.appendChild(valueContainer);

        statItem.addEventListener('click', () => {
            if (!chart) return;
            const index = chart.data.labels.indexOf(site);
            if (index !== -1) {
                chart.toggleDataVisibility(index);
                chart.update();
                statItem.classList.toggle('disabled', !chart.getDataVisibility(index));
            }
        });

        statItem.addEventListener('mouseover', () => {
            if (!chart) return;
            const index = chart.data.labels.indexOf(site);
            if (index !== -1) {
                chart.setActiveElements([{ datasetIndex: 0, index: index }]);
                chart.update();
            }
        });

        statItem.addEventListener('mouseout', () => {
            if (!chart) return;
            chart.setActiveElements([]);
            chart.update();
        });

        return statItem;
    }

    function renderTimeChart(data, chartType) {
        const labels = data.map(item => item[0]);
        const values = data.map(item => item[1]);

        if (timeChart) {
            timeChart.destroy();
            timeChart = null;
        }

        const chartConfig = {
            data: {
                labels: labels,
                datasets: [{
                    label: chartType === 'pie' ? 'Time Spent (seconds)' : 'Time Spent',
                    data: values,
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.7)',
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(255, 206, 86, 0.7)',
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(153, 102, 255, 0.7)',
                        'rgba(255, 159, 64, 0.7)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: 'white'
                        },
                        onClick: (e, legendItem, legend) => {
                            const index = legendItem.index;
                            const ci = legend.chart;

                            ci.toggleDataVisibility(index);
                            ci.update();

                            const isVisible = ci.getDataVisibility(index);
                            const statItem = timeStatsList.querySelector(`.stat-item[data-site="${legendItem.text}"]`);
                            if (statItem) {
                                statItem.classList.toggle('disabled', !isVisible);
                            }
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                let value = context.parsed;
                                if (context.chart.config.type === 'bar') {
                                    value = context.parsed.y;
                                }
                                if (value !== null) {
                                    label += formatTime(value);
                                }
                                return label;
                            }
                        }
                    }
                }
            }
        };

        if (chartType === 'bar') {
            chartConfig.options.scales = {
                x: {
                    ticks: {
                        color: 'white'
                    }
                },
                y: {
                    ticks: {
                        color: 'white'
                    }
                }
            };
            chartConfig.options.plugins.legend.display = false;
        }

        timeChart = new Chart(timeChartCanvas, {
            type: chartType,
            ...chartConfig
        });
    }

    function renderGotchaChart(data, chartType) {
        const labels = data.map(item => item[0]);
        const values = data.map(item => item[1].count); // Access count property

        if (gotchaChart) {
            gotchaChart.destroy();
            gotchaChart = null;
        }

        gotchaChart = new Chart(gotchaChartCanvas, {
            type: chartType,
            data: {
                labels: labels,
                datasets: [{
                    label: '"Gotcha" Count',
                    data: values,
                    backgroundColor: 'rgba(255, 99, 132, 0.7)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: 'white'
                        }
                    },
                    y: {
                        ticks: {
                            color: 'white'
                        }
                    }
                }
            }
        });
    }

    clearTimeStatsBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear all time statistics? This cannot be undone.')) {
            chrome.storage.local.set({ timeData: {}, currentSessionTime: 0 }, () => {
                if (timeChart) {
                    timeChart.destroy();
                    timeChart = null;
                }
                updateStats();
            });
        }
    });

    clearGotchaStatsBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear all "gotcha" statistics? This cannot be undone.')) {
            chrome.storage.local.set({ gotchaStats: {} }, () => {
                if (gotchaChart) {
                    gotchaChart.destroy();
                    gotchaChart = null;
                }
                updateStats();
            });
        }
    });

    // Add event listeners for time filter buttons
    timeFilterControls.querySelectorAll('.filter-button').forEach(button => {
        button.addEventListener('click', () => {
            timeFilterControls.querySelector('.filter-button.active').classList.remove('active');
            button.classList.add('active');
            currentTimeFilter = button.dataset.filter;
            updateStats();
        });
    });

    // Add event listeners for time chart type buttons
    const timeChartTypeControls = document.getElementById('timeChartTypeControls');
    timeChartTypeControls.querySelectorAll('.filter-button').forEach(button => {
        button.addEventListener('click', () => {
            timeChartTypeControls.querySelector('.filter-button.active').classList.remove('active');
            button.classList.add('active');
            currentTimeChartType = button.dataset.chartType;
            updateStats();
        });
    });

    // Add event listeners for gotcha filter buttons
    gotchaFilterControls.querySelectorAll('.filter-button').forEach(button => {
        button.addEventListener('click', () => {
            gotchaFilterControls.querySelector('.filter-button.active').classList.remove('active');
            button.classList.add('active');
            currentGotchaFilter = button.dataset.filter;
            updateStats();
        });
    });

    // Initial update
    updateStats(currentTimeFilter);

    // Set up auto-refresh
    intervalId = setInterval(() => updateStats(currentTimeFilter), 5000);

    // Clean up the interval when the page is hidden
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            clearInterval(intervalId);
        } else {
            intervalId = setInterval(updateStats, 5000);
        }
    });
} 