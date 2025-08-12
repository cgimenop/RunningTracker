function formatSecondsToHMS(seconds) {
    seconds = Number(seconds);
    if (isNaN(seconds)) return seconds;
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return [
        h.toString().padStart(2, '0'),
        m.toString().padStart(2, '0'),
        s.toString().padStart(2, '0')
    ].join(':');
}

document.addEventListener("DOMContentLoaded", function () {
    // Prepare chart data from Jinja context
    const groupedData = window.groupedData || {};
    const datasets = [];
    Object.entries(groupedData).forEach(([source, laps]) => {
        // Compute cumulative distance for each lap
        let cumDist = 0;
        const data = [];
        laps = laps.filter(l => l.LapDistance_m && l.LapTotalTime_s)
                   .sort((a, b) => parseInt(a.LapNumber) - parseInt(b.LapNumber));
        laps.forEach(lap => {
            cumDist += parseFloat(lap.LapDistance_m);
            data.push({
                x: cumDist,
                y: parseFloat(lap.LapTotalTime_s)
            });
        });
        datasets.push({
            label: source,
            data: data,
            fill: false,
            borderColor: '#' + Math.floor(Math.random()*16777215).toString(16),
            tension: 0.2
        });
    });

    const ctx = document.getElementById('lapChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Total Run Distance vs. Lap Time (HH:mm:ss)'
                },
                legend: {
                    display: true
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const x = context.parsed.x;
                            const y = context.parsed.y;
                            return `Total Distance: ${x} m, Time: ${formatSecondsToHMS(y)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Total Run Distance (m)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Lap Time (HH:mm:ss)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatSecondsToHMS(value);
                        }
                    }
                }
            }
        }
    });
});