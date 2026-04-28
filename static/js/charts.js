function weeklyBarChart(labels, data, threshold) {
    const ctx = document.getElementById('weeklyChart');
    if (!ctx) return;
    
    // Highlight the last bar (today)
    const backgroundColors = data.map((_, index) => {
        return index === data.length - 1 ? '#185FA5' : '#378ADD';
    });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Water Usage (L)',
                data: data,
                backgroundColor: backgroundColors,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y + ' L';
                        }
                    }
                },
                annotation: {
                    annotations: {
                        line1: {
                            type: 'line',
                            yMin: threshold,
                            yMax: threshold,
                            borderColor: '#EF4444',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {
                                display: true,
                                content: 'Threshold',
                                position: 'end'
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Litres'
                    }
                }
            }
        }
    });
}

function predictionLineChart(labels, data, threshold) {
    const ctx = document.getElementById('predictionChart');
    if (!ctx) return;

    // Hide spinner
    const spinner = document.getElementById('predictionSpinner');
    if (spinner) spinner.style.display = 'none';

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Predicted Usage (L)',
                data: data,
                borderColor: '#378ADD',
                backgroundColor: 'rgba(55,138,221,0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y.toFixed(1) + ' L';
                        }
                    }
                },
                annotation: {
                    annotations: {
                        line1: {
                            type: 'line',
                            yMin: threshold,
                            yMax: threshold,
                            borderColor: '#EF4444',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {
                                display: true,
                                content: 'Your Threshold',
                                position: 'end'
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Litres'
                    }
                }
            }
        }
    });
}
