import asyncio
import threading
import queue
from playwright.async_api import async_playwright
from evaluate_decision_history import evaluate_decision_history
from config import (
    job_queue, stop_event,
    user_info, user_decisions, decisions_lock, all_job_details,
    apply_to_job_queue
)
from selenium_helpers import remove_score_salary_category, extract_score_salary_category
from apply_to_job import apply_to_job
import logging
from diskcache import Cache
import evaluation

JOBS_URL = "https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm"

# Add a global queue for DUO codes
duo_code_queue = queue.Queue()

def evaluate_job_fit(id, job, job_counter_local):
    with decisions_lock: # Access decisions safely
        current_decision_history = list(user_decisions)

        if len(current_decision_history) > 3:
            decision_history_evaluation = evaluate_decision_history(current_decision_history)

        else:
            decision_history_evaluation = ""

        ai_evaluation_with_score = evaluation.evaluate_job_fit(job, user_info, decision_history_evaluation)
        score, salary, cateogry = extract_score_salary_category(ai_evaluation_with_score) # Score extracted from original
        priority = 100 - score
        job['salary'] = salary
        job['category'] = cateogry
        all_job_details[id] = job

        # Remove score line before putting into queue for user display and history
        ai_evaluation_for_user = remove_score_salary_category(ai_evaluation_with_score)

        job_data_to_queue = {
            "job_id": id,
            "job_details": job,
            "ai_evaluation": ai_evaluation_for_user,
        }
        job_cnt = next(job_counter_local) # Use local counter if defined, else global job_counter
        job_queue.put((priority, job_cnt, job_data_to_queue))
        logging.info(f"Job '{job.get('title', 'N/A')}' (ID: {id}) added to queue with priority {priority}. Evaluation for user will not show score. Queue size: {job_queue.qsize()}")


async def extract_job_details(page, row):
    job = {}
    try:
        title_el = await row.query_selector("td:nth-child(2) a")
        job['title'] = await title_el.inner_text() if title_el else ""
        company_el = await row.query_selector("td:nth-child(3)")
        job['company'] = await company_el.inner_text() if company_el else ""

        # Click the job title link to open the job details panel
        if title_el:
            await title_el.click()
            # Wait for the job info panel to appear
            job_info_panel = await page.wait_for_selector("div.is--long-form-reading", timeout=15000)
            # Try both selectors for key-value containers
            key_value_containers = await job_info_panel.query_selector_all("div.tag__key-value-list.js--question--container")
            if not key_value_containers:
                key_value_containers = await job_info_panel.query_selector_all("xpath=//div[contains(@class, 'row') and ./span[contains(@class, 'label')]]")
            # For each container, extract key and value
            for container in key_value_containers:
                try:
                    # await container.scroll_into_view_if_needed()
                    key_el = await container.query_selector("span.label")
                    key = (await key_el.inner_text()).strip() if key_el else ""
                    value = ""
                    value_el = await container.query_selector("p")
                    if not value_el:
                        value_el = await container.query_selector("div:not([class*='label'])")
                    if value_el:
                        value = (await value_el.inner_text()).strip()
                    else:
                        all_text = (await container.inner_text()).strip()
                        value = all_text.replace(key, '').strip()
                    if key:
                        job[key] = value
                except Exception:
                    continue
            # Close the job info panel (try close button, fallback to browser back)
            try:
                close_btn = await page.query_selector("//button[contains(@class, 'btn__default--text') and .//i[text()='close']]", strict=False)
                await close_btn.click()
            except Exception:
                await page.go_back()
    except Exception as e:
        job['error'] = str(e)
    return job

async def get_total_pages(page):
    # Find all pagination links and return the highest page number
    await page.wait_for_selector(".pagination__link", timeout=10000)
    links = await page.query_selector_all(".pagination__link")
    page_numbers = []
    for link in links:
        text = (await link.inner_text()).strip()
        if text.isdigit():
            page_numbers.append(int(text))
    return max(page_numbers) if page_numbers else 1

async def goto_jobs_page(page, page_num):
    # Only click pagination links for pages > 1
    if page_num == 1:
        # Assume already on page 1, just wait for rows
        await page.wait_for_selector("tr")
        return
    # Find the pagination link with the correct number and click it
    links = await page.query_selector_all(".pagination__link")
    for link in links:
        text = (await link.inner_text()).strip()
        if text == str(page_num):
            await link.click()
            await page.wait_for_selector("tr")
            await page.wait_for_timeout(1000)  # Wait for table to update
            return
        
def cleanup(ai_thread, apply_thread, browser):
    logging.info("Initiating cleanup...")
    stop_event.set()
    # if browser:
    #     logging.info("Quitting WebDriver...")
    #     try:
    #         browser.close()
    #     except Exception as e:
    #         logging.error(f"Error quitting WebDriver: {e}")
    try:
        if ai_thread and ai_thread.is_alive():
            logging.info("Waiting for AI evaluation thread to finish...")
            ai_thread.join(timeout=15)
            if ai_thread.is_alive():
                logging.warning("AI evaluation thread did not terminate gracefully.")
    except Exception as e:
        logging.error(f"Error waiting for AI evaluation thread: {e}")
    
    try:
        if apply_thread and apply_thread.is_alive():
            logging.info("Waiting for apply-to-job thread to finish...")
            apply_thread.join(timeout=15)
            if apply_thread.is_alive():
                logging.warning("Apply-to-job thread did not terminate gracefully.")
    except Exception as e:
        logging.error(f"Error waiting for apply-to-job thread: {e}")

    logging.info("Cleanup complete.")
        

def start_ai_evaluation_worker(jobs):
    def run():
        asyncio.run(ai_evaluation_worker_async(jobs))
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread

async def ai_evaluation_worker_async(jobs):
    job_counter_local = iter(range(1000, 10000))  # Local job counter for this thread
    for job_id, job in jobs.items():
        while job_queue.full() and not stop_event.is_set():
            await asyncio.sleep(0.1)
        await asyncio.to_thread(evaluate_job_fit, job_id, job, job_counter_local)

async def main(username, password, login_states=None):
    job_details_cache = Cache("job_details_cache")
    async with async_playwright() as p:
        # use user data dir to persist login session
        user_data_dir = "user_data"
        # Check if user data dir exists, if not create it
        import os
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)
        # Launch browser with user data dir
        # browser = await p.chromium.launch_persistent_context(user_data_dir, headless=False)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        context = browser  # Use the persistent context directly
        page = await context.new_page()
        await page.goto("https://waterlooworks.uwaterloo.ca/waterloo.htm?action=login")
        # # Wait for username input and enter username
        await page.wait_for_selector("#userNameInput", state="visible", timeout=15000)
        await page.fill("#userNameInput", username)  # Use provided username

        # Click next button
        await page.wait_for_selector("#nextButton", state="attached", timeout=10000)
        await page.click("#nextButton")

        # Wait for password input and enter password
        await page.wait_for_selector("#passwordInput", state="attached", timeout=100000)
        await page.fill("#passwordInput", password)  # Use provided password

        # Click submit button
        await page.wait_for_selector("#submitButton", state="attached", timeout=10000)
        await page.click("#submitButton")

        # Wait for DUO verification code and send to frontend via queue
        await page.wait_for_selector("div.verification-code", state="attached", timeout=10000)
        verification_code_el = await page.query_selector("div.verification-code")
        verification_code = await verification_code_el.inner_text() if verification_code_el else None
        if verification_code:
            duo_code_queue.put(verification_code)  # Make code available to Flask

        # <div class="row display-flex align-flex-justify-content-center verification-code">887</div>
        # parse code
        await page.wait_for_selector("div.verification-code", state="attached", timeout=10000)
        verification_code = await page.query_selector("div.verification-code")

        # # Click trust browser button
        await page.wait_for_selector("#trust-browser-button", state="attached", timeout=15000)
        await page.click("#trust-browser-button")
        
        await page.wait_for_selector("a.items.active", state="attached", timeout=10000)
        if login_states is not None:
            login_states[username]["ready"] = True

        # sleep for 5 seconds to allow the page to load
        # await page.wait_for_timeout(1000)
        await page.goto(JOBS_URL, wait_until="load")

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

        # start AI evaluation worker as a task on a different thread
        ai_thread = start_ai_evaluation_worker(jobs)

        # Start async apply-to-job worker on the main thread (not as a background task)
        try:
            await apply_to_job_worker(context)
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received. Shutting down...")
        finally:
            cleanup(ai_thread, None, browser)

# Start apply-to-job thread
async def apply_to_job_worker(context):
    while not stop_event.is_set():
        # try:
            # Use asyncio.to_thread to avoid blocking the event loop with a blocking queue
            job_id = await asyncio.to_thread(apply_to_job_queue.get, 2)
            await apply_to_job(job_id, context)
            await asyncio.to_thread(apply_to_job_queue.task_done)
        # except Exception:
        #     continue


if __name__ == "__main__":
    app_thread = threading.Thread(target=run_app, daemon=True)
    app_thread.start()
    # You must pass username and password from your Flask backend/session
    # Example: asyncio.run(main(session["username"], session["password"]))
    # For now, just show the function signature change:
    # asyncio.run(main(username, password))
    pass

