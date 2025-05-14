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
    """Synchronous version of cleanup for use in non-async contexts.
    This should only be called from synchronous code paths."""
    logging.info("Initiating sync cleanup...")
    
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
            # Use the existing event loop if available, otherwise create a new one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            async def close_browser_async():
                try:
                    if browser:
                        pages = browser.pages
                        for page in pages:
                            await page.close()
                        await browser.close()
                except Exception as e:
                    logging.error(f"Error in close_browser_async: {e}")
            
            # Run the cleanup in a new task
            if loop.is_running():
                # If loop is running, create a task
                asyncio.create_task(close_browser_async())
            else:
                # If loop is not running, run it directly
                loop.run_until_complete(close_browser_async())
                
        except Exception as e:
            logging.error(f"Error in browser cleanup: {e}")
    
    logging.info("Sync cleanup complete.")

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
    # Clear session at the start
    
    browser = None
    ai_thread = None
    apply_thread = None
    try:
        # Check if already logged in
        if login_states is not None and username in login_states:
            current_state = login_states[username]
            if current_state.get("ready", False):
                logging.info(f"User {username} is already logged in")
                return

        # Initialize login state and user structures
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
        timestamp = int(time.time())
        user_data_dir = os.path.join("user_data", f"{username}_{timestamp}")
        job_details_dir = os.path.join("job_details", username)
        os.makedirs(user_data_dir, exist_ok=True)
        os.makedirs(job_details_dir, exist_ok=True)

        job_details_cache = Cache(os.path.join(job_details_dir, "cache"))

        # Start Playwright and browser
        async with async_playwright() as playwright:
            try:
                # Launch browser with user-specific user data dir
                browser = await playwright.chromium.launch_persistent_context(
                    user_data_dir, 
                    headless=False,
                    timeout=30000  # 30 second timeout for browser launch
                )
                context = browser  # Use the persistent context directly
                page = await context.new_page()
                
                # First try to access login page and check for redirection
                await page.goto("https://waterlooworks.uwaterloo.ca/waterloo.htm?action=login", timeout=80000)
                
                # Poll for either dashboard redirect or login form
                status = None
                start_time = time.time()
                while time.time() - start_time < 30:  # 30 second timeout
                    try:
                        # Check current URL
                        current_url = page.url
                        if '/myAccount/dashboard.htm' in current_url:
                            status = 'dashboard'
                            break
                        
                        # Check for login form
                        username_input = await page.query_selector("#userNameInput")
                        if username_input:
                            status = 'login'
                            break
                    except Exception as e:
                        logging.debug(f"Polling check error: {e}")
                    
                    await asyncio.sleep(1)  # Wait 1 second before next check

                if status == 'dashboard':
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
                    # await page.goto(JOBS_URL, wait_until="load")
                else:
                    # Need to login
                    await page.fill("#userNameInput", username)
                    await page.click("#nextButton")
                    await page.fill("#passwordInput", password)
                    await page.click("#submitButton")

                    # Poll for login status (success, DUO, or error)
                    status = None
                    start_time = time.time()
                    while time.time() - start_time < 30:  # 30 second timeout
                        try:
                            # Check current URL
                            current_url = page.url
                            if '/myAccount/dashboard.htm' in current_url or '/myAccount/co-op/coop-postings.htm' in current_url:
                                status = 'success'
                                break
                            
                            # Check for DUO verification
                            verification_code = await page.query_selector("div.verification-code")
                            if verification_code:
                                status = 'duo'
                                break
                            
                            # Check for login failure - look for error message or username input
                            error_message = await page.query_selector(".error-message, .alert-danger")
                            if error_message:
                                error_text = await error_message.inner_text()
                                if login_states is not None:
                                    login_states[username] = {
                                        "ready": False,
                                        "error": error_text.strip() or "Invalid credentials. Please check your username and password.",
                                        "duo_required": False
                                    }
                                status = 'failed'
                                break

                            # Check if we're back at login form with username input visible
                            username_input = await page.query_selector("#userNameInput")
                            if username_input and await username_input.is_visible():
                                if login_states is not None:
                                    login_states[username] = {
                                        "ready": False,
                                        "error": "Invalid credentials. Please check your username and password.",
                                        "duo_required": False
                                    }
                                status = 'failed'
                                break

                        except Exception as e:
                            logging.debug(f"Polling check error: {e}")
                        
                        await asyncio.sleep(1)  # Wait 1 second before next check

                    if status == 'failed':
                        logging.error("Login failed - Invalid credentials")
                        if browser:
                            await cleanup_async(ai_thread, apply_thread, browser, username)
                        return
                    elif status == 'success':
                        logging.info("Login successful")
                        if login_states is not None:
                            login_states[username] = {
                                "ready": True,
                                "error": None,
                                "duo_required": False
                            }
                    elif status == 'duo':
                        # Get DUO code
                        verification_code_el = await page.query_selector("div.verification-code")
                        verification_code = await verification_code_el.inner_text() if verification_code_el else None
                        if verification_code:
                            # Clear any existing codes in the queue
                            while not duo_code_queue[username].empty():
                                try:
                                    duo_code_queue[username].get_nowait()
                                except:
                                    pass
                            # Put the new code in the queue
                            duo_code_queue[username].put(verification_code)
                            logging.info(f"Put DUO code in queue for user {username}: {verification_code}")
                            if login_states is not None:
                                login_states[username]["duo_required"] = True
                                login_states[username]["duo_code"] = verification_code

                            # Try to click trust browser button if it exists, but continue either way
                            try:
                                # Start a loop to continuously check for try again button
                                start_time = time.time()
                                while time.time() - start_time < 300:  # 5 minute timeout for DUO attempts
                                    try:
                                        # Check for either trust button or retry button
                                        trust_or_retry = await page.query_selector(
                                            "#trust-browser-button, .try-again-button"
                                        )
                                        
                                        if trust_or_retry:
                                            button_class = await trust_or_retry.get_attribute("class")
                                            if "try-again-button" in button_class:
                                                logging.info("Found retry button - DUO code was incorrect")
                                                await trust_or_retry.click()
                                                if login_states is not None:
                                                    # Keep duo_required as True and update the code
                                                    login_states[username] = {
                                                        "ready": False,
                                                        "error": "Incorrect DUO code. Please try again.",
                                                        "duo_required": True,
                                                        "duo_pending": True  # Add this to indicate we're waiting for new code
                                                    }
                                                # Wait for new DUO code to appear
                                                try:
                                                    verification_code_el = await page.wait_for_selector("div.verification-code", timeout=30000)
                                                    if verification_code_el:
                                                        verification_code = await verification_code_el.inner_text()
                                                        # Clear any existing codes in the queue
                                                        while not duo_code_queue[username].empty():
                                                            try:
                                                                duo_code_queue[username].get_nowait()
                                                            except:
                                                                pass
                                                        # Put the new code in the queue
                                                        duo_code_queue[username].put(verification_code)
                                                        logging.info(f"Put new DUO code in queue for user {username}: {verification_code}")
                                                        if login_states is not None:
                                                            login_states[username]["duo_code"] = verification_code
                                                            login_states[username]["duo_pending"] = False  # Code is now available
                                                        # Reset the timer for the next attempt
                                                        start_time = time.time()
                                                        continue  # Continue checking for more attempts
                                                except Exception as e:
                                                    logging.error(f"Error waiting for new DUO code: {e}")
                                                    break
                                            else:
                                                logging.info("Clicked trust browser button")
                                                await trust_or_retry.click()
                                                break  # Exit the loop after clicking trust button
                                        
                                        # Check if we've reached the dashboard
                                        current_url = page.url
                                        if '/myAccount/dashboard.htm' in current_url:
                                            logging.info("Successfully reached dashboard")
                                            if login_states is not None:
                                                login_states[username] = {
                                                    "ready": True,
                                                    "error": None,
                                                    "duo_required": False
                                                }
                                            break  # Exit the loop after successful login
                                        
                                        # Wait a bit before checking again
                                        await asyncio.sleep(1)
                                        
                                    except Exception as e:
                                        logging.error(f"Error in DUO button check loop: {e}")
                                        await asyncio.sleep(1)
                                        continue
                                
                                # If we timed out, update the state
                                if time.time() - start_time >= 300:
                                    if login_states is not None:
                                        login_states[username] = {
                                            "ready": False,
                                            "error": "DUO verification timed out. Please try logging in again.",
                                            "duo_required": False
                                        }
                                    logging.error("DUO verification timed out")
                                    return
                                
                            except Exception as e:
                                logging.info(f"Could not find or click buttons: {e}, continuing anyway")
                            
                            # Only wait for dashboard URL if we haven't already reached it
                            if not '/myAccount/dashboard.htm' in page.url:
                                try:
                                    await page.wait_for_url('https://waterlooworks.uwaterloo.ca/myAccount/dashboard.htm', timeout=50000)
                                except Exception as e:
                                    logging.error(f"Error waiting for dashboard URL: {e}")
                                    if login_states is not None:
                                        login_states[username] = {
                                            "ready": False,
                                            "error": "Failed to reach dashboard after DUO verification",
                                            "duo_required": False
                                        }
                                    return

                        elif status == 'failed':
                            if login_states is not None:
                                login_states[username] = {
                                    "ready": False,
                                    "error": "Invalid credentials. Please check your username and password.",
                                    "duo_required": False
                                }
                            logging.error("Login failed - Invalid credentials")
                            return
                        else:
                            if login_states is not None:
                                login_states[username] = {
                                    "ready": False,
                                    "error": "Login timeout - No response received",
                                    "duo_required": False
                                }
                            logging.error("Login timeout - No response received")
                            return

                        # Get resume details after successful login
                try:
                    resume_result = await get_resume_and_details(username, password, context=context)
                    if resume_result:
                        if username == "jrburtt@uwaterloo.ca":
                            logging.info("Successfully retrieved resume details from test data")
                        else:
                            logging.info(f"Successfully retrieved resume details and downloaded resume to {resume_result['resume_path']}")
                    else:
                        logging.warning("Failed to retrieve resume details")
                except Exception as resume_error:
                    logging.error(f"Error getting resume details: {resume_error}")

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
                    cleanup(ai_thread, apply_thread, browser, username)

            except Exception as e:
                if login_states is not None:
                    login_states[username] = {
                        "ready": False,
                        "error": f"An error occurred: {str(e)}",
                        "duo_required": False
                    }
                logging.error(f"Error in main process: {e}")
                if browser:
                    await cleanup_async(ai_thread, apply_thread, browser, username)
                return
            finally:
                if browser:
                    await cleanup_async(ai_thread, apply_thread, browser, username)

    except Exception as e:
        if login_states is not None:
            login_states[username] = {
                "ready": False,
                "error": f"An error occurred: {str(e)}",
                "duo_required": False
            }
        logging.error(f"Error in main process: {e}")
        if browser:
            await cleanup_async(ai_thread, apply_thread, browser, username)
        return
    finally:
        if browser:
            await cleanup_async(ai_thread, apply_thread, browser, username)

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

async def cleanup_async(ai_thread, apply_thread, browser, username):
    """Async version of cleanup for use in async contexts.
    This should be called from async code paths."""
    logging.info("Initiating async cleanup...")
    
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
            pages = browser.pages
            for page in pages:
                await page.close()
            await browser.close()
        except Exception as e:
            logging.error(f"Error in async browser cleanup: {e}")
    
    logging.info("Async cleanup complete.")

def start_playwright_worker():
    def run():
        while True:
            try:
                username, password = playwright_queue.get()
                asyncio.run(playwright_main(username, password, login_states))
                playwright_queue.task_done()
            except Exception as e:
                logging.error(f"Error in Playwright worker: {e}", exc_info=True)
                # Ensure cleanup happens even on error
                try:
                    if username in login_states:
                        login_states[username] = {
                            "ready": False,
                            "error": str(e),
                            "duo_required": False
                        }
                except Exception as cleanup_error:
                    logging.error(f"Error during error cleanup: {cleanup_error}")
                continue

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    app_thread = threading.Thread(target=run_app, daemon=True)
    app_thread.start()
    # You must pass username and password from your Flask backend/session
    # Example: asyncio.run(main(session["username"], session["password"]))
    # For now, just show the function signature change:
    # asyncio.run(main(username, password))
    pass

