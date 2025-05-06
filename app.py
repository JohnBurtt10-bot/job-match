import time
import logging
import threading
from flask import jsonify, render_template_string, request
from config import (
    app, HTML_TEMPLATE, stop_event, WATERLOOWORKS_USERNAME,
    WATERLOOWORKS_PASSWORD, user_decisions, decisions_lock, MAX_DECISION_HISTORY,
    job_queue, processing_thread,
    served_job_evaluations, served_job_lock
)
from selenium_helpers import start_selenium_session, fetch_and_process_jobs
from evaluation import evaluate_job_fit
from queue import Empty

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_job')
def get_job():
    global job_queue, processing_thread, stop_event, served_job_evaluations, served_job_lock
    if not processing_thread or not processing_thread.is_alive():
         if not stop_event.is_set():
             logging.error("Processing thread is not active unexpectedly.")
             return jsonify({"message": "Error: Backend processing thread stopped."}), 500

    try:
        priority, _, job_data = job_queue.get_nowait()
        job_id = job_data.get('job_id')
        ai_evaluation = job_data.get('ai_evaluation') # Get evaluation from the job data

        logging.info(f"Serving job/message from queue (Priority: {priority}): {job_data.get('job_id', job_data.get('message'))}")

        # Store the evaluation temporarily on the backend before sending
        if job_id and ai_evaluation is not None:
            with served_job_lock:
                served_job_evaluations[job_id] = ai_evaluation
                logging.debug(f"Stored evaluation for job {job_id}. Served count: {len(served_job_evaluations)}")

        job_queue.task_done()
        if "message" in job_data and job_data["message"] == "No more jobs found.":
            stop_event.set()
        return jsonify(job_data)
    except Empty:
        if stop_event.is_set() and job_queue.empty():
            logging.info("Processing finished and queue empty.")
            return jsonify({"message": "All jobs processed."})
        else:
            logging.info("Job queue is empty, waiting for processor...")
            return jsonify({"message": "Processing jobs, please wait..."}), 202
    except Exception as e:
        logging.error(f"Error retrieving job: {e}", exc_info=True) # Added exc_info for better debugging
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

        # Log decision to file (optional, can be kept)
        log_file = "decisions.log"
        try:
            # If you need the title here, you'd have to store it along with the evaluation
            # or accept it from the frontend just for logging purposes.
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - DECISION: {decision}, JOB_ID: {job_id}\n") # Removed title for now
        except Exception as e:
            logging.error(f"Failed to log decision to file {log_file}: {e}")

        return jsonify({"status": "decision received", "decision": decision, "job_id": job_id})
    except Exception as e:
        logging.error(f"Error handling decision: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

def run_app():
    global stop_event, processing_thread
    from threading import Thread
    if start_selenium_session(WATERLOOWORKS_USERNAME, WATERLOOWORKS_PASSWORD):
        stop_event.clear()
        processing_thread = threading.Thread(target=fetch_and_process_jobs, args=(evaluate_job_fit,), daemon=True)
        processing_thread.start()
    else:
        logging.error("Failed to initialize Selenium. Job processing will not start.")
        job_queue.put((101, {"message": "Error: Failed to connect to WaterlooWorks."}))
        stop_event.set()
    logging.info("Starting Flask server on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def cleanup():
    from config import driver
    logging.info("Initiating cleanup...")
    stop_event.set()
    try:
        if processing_thread and processing_thread.is_alive():
            logging.info("Waiting for job processing thread to finish...")
            processing_thread.join(timeout=15)
            if processing_thread.is_alive():
                logging.warning("Processing thread did not terminate gracefully.")
    except Exception as e:
        logging.error(f"Error waiting for processing thread: {e}")
    if driver:
        logging.info("Quitting WebDriver...")
        try:
            driver.quit()
        except Exception as e:
            logging.error(f"Error quitting WebDriver: {e}")
    logging.info("Cleanup complete.")

if __name__ == "__main__":
    try:
        run_app()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received. Shutting down...")
    finally:
        cleanup()
