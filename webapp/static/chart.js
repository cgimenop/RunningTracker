function extractDateFromFilename(filename) {
    // Extracts YYYY-MM-DD from filenames like RunnerUp_2025-08-05-08-24-01_Running.tcx
    const match = filename.match(/([0-9]{4}-[0-9]{2}-[0-9]{2})/);
    return match ? match[1] : filename;
}

document.addEventListener("DOMContentLoaded", function () {
    // Chart logic
    const groupedData = window.groupedData || {};
    const datasets = [];
    Object.entries(groupedData).forEach(([source, laps]) => {
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
            label: extractDateFromFilename(source),
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

    // --- Convert all date strings in the page to local timezone ---
    // Looks for elements with class 'local-datetime' and converts their text
    document.querySelectorAll('.local-datetime').forEach(function(el) {
        const original = el.textContent.trim();
        // Try to parse as ISO or YYYY-MM-DD or YYYY-MM-DD HH:mm:ss
        let date = null;
        if (/^\d{4}-\d{2}-\d{2}$/.test(original)) {
            // If only date, treat as local midnight
            date = new Date(original + "T00:00:00");
        } else if (!isNaN(Date.parse(original))) {
            date = new Date(original);
        }
        if (date && !isNaN(date.getTime())) {
            // Format as local string (date and time if time is not midnight)
            let formatted;
            if (date.getHours() === 0 && date.getMinutes() === 0 && date.getSeconds() === 0) {
                formatted = date.toLocaleDateString();
            } else {
                formatted = date.toLocaleString();
            }
            el.textContent = formatted;
        }
    });
});

// Helper for formatting seconds as HH:mm:ss
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