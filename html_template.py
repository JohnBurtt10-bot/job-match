# --- HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Job Swiper</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background-color: #f4f4f4; margin: 0; padding: 10px; box-sizing: border-box; }
        .job-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; width: 95%; max-width: 600px; display: flex; flex-direction: column; }
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
        @media (max-width: 600px) {
            .buttons button { padding: 10px 15px; font-size: 14px; }
        }
    </style>
</head>
<body>
    <div class="job-card">
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
                jobTitleH2.textContent = escapeHtml(data.job_details['Job Title'] || 'Job Details'); // Update title
                let detailsHtml = '';

                // Display AI Evaluation First (if available)
                if (data.ai_evaluation) {
                    // detailsHtml += '<h3>AI Fit Analysis:</h3>';
                    // Use <pre> for better formatting of the AI output which might have line breaks
                    detailsHtml += `<pre>${escapeHtml(data.ai_evaluation)}</pre>`;
                    detailsHtml += '<hr>'; // Add a separator
                }

                // Display Original Job Details
                // detailsHtml += '<h3>Original Job Details:</h3>';
                // for (const [key, value] of Object.entries(data.job_details)) {
                //    detailsHtml += `<p><strong>${escapeHtml(key)}:</strong> ${escapeHtml(value)}</p>`;
                // }

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
                    // Handle specific status codes if needed (like 202 Accepted)
                    if (response.status === 202) {
                         const data = await response.json();
                         displayJob(data); // Display "Processing..." message
                         // Optionally poll again after a delay
                         setTimeout(fetchJob, 3000); // Retry after 3 seconds
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

            // Optional: Send decision to backend
            try {
                await fetch('/decision', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ decision: decision, job_id: currentJobData.job_id, job_details: currentJobData.job_details }) // Send job identifier and details
                });
            } catch (error) {
                console.error('Error sending decision:', error);
                // Decide if you want to proceed to next job even if decision sending fails
            }

            // Fetch the next job
            fetchJob();
        }

        // Fetch the first job on page load
        window.onload = fetchJob;
    </script>
</body>
</html>
"""