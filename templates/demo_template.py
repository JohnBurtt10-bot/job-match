from index_template import HTML_TEMPLATE

# This is a direct copy of HTML_TEMPLATE with the demo disclaimer and resume info manually inserted.
DEMO_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Job Swiper</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --primary-color: #1976d2;
            --primary-hover: #1565c0;
            --error-color: #d32f2f;
            --error-bg: #ffebee;
            --text-color: #2a3b5d;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --border-color: #e2e8f0;
            --success-color: #4CAF50;
            --success-hover: #45a049;
            --reject-color: #f44336;
            --reject-hover: #da190b;
            --demo-banner-bg: #e3f2fd;
            --demo-banner-border: #bbdefb;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body { 
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-color);
            margin: 0;
            padding: 0.75rem;
            height: 100vh;
            color: var(--text-color);
            line-height: 1.4;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .demo-banner {
            background: var(--demo-banner-bg);
            border: 1px solid var(--demo-banner-border);
            padding: 0.625rem 1rem;
            border-radius: 8px;
            margin-bottom: 0.75rem;
            box-shadow: var(--shadow-sm);
            flex-shrink: 0;
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .demo-banner h2 {
            color: var(--primary-color);
            font-size: 1.125rem;
            margin: 0;
            font-weight: 600;
            white-space: nowrap;
        }

        .demo-banner-content {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem 1rem;
            align-items: center;
            flex: 1;
        }

        .demo-banner p {
            color: var(--text-color);
            font-size: 0.875rem;
            line-height: 1.3;
            margin: 0;
            display: inline;
        }

        .demo-banner p:not(:last-child)::after {
            content: "•";
            margin-left: 1rem;
            color: var(--primary-color);
        }

        .job-card { 
            background: var(--card-bg);
            padding: 0.75rem;
            border-radius: 8px;
            box-shadow: var(--shadow-lg);
            text-align: center;
            width: 95%;
            max-width: 1000px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            height: 90vh;
            overflow: hidden;
        }

        h2 { 
            margin: 0;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-color);
            flex-shrink: 0;
        }

        .map-stats-container { 
            display: flex;
            gap: 0.75rem;
            background: var(--card-bg);
            padding: 0.75rem;
            border-radius: 8px;
            box-shadow: var(--shadow-md);
            flex-shrink: 0;
            flex: 0.5;
        }

        #stats-container { 
            flex: 1;
            min-width: 200px;
            max-width: 280px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: var(--bg-color);
            padding: 0.5rem;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            min-height: 0;
            aspect-ratio: 2.4;
            max-height: 180px;
        }

        #heatmap-container { 
            flex: 1.5;
            min-width: 200px;
            background: var(--bg-color);
            padding: 0.5rem;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
        }

        #heatmap { 
            height: 100%;
            width: 100%;
            margin: 0;
            border-radius: 4px;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
            flex: 1;
        }

        #categoryChart { 
            width: 100% !important;
            height: 100% !important;
            flex: 1;
            min-height: 0;
            max-height: 160px;
            display: flex;
            align-items: center;
        }

        .chartjs-render-monitor, .chartjs-size-monitor, #categoryChart {
            font-size: 0.75rem !important;
            height: 100% !important;
            display: flex;
            align-items: center;
        }

        .chartjs-render-monitor text, .chartjs-render-monitor .legend, .chartjs-render-monitor .label {
            font-size: 0.6875rem !important;
        }

        .job-details-container {
            display: flex;
            flex-direction: column;
            flex: 0.45;
            min-height: 0;
            gap: 0.75rem;
        }

        .job-details { 
            text-align: left;
            flex: 1;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            padding: 0.75rem;
            background-color: var(--card-bg);
            border-radius: 6px;
            box-shadow: var(--shadow-sm);
            min-height: 0;
            max-height: 40vh;
        }

        .job-details p { 
            margin: 0.375rem 0;
            font-size: 0.875rem;
            line-height: 1.3;
        }

        .buttons { 
            display: flex;
            justify-content: center;
            gap: 0.75rem;
            flex-shrink: 0;
        }

        .buttons button { 
            padding: 0.625rem 1.25rem;
            font-size: 0.9375rem;
            font-weight: 500;
            cursor: pointer;
            border: none;
            border-radius: 6px;
            transition: all 0.2s ease;
            flex: 1;
            max-width: 180px;
            box-shadow: var(--shadow-md);
        }

        .accept { 
            background-color: var(--success-color);
            color: white;
        }

        .accept:hover { 
            background-color: var(--success-hover);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .reject { 
            background-color: var(--reject-color);
            color: white;
        }

        .reject:hover { 
            background-color: var(--reject-hover);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        pre { 
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 0.8125rem;
            font-family: 'SF Mono', 'Consolas', monospace;
            background: var(--bg-color);
            padding: 0.625rem;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            margin: 0.375rem 0;
            line-height: 1.3;
        }

        .error-message { 
            color: var(--error-color);
            background-color: var(--error-bg);
            padding: 0.625rem;
            border-radius: 6px;
            margin: 0.375rem 0;
            border: 1px solid #ffcdd2;
            font-size: 0.875rem;
        }

        .loading { 
            color: #64748b;
            font-size: 0.9375rem;
            text-align: center;
            padding: 0.625rem;
        }

        .no-more-jobs {
            text-align: center;
            padding: 2rem;
            background: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin: 1rem 0;
        }

        .no-more-jobs h3 {
            color: var(--primary-color);
            font-size: 1.25rem;
            margin-bottom: 0.75rem;
        }

        .no-more-jobs p {
            color: var(--text-color);
            font-size: 0.9375rem;
            margin: 0.5rem 0;
            line-height: 1.4;
        }

        @media (max-width: 900px) {
            .demo-banner {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
                padding: 0.75rem;
            }
            .demo-banner-content {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.25rem;
            }
            .demo-banner p {
                display: block;
            }
            .demo-banner p:not(:last-child)::after {
                display: none;
            }
            .job-card {
                height: 95vh;
            }
            .map-stats-container { 
                flex-direction: column;
                gap: 0.5rem;
                padding: 0.5rem;
                flex: 0.6;
            }
            #stats-container {
                aspect-ratio: 2.8;
                min-height: 140px;
                max-height: 170px;
            }
            #heatmap-container {
                min-height: 180px;
            }
            .job-details-container {
                flex: 0.4;
            }
            .job-details {
                max-height: 35vh;
            }
            #categoryChart {
                max-height: 140px;
            }
        }

        @media (max-width: 600px) {
            body {
                padding: 0.375rem;
            }
            .demo-banner {`
                padding: 0.625rem;
            }
            .job-card {
                padding: 0.5rem;
                width: 100%;
                height: 100vh;
            }
            .buttons { 
                flex-direction: column;
                gap: 0.5rem;
            }
            .buttons button { 
                max-width: none;
                padding: 0.625rem 1rem;
                font-size: 0.875rem;
            }
            .map-stats-container { 
                flex: 0.7;
            }
            #heatmap-container {
                min-height: 160px;
            }
            .job-details-container {
                flex: 0.3;
            }
            .job-details {
                max-height: 30vh;
            }
            #stats-container {
                aspect-ratio: 3;
                min-height: 120px;
                max-height: 150px;
            }
            #categoryChart {
                max-height: 120px;
            }
        }

        @media (max-width: 480px) {
            .demo-banner {
                padding: 0.625rem;
            }
            .job-card {
                padding: 0.5rem;
                width: 100%;
                height: 100vh;
            }
            .buttons { 
                flex-direction: column;
                gap: 0.5rem;
            }
            .buttons button { 
                max-width: none;
                padding: 0.625rem 1rem;
                font-size: 0.875rem;
            }
            .map-stats-container { 
                flex: 0.7;
            }
            #heatmap-container {
                min-height: 160px;
            }
            .job-details-container {
                flex: 0.3;
            }
            .job-details {
                max-height: 30vh;
            }
            #stats-container {
                aspect-ratio: 3;
                min-height: 120px;
                max-height: 150px;
            }
            #categoryChart {
                max-height: 120px;
            }
        }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <!-- DEMO DISCLAIMER BANNER -->
    <div class="demo-banner">
        <h2>✨ Demo Mode</h2>
        <div class="demo-banner-content">
            <p>Welcome to the Job Match system demo! This is a <b>sample data</b> demonstration using <b>my own (the creator's) resume</b>. <b>No real WaterlooWorks scraping is happening</b> - the AI is evaluating each job for fit using this resume, and you can swipe through jobs, accept/reject, and see a live summary of your decisions above.</p>
        </div>
    </div>
    <div class="job-card">
        <div class="map-stats-container">
            <div id="stats-container">
                <canvas id="categoryChart"></canvas>
            </div>
            <div id="heatmap-container">
                <div id="heatmap"></div>
            </div>
        </div>
        <h2 id="job-title">Job Details</h2>
        <div class="job-details-container">
            <div class="job-details" id="job-details">
                <p class="loading">Initializing and loading first job...</p>
            </div>
            <div class="buttons">
                <button class="reject" onclick="makeDecision('reject')" disabled>Reject</button>
                <button class="accept" onclick="makeDecision('accept')" disabled>Apply</button>
            </div>
        </div>
    </div>

    <script>
        let currentJobData = null;
        // Add cleanup on page unload
        window.addEventListener('beforeunload', async function(e) {
            try {
                await fetch('/demo_cleanup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
            } catch (error) {
                console.error('Error during cleanup:', error);
            }
        });

        // Add cleanup on page visibility change (for mobile browsers)
       

        function escapeHtml(unsafe) {
            if (unsafe === null || unsafe === undefined) return '';
            return unsafe
                 .toString()
                 .replace(/&/g, "&amp;")
                 .replace(/</g, "&lt;")
                 .replace(/>/g, "&gt;")
                 .replace(/"/g, "&quot;")
                 .replace(/'/g, "&#039;");
        }

        function decodeHtmlEntities(text) {
            if (!text) return '';
            const textarea = document.createElement('textarea');
            textarea.innerHTML = text;
            return textarea.value;
        }

        function displayJob(data) {
            const jobDetailsDiv = document.getElementById('job-details');
            const jobTitleH2 = document.getElementById('job-title');
            const buttons = document.querySelectorAll('.buttons button');

            if (data.job_details) {
                currentJobData = data;
                let title = decodeHtmlEntities(data.job_details['Job Title']);
                let company = data.job_details['Company'] ? decodeHtmlEntities(data.job_details['Company']) : '';
                if (company) {
                    jobTitleH2.textContent = `${title} @ ${company}`;
                } else {
                    jobTitleH2.textContent = title;
                }
                let detailsHtml = '';

                if (data.ai_evaluation) {
                    detailsHtml += `<pre>${escapeHtml(data.ai_evaluation)}</pre>`;
                    detailsHtml += '<hr>';
                }

                jobDetailsDiv.innerHTML = detailsHtml;
                buttons.forEach(btn => btn.disabled = false);
            } else if (data.message) {
                if (data.message === "All jobs processed.") {
                    jobTitleH2.textContent = 'Demo Complete';
                    jobDetailsDiv.innerHTML = `
                        <div class="no-more-jobs">
                            <h3>✨ Demo Session Complete</h3>
                            <p>You've gone through all the available demo jobs!</p>
                            <p>Feel free to refresh the page to start a new demo session, or check out the statistics below to see your decisions.</p>
                        </div>`;
                    buttons.forEach(btn => btn.disabled = true);
                } else {
                    jobTitleH2.textContent = 'Status';
                    jobDetailsDiv.innerHTML = `<p class="loading">${escapeHtml(data.message)}</p>`;
                    buttons.forEach(btn => btn.disabled = true);
                }
            } else {
                jobTitleH2.textContent = 'Error';
                jobDetailsDiv.innerHTML = '<p class="loading">Error: Received unexpected data.</p>';
                buttons.forEach(btn => btn.disabled = true);
            }
            jobDetailsDiv.scrollTop = 0;
        }

        async function fetchJob() {
            const jobDetailsDiv = document.getElementById('job-details');
            const jobTitleH2 = document.getElementById('job-title');
            const buttons = document.querySelectorAll('.buttons button');
            jobDetailsDiv.innerHTML = '<p class="loading">Loading next job...</p>';
            jobTitleH2.textContent = 'Loading...';
            buttons.forEach(btn => btn.disabled = true);

            try {
                const response = await fetch('/get_job');
                if (!response.ok) {
                    if (response.status === 202) {
                        const data = await response.json();
                        if (data.message === "All jobs processed.") {
                            displayJob(data);
                            return;
                        }
                        displayJob(data);
                        setTimeout(fetchJob, 3000);
                        return;
                    }
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                if (data.message === "All jobs processed.") {
                    displayJob(data);
                    return;
                } else if (data.message === "Processing jobs, please wait...") {
                    jobTitleH2.textContent = 'Processing...';
                    jobDetailsDiv.innerHTML = '<p class="loading">Processing jobs, please wait...</p>';
                    setTimeout(fetchJob, 3000);
                    return;
                }
                displayJob(data);
            } catch (error) {
                console.error('Error fetching job:', error);
                document.getElementById('job-title').textContent = 'Error';
                jobDetailsDiv.innerHTML = '<p class="loading">Error loading job. Retrying in 3 seconds...</p>';
                setTimeout(fetchJob, 3000);
                buttons.forEach(btn => btn.disabled = true);
            }
        }

        async function makeDecision(decision) {
            if (!currentJobData || !currentJobData.job_id) {
                console.warn("No current job data to make a decision on.");
                return;
            }
            console.log(`Decision: ${decision} for job ID: ${currentJobData.job_id}`);

            try {
                await fetch('/decision', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ decision: decision, job_id: currentJobData.job_id, job_details: currentJobData.job_details })
                });
            } catch (error) {
                console.error('Error sending decision:', error);
            }

            fetchJob();
        }

        function updateMapStats() {
            fetch('/accepted_jobs')
              .then(response => response.json())
              .then(async function(data) {
                  let aggregated = {};
                  let salarySum = 0, salaryCount = 0;
                  let categoryCounts = {};

                  for (const item of data) {
                      salarySum += parseFloat(item.salary) || 0;
                      salaryCount++;
                      categoryCounts[item.category] = (categoryCounts[item.category] || 0) + 1;

                      let loc = item.location;
                      try {
                          const response = await fetch("https://nominatim.openstreetmap.org/search?format=json&q=" + encodeURIComponent(loc));
                          const result = await response.json();
                          if (result && result[0]) {
                              let lat = parseFloat(result[0].lat);
                              let lon = parseFloat(result[0].lon);
                              let key = lat.toFixed(5) + "," + lon.toFixed(5);
                              if (aggregated[key]) {
                                  aggregated[key].count += 1;
                              } else {
                                  aggregated[key] = { lat, lon, location: loc, count: 1 };
                              }
                          }
                      } catch(e) {
                          console.error("Geocoding error for location:", loc, e);
                      }
                  }
                  let markers = [];
                  for (const key in aggregated) {
                      const { lat, lon, location, count } = aggregated[key];
                      let radius = 5 + 3 * count;
                      let popupText = escapeHtml(location) + (count > 1 ? " (x" + count + ")" : "");
                      markers.push(L.circleMarker([lat, lon], { color: 'red', radius: radius }).bindPopup(popupText));
                  }
                  if (markers.length === 0) {
                      markers.push(L.circleMarker([43.6532, -79.3832], { color: 'red', radius: 5 }).bindPopup("Default Location"));
                  }
                  
                  let avgSalary = salaryCount ? (salarySum / salaryCount) : 0;
                  
                  const ctx = document.getElementById('categoryChart').getContext('2d');
                  const labels = Object.keys(categoryCounts);
                  const counts = labels.map(k => categoryCounts[k]);
                  if(window.categoryChart && typeof window.categoryChart.update === 'function') {
                      window.categoryChart.config.data.labels = labels;
                      window.categoryChart.config.data.datasets[0].data = counts;
                      window.categoryChart.update();
                  } else {
                      window.categoryChart = new Chart(ctx, {
                          type: 'bar',
                          data: {
                              labels: labels,
                              datasets: [{
                                  data: counts,
                                  backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                  borderColor: 'rgba(75, 192, 192, 1)',
                                  borderWidth: 1,
                              }]
                          },
                          options: {
                            indexAxis: 'y',
                              plugins: {
                                  legend: { display: false }
                              },
                              scales: {
                                  x: {
                                      ticks: {
                                          stepSize: 1,
                                          font: {
                                              size: 10
                                          }
                                      }
                                  },
                                  y: {
                                      ticks: {
                                          font: {
                                              size: 10
                                          }
                                      }
                                  }
                              }
                          }
                      });
                  }
                  
                  if (!window.map) {
                      window.map = L.map('heatmap').setView([20, 0], 2);
                      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                          attribution: '&copy; OpenStreetMap contributors'
                      }).addTo(window.map);
                      window.pointsGroup = L.layerGroup(markers).addTo(window.map);
                  } else {
                      window.pointsGroup.clearLayers();
                      markers.forEach(marker => window.pointsGroup.addLayer(marker));
                  }
              })
              .catch(err => {
                  console.error("Error fetching accepted jobs:", err);
              });
        }
        setInterval(updateMapStats, 10000);
        updateMapStats();

        // In demo mode, start fetching jobs immediately on page load
        window.onload = function() {
            fetchJob();
        };
    </script>
</body>
</html>
""" 