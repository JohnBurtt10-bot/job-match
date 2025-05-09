import os
import glob
import ast
import logging
import time
from evaluation import evaluate_job_fit
from config import user_info, job_queue, decisions_lock, user_decisions, all_job_details
from itertools import count
from app import app
from selenium_helpers import extract_score_salary_category, remove_score_salary_category

logging.basicConfig(level=logging.INFO)

def main():
    # Start the hosted front-end app first in a separate thread
    import threading, requests
    def run_app():
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_app, daemon=True)
    flask_thread.start()
    time.sleep(2)  # Wait for the server to start

    TEST_DIR = r"c:\Users\johnb\OneDrive\Desktop\project\test\software"
    pattern = os.path.join(TEST_DIR, "job_details_debug*.txt")
    files = glob.glob(pattern)

    if not files:
        logging.error("No test job detail files found in %s", TEST_DIR)
        exit(1)

    dummy_counter = count(1000)

    for filepath in files:
        # if it's not the first file, wait for 10 seconds
        if filepath != files[0]:
            logging.info("Waiting for 10 seconds before processing the next file...")
            time.sleep(4)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        # Look for the line starting with "Details:"
        job_details = None
        for line in content.splitlines():
            if line.startswith("Details:"):
                details_str = line[len("Details: "):].strip()
                try:
                    job_details = ast.literal_eval(details_str)
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    all_job_details[timestamp] = job_details # Store all job details with timestamp
                except Exception as e:
                    logging.error("Error parsing details from %s: %s", filepath, e)
                break

        if not job_details:
            logging.warning("No job details found in %s", filepath)
            continue

        
        with decisions_lock: # Access decisions safely
            current_decision_history = list(user_decisions)[:10] # Limit to the last 10 decisions

        # Call the evaluation function with an empty decision history.
        ai_evaluation_with_score = evaluate_job_fit(job_details, user_info, current_decision_history)
        score, salary, category = extract_score_salary_category(ai_evaluation_with_score) # Score extracted from original
        print(f"Score: {score}, Salary: {salary}, Category: {category}")
        priority = 100 - score

        # Remove score line before putting into queue for user display and history
        ai_evaluation_for_user = remove_score_salary_category(ai_evaluation_with_score)
        job_data_to_queue = {
                    "job_id": 1,
                    "job_details": job_details,
                    "ai_evaluation": ai_evaluation_for_user # Store version without score line
                }
                
        print(f"Putting job into queue with priority {priority} and dummy counter {next(dummy_counter)}")
        job_queue.put((priority, next(dummy_counter), job_data_to_queue))

    # Test the live, hosted /get_job endpoint using requests
    # try:
    #     response = requests.get('http://127.0.0.1:5000/get_job')
    #     print("Hosted front-end /get_job response:")
    #     print(response.json())
    # except Exception as e:
    #     print(f"Error querying hosted frontend: {e}")

if __name__ == "__main__":
    main()

