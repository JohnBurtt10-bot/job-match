# --- HTML Template ---
HTML_TEMPLATE = """
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
            padding: 1rem;
            min-height: 100vh;
            color: var(--text-color);
            line-height: 1.5;
        }

        .job-card { 
            background: var(--card-bg);
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            text-align: center;
            width: 95%;
            max-width: 1100px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
        }

        h2 { 
            margin: 0 0 1.5rem 0;
            font-size: 1.75rem;
            font-weight: 600;
            color: var(--text-color);
        }

        .job-details { 
            margin-bottom: 1.5rem;
            text-align: left;
            max-height: 60vh;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            padding: 1.25rem;
            background-color: var(--card-bg);
            border-radius: 8px;
        }

        .job-details p { 
            margin: 0.5rem 0;
        }

        .job-details strong { 
            color: var(--text-color);
            font-weight: 600;
        }

        .buttons { 
            margin-top: auto;
            padding-top: 1.5rem;
            display: flex;
            justify-content: space-around;
            gap: 1rem;
        }

        .buttons button { 
            padding: 0.875rem 1.5rem;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            border: none;
            border-radius: 8px;
            transition: all 0.2s ease;
            flex: 1;
            max-width: 200px;
        }

        .accept { 
            background-color: var(--success-color);
            color: white;
        }

        .accept:hover { 
            background-color: var(--success-hover);
            transform: translateY(-1px);
        }

        .reject { 
            background-color: var(--reject-color);
            color: white;
        }

        .reject:hover { 
            background-color: var(--reject-hover);
            transform: translateY(-1px);
        }

        .loading { 
            color: #64748b;
            font-size: 1.125rem;
        }

        pre { 
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 0.9375rem;
            font-family: 'SF Mono', 'Consolas', monospace;
            background: var(--bg-color);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }

        .error-message { 
            color: var(--error-color);
            background-color: var(--error-bg);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            border: 1px solid #ffcdd2;
            font-size: 0.9375rem;
        }

        .login-status {
            position: fixed;
            top: 1.25rem;
            right: 1.25rem;
            padding: 0.75rem 1.25rem;
            border-radius: 8px;
            font-weight: 500;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .login-status.error {
            background-color: var(--error-bg);
            color: var(--error-color);
            border: 1px solid #ffcdd2;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }

        .login-status .retry-button {
            background-color: var(--error-color);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.875rem;
            transition: background-color 0.2s;
        }

        .login-status .retry-button:hover {
            background-color: #b71c1c;
        }

        .login-status .error-message {
            flex: 1;
            margin: 0;
            padding: 0;
            background: none;
            border: none;
        }

        .login-status.success {
            background-color: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #c8e6c9;
        }

        .login-status.loading {
            background-color: #e3f2fd;
            color: #1565c0;
            border: 1px solid #bbdefb;
        }

        .map-stats-container { 
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        #stats-container { 
            flex: 1;
            min-width: 180px;
            max-width: 260px;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }

        #heatmap-container { 
            flex: 2;
            min-width: 200px;
        }

        #heatmap { 
            height: 300px;
            width: 100%;
            margin-bottom: 0;
            border-radius: 8px;
            overflow: hidden;
        }

        #categoryChart { 
            width: 100% !important;
            height: 150px !important;
        }

        .chartjs-render-monitor, .chartjs-size-monitor, #categoryChart {
            font-size: 0.75rem !important;
        }

        .chartjs-render-monitor text, .chartjs-render-monitor .legend, .chartjs-render-monitor .label {
            font-size: 0.625rem !important;
        }

        @media (max-width: 900px) {
            .map-stats-container { 
                flex-direction: column;
                gap: 1rem;
            }
            #stats-container, #heatmap-container { 
                width: 100%;
                max-width: none;
            }
            #heatmap { 
                height: 250px;
            }
        }

        @media (max-width: 600px) {
            .job-card {
                padding: 1.25rem;
            }
            .buttons button { 
                padding: 0.75rem 1rem;
                font-size: 0.9375rem;
            }
            .map-stats-container { 
                padding: 1rem;
            }
            #heatmap { 
                height: 180px;
            }
            .login-status {
                top: 0.75rem;
                right: 0.75rem;
                font-size: 0.875rem;
            }
        }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div id="login-status" class="login-status loading">Checking login status...</div>
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
        let loginCheckInterval = null;
        let loginRetryCount = 0;
        const MAX_LOGIN_RETRIES = 3;

        function updateLoginStatus() {
            fetch('/login_status')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('login-status');
                    if (data.ready) {
                        statusDiv.className = 'login-status success';
                        statusDiv.textContent = 'Logged in successfully';
                        loginRetryCount = 0; // Reset retry count on successful login
                        // Start job fetching if not already started
                        if (!window.jobFetchStarted) {
                            window.jobFetchStarted = true;
                            fetchJob();
                        }
                    } else if (data.error) {
                        statusDiv.className = 'login-status error';
                        let errorMessage = data.error;
                        
                        // Handle specific error cases
                        if (errorMessage.includes('Invalid credentials')) {
                            errorMessage = 'Invalid username or password. Please check your credentials.';
                            if (loginRetryCount < MAX_LOGIN_RETRIES) {
                                statusDiv.innerHTML = `
                                    <span class="error-message">${errorMessage}</span>
                                    <button class="retry-button" onclick="retryLogin()">Retry Login</button>
                                `;
                            } else {
                                statusDiv.innerHTML = `
                                    <span class="error-message">Too many failed attempts. Please refresh the page to try again.</span>
                                `;
                            }
                        } else if (errorMessage.includes('DUO')) {
                            errorMessage = 'DUO verification required. Please check your device.';
                            statusDiv.innerHTML = `
                                <span class="error-message">${errorMessage}</span>
                                <button class="retry-button" onclick="retryLogin()">Check DUO Status</button>
                            `;
                        } else {
                            statusDiv.innerHTML = `
                                <span class="error-message">${errorMessage}</span>
                                <button class="retry-button" onclick="retryLogin()">Retry</button>
                            `;
                        }
                        
                        // Disable job interaction
                        document.querySelectorAll('.buttons button').forEach(btn => btn.disabled = true);
                    } else {
                        statusDiv.className = 'login-status loading';
                        statusDiv.textContent = 'Checking login status...';
                    }
                })
                .catch(error => {
                    const statusDiv = document.getElementById('login-status');
                    statusDiv.className = 'login-status error';
                    statusDiv.innerHTML = `
                        <span class="error-message">Error checking login status. Please try again.</span>
                        <button class="retry-button" onclick="retryLogin()">Retry</button>
                    `;
                    console.error('Error checking login status:', error);
                });
        }

        function retryLogin() {
            loginRetryCount++;
            const statusDiv = document.getElementById('login-status');
            statusDiv.className = 'login-status loading';
            statusDiv.textContent = 'Retrying login...';
            
            // Make a request to retry login
            fetch('/retry_login', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        updateLoginStatus(); // This will show the error with retry button if needed
                    } else {
                        updateLoginStatus(); // This will check the new login status
                    }
                })
                .catch(error => {
                    console.error('Error retrying login:', error);
                    updateLoginStatus(); // This will show the error with retry button
                });
        }

        // Check login status every 2 seconds
        loginCheckInterval = setInterval(updateLoginStatus, 2000);
        updateLoginStatus(); // Initial check

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
                currentJobData = data;
                let title = escapeHtml(data.job_details['title'] || 'Job Details');
                let company = data.job_details['company'] ? escapeHtml(data.job_details['company']) : '';
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
                jobTitleH2.textContent = 'Status';
                jobDetailsDiv.innerHTML = `<p class="loading">${escapeHtml(data.message)}</p>`;
                buttons.forEach(btn => btn.disabled = true);
            } else {
                jobTitleH2.textContent = 'Error';
                jobDetailsDiv.innerHTML = '<p class="loading">Error: Received unexpected data.</p>';
                buttons.forEach(btn => btn.disabled = true);
            }
            jobDetailsDiv.scrollTop = 0;
        }

        async function fetchJob() {
            const jobDetailsDiv = document.getElementById('job-details');
            const buttons = document.querySelectorAll('.buttons button');
            jobDetailsDiv.innerHTML = '<p class="loading">Loading next job...</p>'; // Show loading state
            buttons.forEach(btn => btn.disabled = true); // Disable buttons while loading

            try {
                const response = await fetch('/get_job');
                const data = await response.json();
                
                if (!response.ok) {
                    if (response.status === 202) {
                        // If we get a 202, it means the server is still processing
                        displayJob(data);
                        setTimeout(fetchJob, 3000); // Continue polling every 3 seconds
                        return;
                    }
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                if (data.message === "All jobs processed.") {
                    // If all jobs are processed, start polling for new ones
                    jobDetailsDiv.innerHTML = '<p class="loading">Waiting for new jobs to become available...</p>';
                    setTimeout(fetchJob, 3000); // Poll every 3 seconds
                    return;
                }

                if (data.message === "Processing jobs, please wait...") {
                    // If server is still processing, continue polling
                    displayJob(data);
                    setTimeout(fetchJob, 3000); // Poll every 3 seconds
                    return;
                }

                // If we got a job, display it
                displayJob(data);
            } catch (error) {
                console.error('Error fetching job:', error);
                document.getElementById('job-title').textContent = 'Error';
                jobDetailsDiv.innerHTML = '<p class="loading">Error loading job. Retrying in 3 seconds...</p>';
                setTimeout(fetchJob, 3000); // Retry on error after 3 seconds
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

        // Modify window.onload to not automatically start fetching jobs
        window.onload = function() {
            updateLoginStatus();
            // Only start fetching jobs if login is successful
            if (document.getElementById('login-status').classList.contains('success')) {
                fetchJob();
            }
        };
    </script>
</body>
</html>
""" 