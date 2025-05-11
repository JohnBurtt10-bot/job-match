import time
import logging
import threading
from flask import jsonify, render_template_string, request, session, redirect, url_for
from config import (
    app, HTML_TEMPLATE, stop_event, user_decisions, decisions_lock, MAX_DECISION_HISTORY,
    job_queue, processing_thread, apply_to_job_queue,   # ADDED apply_to_job_queue
    served_job_evaluations, served_job_lock, all_job_details
)
from evaluation import evaluate_job_fit
from queue import Empty, Queue
from playwright_job_parser import duo_code_queue
from threading import Thread
import asyncio
from playwright_job_parser import main as playwright_main

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

# Add secret key for session management
app.secret_key = "your_secret_key_here"  # Replace with a secure random key

# Temporary in-memory store for login state (for demo; use session/db in prod)
login_states = {}

# Add after other global variables
playwright_queue = Queue()  # Queue for new users to be processed by Playwright
playwright_thread = None

@app.route('/')
def index():
    # Show login page if not logged in
    if not session.get("logged_in"):
        return render_template_string("""
        <html>
        <head>
            <title>Login - WaterlooWorks Job Parser</title>
            <style>
                body { font-family: Arial, sans-serif; background: #f4f6fa; }
                .login-container {
                    background: #fff;
                    max-width: 350px;
                    margin: 80px auto;
                    padding: 32px 28px 24px 28px;
                    border-radius: 10px;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
                }
                h2 { text-align: center; color: #2a3b5d; }
                input[type=text], input[type=password] {
                    width: 100%;
                    padding: 10px;
                    margin: 8px 0 16px 0;
                    border: 1px solid #cfd8dc;
                    border-radius: 5px;
                    box-sizing: border-box;
                }
                button {
                    width: 100%;
                    background: #1976d2;
                    color: white;
                    padding: 10px;
                    border: none;
                    border-radius: 5px;
                    font-size: 16px;
                    cursor: pointer;
                }
                button:disabled { background: #90caf9; }
                .error { color: #d32f2f; text-align: center; margin-bottom: 10px; }
                .duo-code { font-size: 22px; color: #1976d2; margin: 12px 0; }
            </style>
        </head>
        <body>
            <div class="login-container">
                <h2>WaterlooWorks Login</h2>
                <div id="error" class="error"></div>
                <form id="loginForm">
                    <input name="username" id="username" placeholder="Username" required>
                    <input name="password" id="password" type="password" placeholder="Password" required>
                    <button id="loginBtn" type="submit">Login</button>
                </form>
                <div id="waitSection" style="display:none; text-align:center; margin-top:24px;">
                    <div>Logging in... Please complete DUO on your phone if prompted.</div>
                    <div id="waitSpinner" style="font-size:32px; margin:16px 0;">⏳</div>
                    <div id="duoCode" class="duo-code"></div>
                </div>
            </div>
            <script>
                const loginForm = document.getElementById('loginForm');
                const waitSection = document.getElementById('waitSection');
                const errorDiv = document.getElementById('error');
                const duoCodeDiv = document.getElementById('duoCode');
                let loginPolling = null;
                let duoPolling = null;

                loginForm.onsubmit = function(e) {
                    e.preventDefault();
                    errorDiv.textContent = "";
                    document.getElementById('loginBtn').disabled = true;
                    fetch('/login', {
                        method: 'POST',
                        body: new FormData(loginForm)
                    }).then(resp => resp.json())
                    .then(data => {
                        if (!data) return;
                        if (data.status === "error") {
                            errorDiv.textContent = data.message || "Login failed.";
                            document.getElementById('loginBtn').disabled = false;
                        } else {
                            loginForm.style.display = "none";
                            waitSection.style.display = "";
                            pollLoginStatus();
                            pollDuoCode();
                        }
                    }).catch(() => {
                        errorDiv.textContent = "Login failed.";
                        document.getElementById('loginBtn').disabled = false;
                    });
                };

                function pollLoginStatus() {
                    loginPolling = setInterval(() => {
                        fetch('/login_status').then(resp => resp.json())
                        .then(data => {
                            if (data && data.status === "ready") {
                                clearInterval(loginPolling);
                                clearInterval(duoPolling);
                                window.location = "/";
                            }
                        });
                    }, 1500);
                }

                function pollDuoCode() {
                    duoCodeDiv.textContent = "";
                    duoPolling = setInterval(() => {
                        fetch('/duo_code').then(resp => {
                            if (resp.status === 200) {
                                return resp.json();
                            }
                        }).then(data => {
                            if (data && data.duo_code) {
                                duoCodeDiv.textContent = "DUO Code: " + data.duo_code;
                                // keep polling in case code changes
                            }
                        });
                    }, 1500);
                }
            </script>
        </body>
        </html>
        """)
    
    # If user is logged in but not in login_states, start their Playwright process
    username = session.get("username")
    password = session.get("password")
    if username and password and username not in login_states:
        login_states[username] = {"ready": False}
        playwright_queue.put((username, password))
    
    return render_template_string(HTML_TEMPLATE)

def start_playwright_worker():
    def run():
        while True:
            try:
                username, password = playwright_queue.get()
                asyncio.run(playwright_main(username, password, login_states))
                playwright_queue.task_done()
            except Exception as e:
                logging.error(f"Error in Playwright worker: {e}", exc_info=True)
                continue

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    if not username or not password:
        return jsonify({"status": "error", "message": "Missing credentials"}), 400

    session["logged_in"] = True
    session["username"] = username
    session["password"] = password

    # Mark login as not ready yet
    login_states[username] = {"ready": False}

    # Add user to Playwright queue
    playwright_queue.put((username, password))

    return jsonify({"status": "ok"})

@app.route('/login_status')
def login_status():
    username = session.get("username")
    print(f"Login status check for {username}: {login_states.get(username)}")
    if not username or username not in login_states:
        return jsonify({"status": "not_logged_in"})
    if login_states[username].get("ready"):
        return jsonify({"status": "ready"})
    return jsonify({"status": "waiting"})

@app.route('/duo', methods=['POST'])
def duo():
    duo_code = request.json.get("duo_code")
    username = session.get("username")
    if not username or not duo_code:
        return jsonify({"status": "error", "message": "Missing DUO code or not logged in"}), 400

    # Continue playwright login with DUO code (pseudo-code)
    try:
        # playwright_submit_duo_code(username, duo_code)
        login_states[username]["duo_pending"] = False
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "success"})

@app.route('/duo_code')
def get_duo_code():
    try:
        code = duo_code_queue.get_nowait()
        return jsonify({"duo_code": code})
    except Exception:
        return jsonify({"duo_code": None}), 204

@app.route('/get_job')
def get_job():
    username = session.get("username")
    if not username:
        return jsonify({"message": "Not logged in"}), 401

    if username not in job_queue:
        return jsonify({"message": "No job queue found for user"}), 404

    try:
        priority, _, job_data = job_queue[username].get_nowait()
        job_id = job_data.get('job_id')
        ai_evaluation = job_data.get('ai_evaluation') # Get evaluation from the job data

        logging.info(f"Serving job/message from queue (Priority: {priority}): {job_data.get('job_id', job_data.get('message'))}")

        # Store the evaluation temporarily on the backend before sending
        if job_id and ai_evaluation is not None:
            with served_job_lock:
                served_job_evaluations[job_id] = ai_evaluation
                logging.debug(f"Stored evaluation for job {job_id}. Served count: {len(served_job_evaluations)}")

        job_queue[username].task_done()
        if "message" in job_data and job_data["message"] == "No more jobs found.":
            stop_event[username].set()
        return jsonify(job_data)
    except Empty:
        if stop_event[username].is_set() and job_queue[username].empty():
            logging.info("Processing finished and queue empty.")
            return jsonify({"message": "All jobs processed."})
        else:
            logging.info("Job queue is empty, waiting for processor...")
            return jsonify({"message": "Processing jobs, please wait..."}), 202
    except Exception as e:
        logging.error(f"Error retrieving job: {e}", exc_info=True)
        return jsonify({"message": "Internal server error"}), 500

@app.route('/decision', methods=['POST'])
def handle_decision():
    global user_decisions, decisions_lock, MAX_DECISION_HISTORY, served_job_evaluations, served_job_lock
    try:
        data = request.json
        decision = data.get('decision')
        job_id = data.get('job_id')

        if not job_id:
            logging.warning("Received decision request without job_id.")
            return jsonify({"status": "error", "message": "Missing job_id"}), 400

        logging.info(f"Received decision: {decision} for job ID: {job_id}")

        # Retrieve the stored AI evaluation for this job_id
        retrieved_evaluation = None
        with served_job_lock:
            retrieved_evaluation = served_job_evaluations.pop(job_id, None) # Use pop to remove after retrieval

        if retrieved_evaluation is None:
            logging.warning(f"Could not find stored evaluation for job ID: {job_id}. Decision might be duplicate or job not served.")
            # Decide how to handle this - maybe still log decision to file?
        else:
            logging.debug(f"Retrieved stored evaluation for job {job_id}.")
            # Store decision and the retrieved AI evaluation for profile update
            with decisions_lock:
                decision_info = {
                    'decision': decision,
                    'job_id': job_id,
                    # 'job_title': job_title, # Need to store/retrieve this too if needed
                    'evaluation_shown': retrieved_evaluation # Store the retrieved evaluation
                }
                user_decisions.append(decision_info)
                if len(user_decisions) > MAX_DECISION_HISTORY:
                    user_decisions.pop(0)
                logging.debug(f"Stored decision with retrieved AI evaluation. History size: {len(user_decisions)}")

        if decision == "accept":
            apply_to_job_queue.put(job_id)

        # Log decision to file (optional, can be kept)
        log_file = "decisions.log"
        try:
            # If you need the title here, you'd have to store it along with the evaluation
            # or accept it from the frontend just for logging purposes.
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - DECISION: {decision}, JOB_ID: {job_id}\n")
        except Exception as e:
            logging.error(f"Failed to log decision to file {log_file}: {e}")

        return jsonify({"status": "decision received", "decision": decision, "job_id": job_id})
    except Exception as e:
        logging.error(f"Error handling decision: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/accepted_jobs')
def accepted_jobs():
    accepted = []
    for decision in user_decisions:
        if decision.get('decision') == 'accept':
            job_details = all_job_details.get(decision['job_id'], {})
            # Use new location fields if available
            if "Job - City:" in job_details and "Job - Province/State:" in job_details and "Job - Country:" in job_details:
                loc = f"{job_details['Job - City:']}, {job_details['Job - Province/State:']}, {job_details['Job - Country:']}"
            else:
                # fallback to previous location field if defined
                loc = job_details.get("Location", "")
            if loc:
                accepted.append({'location': loc, 'salary': job_details.get('salary', 'N/A'), 'category': job_details.get('category', 'N/A')})
    return jsonify(accepted)

def run_app():
    global playwright_thread
    logging.info("Starting Flask server on http://127.0.0.1:5000")
    
    # Start Playwright worker thread
    playwright_thread = start_playwright_worker()
    
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def cleanup():
    logging.info("Initiating cleanup...")
    if playwright_thread and playwright_thread.is_alive():
        logging.info("Waiting for Playwright worker thread to finish...")
        playwright_thread.join(timeout=15)
        if playwright_thread.is_alive():
            logging.warning("Playwright worker thread did not terminate gracefully.")
    logging.info("Cleanup complete.")

if __name__ == "__main__":
    try:
        run_app()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received. Shutting down...")
    finally:
        cleanup()
