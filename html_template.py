# --- HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Job Swiper</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background-color: #f4f4f4; margin: 0; padding: 10px; box-sizing: border-box; }
        .job-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; width: 95%; max-width: 1100px; display: flex; flex-direction: column; }
        h2 { margin-top: 0; }
        .job-details { margin-bottom: 20px; text-align: left; max-height: 60vh; overflow-y: auto; border: 1px solid #eee; padding: 10px; background-color: #fdfdfd; }
        .job-details p { margin: 5px 0; }
        .job-details strong { color: #333; }
        .buttons { margin-top: auto; padding-top: 15px; display: flex; justify-content: space-around; }
        .buttons button { padding: 12px 25px; font-size: 16px; cursor: pointer; border: none; border-radius: 5px; transition: background-color 0.2s ease; }
        .accept { background-color: #4CAF50; color: white; }
        .accept:hover { background-color: #45a049; }
        .reject { background-color: #f44336; color: white; }
        .reject:hover { background-color: #da190b; }
        .loading { color: #777; }
        pre { white-space: pre-wrap; word-wrap: break-word; font-size: 0.9em; }
        /* Basic responsiveness */
        @media (max-width: 900px) {
            .map-stats-container { flex-direction: column; gap: 10px; }
            #stats-container, #heatmap-container { width: 100%; }
            #heatmap { height: 250px; }
        }
        @media (max-width: 600px) {
            .buttons button { padding: 10px 15px; font-size: 14px; }
            .map-stats-container { flex-direction: column; gap: 10px; }
            #stats-container, #heatmap-container { width: 100%; }
            #heatmap { height: 180px; }
        }
        /* Adjust heatmap container styling */
        #heatmap { height: 300px; width: 100%; margin-bottom: 0; }
        /* New container for map and stats side by side */
        .map-stats-container { display: flex; gap: 20px; margin-bottom: 20px; }
        #stats-container { flex: 1; min-width: 180px; max-width: 260px; display: flex; flex-direction: column; align-items: flex-start; }
        #heatmap-container { flex: 2; min-width: 200px; }
        #categoryChart { width: 100% !important; height: 150px !important; }
        /* Make chart.js label text smaller */
        .chartjs-render-monitor, .chartjs-size-monitor, #categoryChart {
            font-size: 12px !important;
        }
        /* Chart.js axis and legend labels */
        .chartjs-render-monitor text, .chartjs-render-monitor .legend, .chartjs-render-monitor .label {
            font-size: 8px !important;
        }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="job-card">
        <!-- Map and stats stacked on mobile, side by side on desktop -->
        <div class="map-stats-container">
            <div id="stats-container">
                <canvas id="categoryChart"></canvas>
            </div>
            <div id="heatmap-container">
                <div id="heatmap"></div>
            </div>
        </div>
        <h2 id="job-title">Job Details</h2>
        <div class="job-details" id="job-details">
            <p class="loading">Initializing and loading first job...</p>
        </div>
        <div class="buttons">
            <button class="reject" onclick="makeDecision('reject')" disabled>Reject</button>
            <button class="accept" onclick="makeDecision('accept')" disabled>Accept</button>
        </div>
    </div>

    <script>
        let currentJobData = null;

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

        function displayJob(data) {
            const jobDetailsDiv = document.getElementById('job-details');
            const jobTitleH2 = document.getElementById('job-title');
            const buttons = document.querySelectorAll('.buttons button');

            if (data.job_details) {
                currentJobData = data; // Store current job data
                // Add company to title if available
                let title = escapeHtml(data.job_details['title'] || 'Job Details');
                let company = data.job_details['company'] ? escapeHtml(data.job_details['company']) : '';
                if (company) {
                    jobTitleH2.textContent = `${title} @ ${company}`;
                } else {
                    jobTitleH2.textContent = title;
                }
                let detailsHtml = '';

                // Display AI Evaluation First (if available)
                if (data.ai_evaluation) {
                    detailsHtml += `<pre>${escapeHtml(data.ai_evaluation)}</pre>`;
                    detailsHtml += '<hr>';
                }

                jobDetailsDiv.innerHTML = detailsHtml;
                buttons.forEach(btn => btn.disabled = false); // Enable buttons
            } else if (data.message) {
                jobTitleH2.textContent = 'Status';
                jobDetailsDiv.innerHTML = `<p class="loading">${escapeHtml(data.message)}</p>`;
                buttons.forEach(btn => btn.disabled = true); // Disable buttons
            } else {
                 jobTitleH2.textContent = 'Error';
                 jobDetailsDiv.innerHTML = '<p class="loading">Error: Received unexpected data.</p>';
                 buttons.forEach(btn => btn.disabled = true);
            }
             // Scroll details to top
            jobDetailsDiv.scrollTop = 0;
        }

        async function fetchJob() {
            const jobDetailsDiv = document.getElementById('job-details');
            const buttons = document.querySelectorAll('.buttons button');
            jobDetailsDiv.innerHTML = '<p class="loading">Loading next job...</p>'; // Show loading state
            buttons.forEach(btn => btn.disabled = true); // Disable buttons while loading

            try {
                const response = await fetch('/get_job');
                if (!response.ok) {
                    if (response.status === 202) {
                         const data = await response.json();
                         displayJob(data);
                         setTimeout(fetchJob, 3000);
                         return;
                    }
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                displayJob(data);
            } catch (error) {
                console.error('Error fetching job:', error);
                document.getElementById('job-title').textContent = 'Error';
                jobDetailsDiv.innerHTML = '<p class="loading">Error loading job. Check console or backend logs.</p>';
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
                  // document.getElementById('avg-salary').innerText = "Average Salary: " + avgSalary.toFixed(2);
                  
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

        window.onload = fetchJob;
    </script>
</body>
</html>
"""
