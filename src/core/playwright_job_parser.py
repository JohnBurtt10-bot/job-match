import asyncio
import threading
import queue
from playwright.async_api import async_playwright
from src.utils.config import (
    job_queue, stop_event,
    user_info, user_decisions, decisions_lock, all_job_details,
    apply_to_job_queue, served_job_lock, served_job_evaluations
)
from src.core.job_evaluator import evaluate_job_fit
from src.core.browser_utils import extract_job_details, get_total_pages, goto_jobs_page
from src.core.apply_to_job import apply_to_job
from src.core.resume_utils import get_resume_and_details
import logging
from diskcache import Cache
import os
import time

JOBS_URL = "https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm"

# Add a global queue for DUO codes
duo_code_queue = {}

def cleanup(ai_thread, apply_thread, browser, username):
    logging.info("Initiating cleanup...")
    
    if username in stop_event:
        stop_event[username].set()
    
    # Clean up threads
    if ai_thread and ai_thread.is_alive():
        ai_thread.join(timeout=5)
    if apply_thread and apply_thread.is_alive():
        apply_thread.join(timeout=5)
    
    # Clean up browser
    if browser:
        try:
            # Create a new event loop for browser cleanup
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Close all pages first
            async def close_browser():
                pages = browser.pages
                for page in pages:
                    await page.close()
                await browser.close()
            
            loop.run_until_complete(close_browser())
            loop.close()
        except Exception as e:
            logging.error(f"Error closing browser: {e}")
    
    logging.info("Cleanup complete.")

def start_ai_evaluation_worker(jobs, username):
    def run():
        asyncio.run(ai_evaluation_worker_async(jobs, username))
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread

async def ai_evaluation_worker_async(jobs, username):
    job_counter_local = iter(range(1000, 10000))  # Local job counter for this thread
    for job_id, job in jobs.items():
        while job_queue[username].full() and not stop_event[username].is_set():
            await asyncio.sleep(0.1)
        await asyncio.to_thread(evaluate_job_fit, job_id, job, job_counter_local, username)

async def main(username, password, login_states=None):
    # Check if already logged in
    if login_states is not None and username in login_states:
        current_state = login_states[username]
        if current_state.get("ready", False):
            logging.info(f"User {username} is already logged in")
            return
        elif current_state.get("error"):
            logging.info(f"User {username} has a previous login error: {current_state['error']}")
            return

    # Initialize login state
    if login_states is not None:
        login_states[username] = {
            "ready": False,
            "error": None,
            "duo_required": False
        }

    # Initialize all user-specific structures
    if username not in job_queue:
        job_queue[username] = queue.PriorityQueue(maxsize=15)
    if username not in stop_event:
        stop_event[username] = threading.Event()
    if username not in user_decisions:
        user_decisions[username] = []
    if username not in decisions_lock:
        decisions_lock[username] = threading.Lock()
    if username not in all_job_details:
        all_job_details[username] = {}
    if username not in apply_to_job_queue:
        apply_to_job_queue[username] = queue.Queue()
    if username not in served_job_lock:
        served_job_lock[username] = threading.Lock()
    if username not in served_job_evaluations:
        served_job_evaluations[username] = {}
    if username not in duo_code_queue:
        duo_code_queue[username] = queue.Queue()

    # Create base directories if they don't exist
    user_data_dir = os.path.join("user_data", username)
    job_details_dir = os.path.join("job_details", username)
    os.makedirs(user_data_dir, exist_ok=True)
    os.makedirs(job_details_dir, exist_ok=True)

    job_details_cache = Cache(os.path.join(job_details_dir, "cache"))
    browser = None
    ai_thread = None
    try:
        async with async_playwright() as p:
            # Launch browser with user-specific user data dir
            browser = await p.chromium.launch_persistent_context(user_data_dir, headless=True)
            context = browser  # Use the persistent context directly
            page = await context.new_page()
            
            # First try to access login page and check for redirection
            await page.goto("https://waterlooworks.uwaterloo.ca/waterloo.htm?action=login")
            
            # Check if we get redirected to dashboard
            try:
                await page.wait_for_url("**/myAccount/dashboard.htm", timeout=5000)
                logging.info("Already logged in - redirected to dashboard")
                if login_states is not None:
                    login_states[username] = {
                        "ready": True,
                        "error": None,
                        "duo_required": False
                    }
                
                # Get resume details since we're already logged in
                try:
                    resume_result = await get_resume_and_details(username, password, context=context)
                except Exception as resume_error:
                    logging.error(f"Error getting resume details: {resume_error}")
                
                # Skip login process and continue with job processing
                await page.goto(JOBS_URL, wait_until="load")
            except Exception:
                # If not redirected, proceed with normal login
                # Wait for username input and enter username
                await page.wait_for_selector("#userNameInput", state="visible", timeout=15000)
                await page.fill("#userNameInput", username)

                # Click next button
                await page.wait_for_selector("#nextButton", state="attached", timeout=10000)
                await page.click("#nextButton")

                # Wait for password input and enter password
                await page.wait_for_selector("#passwordInput", state="attached", timeout=100000)
                await page.fill("#passwordInput", password)

                # Click submit button
                await page.wait_for_selector("#submitButton", state="attached", timeout=10000)
                await page.click("#submitButton")

                # Check for login success or DUO verification
                try:
                    # First try to wait for DUO verification code
                    try:
                        await page.wait_for_selector("div.verification-code", state="attached", timeout=5000)
                        # If we get here, we have a DUO code
                        verification_code_el = await page.query_selector("div.verification-code")
                        verification_code = await verification_code_el.inner_text() if verification_code_el else None
                        if verification_code:
                            duo_code_queue[username].put(verification_code)
                            if login_states is not None:
                                login_states[username]["duo_required"] = True

                        # Click trust browser button
                        await page.wait_for_selector("#trust-browser-button", state="attached", timeout=15000)
                        await page.click("#trust-browser-button")
                    except Exception as duo_error:
                        # If DUO verification not found, check if we're already logged in
                        try:
                            await page.wait_for_selector("a.items.active", state="attached", timeout=3000)
                            logging.info("Login successful without DUO verification")
                            if login_states is not None:
                                login_states[username] = {
                                    "ready": True,
                                    "error": None,
                                    "duo_required": False
                                }
                        except Exception as login_error:
                            # If neither DUO nor direct login worked, credentials are invalid
                            if login_states is not None:
                                login_states[username] = {
                                    "ready": False,
                                    "error": "Invalid credentials. Please check your username and password.",
                                    "duo_required": False
                                }
                            logging.error(f"Login failed: {login_error}")
                            return

                    # If we get here, we're logged in (either through DUO or directly)
                    if login_states is not None and not login_states[username].get("ready", False):
                        login_states[username] = {
                            "ready": True,
                            "error": None,
                            "duo_required": False
                        }

                    # Get resume details after successful login
                    try:
                        resume_result = await get_resume_and_details(username, password, context=context)
                        if resume_result:
                            logging.info(f"Successfully retrieved resume details and downloaded resume to {resume_result['resume_path']}")
                        else:
                            logging.warning("Failed to retrieve resume details")
                    except Exception as resume_error:
                        logging.error(f"Error getting resume details: {resume_error}")

                except Exception as e:
                    if login_states is not None:
                        login_states[username] = {
                            "ready": False,
                            "error": f"An error occurred during login: {str(e)}",
                            "duo_required": False
                        }
                    logging.error(f"Login failed: {e}")
                    return

                # Continue with the rest of the job processing...
                await page.goto(JOBS_URL, wait_until="load")

            # Common code that runs after either successful login or already being logged in
            # Click the "My Program" button if it exists
            try:
                my_program_btn = await page.query_selector(
                    "button.btn__default.btn--info.pill:has-text('My Program')"
                )
                if my_program_btn:
                    await my_program_btn.click()
                    await page.wait_for_timeout(3000)  # Wait for the page to update
            except Exception as e:
                logging.warning(f"Could not click 'My Program' button: {e}")
        
            # Wait for job rows to load
            await page.wait_for_selector("tr")
            total_pages = await get_total_pages(page)
            total_pages = 1
            jobs = {}
            page_num = 1
            while page_num <= total_pages:
                await goto_jobs_page(page, page_num)
                await page.wait_for_selector("tr")
                # Check if total_pages has changed (e.g., due to dynamic content)
                new_total_pages = await get_total_pages(page)
                if new_total_pages != total_pages:
                    logging.info(f"Total pages changed from {total_pages} to {new_total_pages} on page {page_num}")
                    # total_pages = new_total_pages
                all_rows = await page.query_selector_all("tr")
                rows = all_rows[1:]  # skip header
                for row in rows:
                    try:
                        # scroll to the row to ensure it's in view
                        id_el = await row.query_selector("th:nth-child(1) span")
                        id = (await id_el.inner_text()).strip() if id_el else ""
                    except Exception:
                        id = None
                    if id in job_details_cache:
                        job = job_details_cache[id]
                    else:
                        job = await extract_job_details(page, row)
                        job_details_cache[id] = job
                    jobs[id] = job
                page_num += 1

            print(f"Extracted {len(jobs)} jobs")

            ai_thread = start_ai_evaluation_worker(jobs, username)

            # Start async apply-to-job worker on the main thread (not as a background task)
            try:
                await apply_to_job_worker(username, context)
            except KeyboardInterrupt:
                logging.info("KeyboardInterrupt received. Shutting down...")
            finally:
                cleanup(ai_thread, None, browser, username)

    except Exception as e:
        if login_states is not None:
            login_states[username] = {
                "ready": False,
                "error": f"An error occurred: {str(e)}",
                "duo_required": False
            }
        logging.error(f"Error in main process: {e}")
        return
    finally:
        if browser:
            cleanup(ai_thread, None, browser, username)

# Start apply-to-job thread
async def apply_to_job_worker(username, context=None):
    while not stop_event[username].is_set():
        try:
            # Use asyncio.to_thread to avoid blocking the event loop with a blocking queue
            job_id = await asyncio.to_thread(apply_to_job_queue[username].get, 2)
            await apply_to_job(job_id, username, context)
            await asyncio.to_thread(apply_to_job_queue[username].task_done)
        except Exception:
            continue

if __name__ == "__main__":
    app_thread = threading.Thread(target=run_app, daemon=True)
    app_thread.start()
    # You must pass username and password from your Flask backend/session
    # Example: asyncio.run(main(session["username"], session["password"]))
    # For now, just show the function signature change:
    # asyncio.run(main(username, password))
    pass

