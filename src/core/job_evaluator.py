import logging
import time
import threading
import asyncio
from src.utils.evaluate_decision_history import evaluate_decision_history
from src.utils.config import (
    job_queue, stop_event,
    user_info, user_decisions, decisions_lock, all_job_details,
    apply_to_job_queue, served_job_lock, served_job_evaluations
)
from src.utils.evaluation_parser import remove_score_salary_category, extract_score_salary_category
from src.core import evaluation

def start_ai_evaluation_worker(jobs, username):
    """Start a worker thread to handle AI evaluations."""
    def run():
        asyncio.run(ai_evaluation_worker_async(jobs, username))
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread

async def ai_evaluation_worker_async(jobs, username):
    """Async worker that processes jobs for AI evaluation."""
    import itertools
    job_counter_local = itertools.count(1000)
    
    for job_id, job in jobs.items():
        if username in stop_event and stop_event[username].is_set():
            logging.info(f"Stopping AI evaluation worker for user {username}")
            return
            
        while job_queue[username].full() and not stop_event[username].is_set():
            await asyncio.sleep(0.1)
            
        try:
            await asyncio.to_thread(evaluate_job_fit, job_id, job, job_counter_local, username)
        except Exception as e:
            logging.error(f"Error evaluating job {job_id}: {e}", exc_info=True)
            # Queue the job with error message
            job_data = {
                'job_id': job_id,
                'job_details': job,
                'ai_evaluation': f"Error: {e}"
            }
            try:
                job_queue[username].put((0, next(job_counter_local), job_data))
            except Exception as queue_error:
                logging.error(f"Error queueing job {job_id}: {queue_error}")

def evaluate_job_fit(id, job, job_counter_local, username):
    # Use per-user lock and decisions
    with decisions_lock[username]:
        # Skip if job is already in user's decisions
        if any(decision.get('job_id') == id for decision in user_decisions[username]):
            logging.info(f"Job '{job.get('title', 'N/A')}' (ID: {id}) already shown to user, skipping.")
            return

        current_decision_history = list(user_decisions[username])

        if len(current_decision_history) > 3:
            decision_history_evaluation = evaluate_decision_history(current_decision_history)
        else:
            decision_history_evaluation = ""

        # First evaluation attempt
        try:
            ai_evaluation_with_score = evaluation.evaluate_job_fit(job, user_info, decision_history_evaluation)
            score, salary, category = extract_score_salary_category(ai_evaluation_with_score)
        except Exception as e:
            logging.error(f"Initial evaluation failed for job {id}: {e}", exc_info=True)
            score, salary, category = None, None, None
        
        # If score is None, try re-evaluating up to 3 times with delays
        retry_count = 0
        while score is None and retry_count < 3:
            retry_count += 1
            delay = retry_count * 2  # Exponential backoff: 2s, 4s, 6s
            logging.warning(f"Received None score for job {id}, attempt {retry_count} of 3. Waiting {delay}s before retry...")
            time.sleep(delay)
            
            try:
                ai_evaluation_with_score = evaluation.evaluate_job_fit(job, user_info, decision_history_evaluation)
                score, salary, category = extract_score_salary_category(ai_evaluation_with_score)
                if score is not None:
                    logging.info(f"Successfully evaluated job {id} on retry {retry_count}")
            except Exception as e:
                logging.error(f"Retry {retry_count} failed for job {id}: {e}", exc_info=True)
                score, salary, category = None, None, None
        
        # If still None after retries, log and skip the job
        if score is None:
            logging.error(f"Failed to get valid score for job {id} after {retry_count} retries. Skipping job.")
            return  # Skip this job entirely instead of using default score
        
        priority = 100 - score
        job['salary'] = salary
        job['category'] = category
        all_job_details[username][id] = job

        ai_evaluation_for_user = remove_score_salary_category(ai_evaluation_with_score)

        job_data_to_queue = {
            "job_id": id,
            "job_details": job,
            "ai_evaluation": ai_evaluation_for_user,
        }
        job_cnt = next(job_counter_local)
        job_queue[username].put((priority, job_cnt, job_data_to_queue))
        logging.info(f"Job '{job.get('title', 'N/A')}' (ID: {id}) added to queue with priority {priority}. Evaluation for user will not show score. Queue size: {job_queue[username].qsize()}") 