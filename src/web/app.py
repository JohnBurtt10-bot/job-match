#!/usr/bin/env python3

import time
import logging
import threading
from flask import jsonify, render_template, request, session, redirect, url_for
from src.utils.config import (
    app, stop_event, user_decisions, decisions_lock, MAX_DECISION_HISTORY,
    job_queue, processing_thread, apply_to_job_queue,   # ADDED apply_to_job_queue
    served_job_evaluations, served_job_lock, all_job_details
)
from src.core.evaluation import evaluate_job_fit
from queue import Empty, Queue
from src.core.playwright_job_parser import duo_code_queue
from threading import Thread
import asyncio
from src.core.playwright_job_parser import main as playwright_main
import shutil
import os
from login_template import LOGIN_TEMPLATE
from index_template import HTML_TEMPLATE
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

# Add secret key for session management
app.secret_key = "your_secret_key_here"  # Replace with a secure random key

# Temporary in-memory store for login state (for demo; use session/db in prod)
login_states = {}

# Add after other global variables
playwright_queue = Queue()  # Queue for new users to be processed by Playwright
playwright_thread = None
_initialized = False

def load_user_decisions_from_logs():
    """Load user decisions from log files on startup."""
    logging.info("Loading user decisions from log files...")
    
    # Find all decision log files
    log_files = [f for f in os.listdir('.') if f.startswith('decisions_') and f.endswith('.log')]
    
    for log_file in log_files:
        username = log_file.replace('decisions_', '').replace('.log', '')
        logging.info(f"Loading decisions for user: {username}")
        
        # Initialize user's decision history if it doesn't exist
        if username not in user_decisions:
            user_decisions[username] = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # Parse the log line
                    # Format: "2024-03-14 12:34:56 - DECISION: accept/reject, JOB_ID: 12345"
                    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - DECISION: (\w+), JOB_ID: (\d+)', line.strip())
                    if match:
                        timestamp, decision, job_id = match.groups()
                        decision_info = {
                            'decision': decision,
                            'job_id': job_id,
                            'timestamp': timestamp
                        }
                        user_decisions[username].append(decision_info)
            
            # Keep only the most recent decisions up to MAX_DECISION_HISTORY
            if len(user_decisions[username]) > MAX_DECISION_HISTORY:
                user_decisions[username] = user_decisions[username][-MAX_DECISION_HISTORY:]
            
            logging.info(f"Loaded {len(user_decisions[username])} decisions for user {username}")
        except Exception as e:
            logging.error(f"Error loading decisions for user {username}: {e}")

# Load user decisions on startup
load_user_decisions_from_logs()

@app.before_request
def initialize_app():
    global playwright_thread, _initialized
    if not _initialized:
        logging.info("Initializing application...")
        # Start Playwright worker thread
        playwright_thread = start_playwright_worker()
        # Load user decisions on startup
        load_user_decisions_from_logs()
        _initialized = True

@app.route('/')
def index():
    username = session.get('username')
    
    # If no username in session or user not in login_states, clear session and redirect to login
    if username is None or username not in login_states:
        session.clear()
        return redirect(url_for('login'))
    
    return HTML_TEMPLATE

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            })
        
        # Store username in session
        session['username'] = username
        
        # Start login process
        def run_login():
            asyncio.run(playwright_main(username, password, login_states))
        
        login_thread = threading.Thread(target=run_login)
        login_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Login process started'
        })
    
    return LOGIN_TEMPLATE

@app.route('/login_status')
def check_login_status():
    username = session.get('username')
    if not username:
        return jsonify({
            'ready': False,
            'error': 'Not logged in'
        })
    
    if username not in login_states:
        return jsonify({
            'ready': False,
            'error': 'Login in progress'
        })
    
    return jsonify(login_states[username])

@app.route('/get_duo_code')
def get_duo_code():
    username = session.get('username')
    if not username:
        return jsonify({
            'success': False,
            'error': 'Not logged in'
        })
    
    try:
        # First try to get code from queue
        try:
            code = duo_code_queue[username].get_nowait()
            return jsonify({
                'success': True,
                'code': code
            })
        except:
            # If queue is empty, check login state
            if username in login_states and login_states[username].get("duo_code"):
                code = login_states[username]["duo_code"]
                return jsonify({
                    'success': True,
                    'code': code
                })
            return jsonify({
                'success': False,
                'error': 'No DUO code available'
            })
    except Exception as e:
        logging.error(f"Error getting DUO code: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

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
            with served_job_lock[username]:
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
        username = session.get('username')

        if not username:
            return jsonify({"status": "error", "message": "Not logged in"}), 401

        if not job_id:
            logging.warning("Received decision request without job_id.")
            return jsonify({"status": "error", "message": "Missing job_id"}), 400

        logging.info(f"Received decision: {decision} for job ID: {job_id} from user {username}")

        # Initialize user's decision history if it doesn't exist
        if username not in user_decisions:
            user_decisions[username] = []

        # Retrieve the stored AI evaluation for this job_id
        retrieved_evaluation = None
        with served_job_lock[username]:
            retrieved_evaluation = served_job_evaluations.pop(job_id, None)

        if retrieved_evaluation is None:
            logging.warning(f"Could not find stored evaluation for job ID: {job_id}. Decision might be duplicate or job not served.")
        else:
            logging.debug(f"Retrieved stored evaluation for job {job_id}.")
            # Store decision and the retrieved AI evaluation for profile update
            with decisions_lock[username]:
                decision_info = {
                    'decision': decision,
                    'job_id': job_id,
                    'evaluation_shown': retrieved_evaluation
                }
                user_decisions[username].append(decision_info)
                if len(user_decisions[username]) > MAX_DECISION_HISTORY:
                    user_decisions[username].pop(0)
                logging.debug(f"Stored decision with retrieved AI evaluation. History size for user {username}: {len(user_decisions[username])}")

        if decision == "accept":
            apply_to_job_queue[username].put(job_id)

        # Log decision to file
        log_file = f"decisions_{username}.log"
        try:
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
    username = session.get('username')
    if not username:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    accepted = []
    if username in user_decisions:
        for decision in user_decisions[username]:
            if decision.get('decision') == 'accept':
                job_details = all_job_details.get(decision['job_id'], {})
                # Use new location fields if available
                if "Job - City:" in job_details and "Job - Province/State:" in job_details and "Job - Country:" in job_details:
                    loc = f"{job_details['Job - City:']}, {job_details['Job - Province/State:']}, {job_details['Job - Country:']}"
                else:
                    # fallback to previous location field if defined
                    loc = job_details.get("Location", "")
                if loc:
                    accepted.append({
                        'location': loc, 
                        'salary': job_details.get('salary', 'N/A'), 
                        'category': job_details.get('category', 'N/A')
                    })
    return jsonify(accepted)

def run_app():
    return app

def cleanup():
    logging.info("Initiating cleanup...")
    
    # Stop all user processes
    for username in list(stop_event.keys()):
        stop_event[username].set()
    
    # Wait for Playwright thread to finish
    if playwright_thread and playwright_thread.is_alive():
        logging.info("Waiting for Playwright worker thread to finish...")
        playwright_thread.join(timeout=15)
        if playwright_thread.is_alive():
            logging.warning("Playwright worker thread did not terminate gracefully.")
    
    # Clear all user data
    for username in list(login_states.keys()):
        # Clear user-specific data
        if username in job_queue:
            del job_queue[username]
        if username in stop_event:
            del stop_event[username]
        if username in user_decisions:
            del user_decisions[username]
        if username in decisions_lock:
            del decisions_lock[username]
        if username in all_job_details:
            del all_job_details[username]
        if username in apply_to_job_queue:
            del apply_to_job_queue[username]
        if username in served_job_lock:
            del served_job_lock[username]
        if username in served_job_evaluations:
            del served_job_evaluations[username]
        if username in login_states:
            del login_states[username]
    
    logging.info("Cleanup complete.")
