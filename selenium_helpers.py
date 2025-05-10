import subprocess
import time
import logging
import itertools
import threading
import os
import tempfile
from diskcache import Cache
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from config import driver, job_iterator, job_queue, stop_event, selenium_lock, job_counter, WATERLOOWORKS_USERNAME, WATERLOOWORKS_PASSWORD, user_info, user_decisions, decisions_lock, served_job_evaluations, served_job_lock, all_job_details
import pdb as pbd
from evaluate_decision_history import evaluate_decision_history
import config
from selenium.webdriver.chrome.options import Options

# share the same profile folder
USER_DATA_DIR = "/path/to/shared/profile"  # Set this to a real, writable directory

def init_apply_driver():
    # Wait for the main Selenium session to be initialized
    while not config.driver:
        logging.info("Waiting for main driver to initialize...")
        time.sleep(3)
    main_driver = config.driver
    if not main_driver:
        raise RuntimeError("Cannot init apply driver: main webdriver not available")

    # Use a temp profile for the apply window to avoid profile lock
    # temp_profile = os.path.join(tempfile.gettempdir(), "ww_apply_profile")
    # options = webdriver.ChromeOptions()
    # options.add_argument(f"--user-data-dir={temp_profile}")
    # options.add_argument('--disable-gpu')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--remote-debugging-port=9223')  # Use a different port for parallel instance

    # d = webdriver.Chrome(options=options)
    # d.implicitly_wait(5)

    # # Import cookies from main driver for session sharing
    # Set up Chrome remote debugging
    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    user_data_dir = "C:/temp/chrome-profile1"
    remote_debugging_port = "9223"

    # Launch Chrome manually
    subprocess.Popen([
        chrome_path,
        f"--remote-debugging-port={remote_debugging_port}",
        f"--user-data-dir={user_data_dir}",
        "--new-window"
    ])

    # Wait for Chrome to start
    time.sleep(2)

    # Attach Selenium to it
    options = Options()
    options.debugger_address = f"localhost:{remote_debugging_port}"
    driver = webdriver.Chrome(options=options)
    driver.get("https://waterlooworks.uwaterloo.ca")
    # for ck in main_driver.get_cookies():
    #     try:
    #         d.add_cookie(ck)
    #     except Exception as e:
    #         logging.debug(f"Failed to add cookie: {ck.get('name')}: {e}")

    driver.get("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
    return driver

JOB_CACHE = Cache("job_cache") # Initialize diskcache

def load_job_cache():
    # Return the diskcache instance; it behaves like a dict.
    return JOB_CACHE

def launch_chrome_instance(port, profile_dir):
    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    subprocess.Popen([
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--new-window"
    ])

def connect_driver_to_chrome(port):
    options = Options()
    options.debugger_address = f"localhost:{port}"
    return webdriver.Chrome(options=options)

def start_selenium_session(username, password):
    global job_iterator, driver
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-debugging-port=9223')  # Main instance uses 9222
    try:
        logging.info("Initializing WebDriver...")
        driver = connect_driver_to_chrome(9222)  # Connect to the existing Chrome instance
        driver.implicitly_wait(5)
        driver.get("https://waterlooworks.uwaterloo.ca/waterloo.htm?action=login")
        logging.info("Logging in...")
        WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, "userNameInput"))).send_keys(username)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "nextButton"))).click()
        WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.ID, "passwordInput"))).send_keys(password)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "submitButton"))).click()
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "trust-browser-button"))).click()
        time.sleep(3)
        logging.info("Navigating to jobs page...")
        driver.get("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='All Jobs']"))).click()
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr")))
        rows = driver.find_elements(By.CSS_SELECTOR, "tr")[1:]
        logging.info(f"Found {len(rows)} job rows initially.")
        job_iterator = iter(rows)
        config.main_window = driver.current_window_handle
        logging.info("Selenium session started successfully.")
        config.driver = driver  # Update the global driver reference
        return True
    except (TimeoutException, NoSuchElementException, Exception) as e:
        logging.error(f"Error starting Selenium session: {e}", exc_info=True)
        if driver:
            driver.quit()
        driver = None
        job_iterator = None
        return False

def extract_job_details(job_info_panel):
    details = {}
    try:
        # <h2 class="margin--b--none padding--r--xs h3">Tech Support Assistant</h2>
        # <h2 class="margin--b--none padding--r--xs h3">Software Development</h2>
        job_title_element = job_info_panel.find_element(By.XPATH, "//h2[contains(@class, 'margin--b--none') and contains(@class, 'padding--r--xs') and contains(@class, 'h3')]")
        job_title_text = job_title_element.text.strip()
        if job_title_text:
            details['Job Title'] = job_title_text
    except NoSuchElementException:
        logging.warning("Job title element not found in job info panel.")
    try:
        # <div class="font--14 margin--t--s"><span>Geosource Energy Inc</span> - <span>Divisional Office</span><!----></div>
        company_element = job_info_panel.find_element(By.XPATH, "//div[contains(@class, 'font--14') and contains(@class, 'margin--t--s')]//span[1]")
        company_text = company_element.text.strip()
        if company_text:
            details['Company'] = company_text
        location_element = job_info_panel.find_element(By.XPATH, "//div[contains(@class, 'font--14') and contains(@class, 'margin--t--s')]//span[2]")
        location_text = location_element.text.strip()
        if location_text:
            details['Location'] = location_text
    except NoSuchElementException:
        logging.warning("Location or company element not found in job info panel.") 
    try:
        key_value_containers = job_info_panel.find_elements(By.CSS_SELECTOR, "div.tag__key-value-list.js--question--container")
        if not key_value_containers:
             key_value_containers = job_info_panel.find_elements(By.XPATH, "//div[contains(@class, 'row') and ./span[contains(@class, 'label')]]")
        logging.debug(f"Found {len(key_value_containers)} potential key-value containers.")
        for container in key_value_containers:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'}); window.scrollBy(0, -50);", container)
                time.sleep(0.1)
                key_element = container.find_element(By.CSS_SELECTOR, "span.label")
                key = key_element.text.strip()
                value_element = None
                try:
                    value_element = container.find_element(By.CSS_SELECTOR, "p")
                except NoSuchElementException:
                    try:
                        value_element = container.find_element(By.CSS_SELECTOR, "div:not([class*='label'])")
                    except NoSuchElementException:
                         all_text = container.get_attribute('textContent').strip()
                         value = all_text.replace(key, '').strip()
                         if key:
                             details[key] = value
                         continue
                if value_element and key:
                    value = value_element.get_attribute('textContent').strip()
                    details[key] = value
                    logging.debug(f"Extracted: {key} -> {value[:50]}...")
            except NoSuchElementException:
                logging.debug("Skipping container, couldn't find key or value element.")
            except StaleElementReferenceException:
                 logging.warning("Stale element reference during detail extraction, skipping container.")
            except Exception as e:
                logging.warning(f"Minor error parsing key-value pair: {e}")
    except Exception as e:
        logging.error(f"Error during detailed job extraction: {e}", exc_info=True)
    try:
        job_id_element = job_info_panel.find_element(By.XPATH, "//span[contains(@class, 'tag-label') and contains(@style, 'background: rgb(0, 0, 0)')]")
        details['Job Posting ID'] = job_id_element.text.strip()
    except NoSuchElementException:
        logging.warning("Job Posting ID not found using specific XPath.")
        for key in details:
            if 'job posting id' in key.lower():
                details['Job Posting ID'] = details[key]
                break
    if not details.get('Job Posting ID'):
         details['Job Posting ID'] = details.get('Job Title', f"UnknownJob_{time.time()}")
    return details

# 'Compatibility score out of 100: X, Salary in CAD: Y, Category: Z'\n\n"
def extract_score_salary_category(evaluation_text: str) -> tuple:
    """Extracts the score, salary, and category from the evaluation text."""
    if not evaluation_text:
        return None, None, None
    try:
        lines = evaluation_text.split('\n')
        for line in lines:
            if "Compatibility score out of 100:" in line:
                parts = line.split(",")
                score_part = parts[0].split(":")[-1].strip()
                salary_part = parts[1].split(":")[-1].strip()
                category_part = parts[2].split(":")[-1].strip()
                return int(score_part), salary_part, category_part
    except Exception as e:
        logging.error(f"Error extracting score/salary/category: {e}", exc_info=True)
    return None, None, None

def remove_score_salary_category(evaluation_text: str) -> str:
    """Removes the score line from the evaluation text."""
    if not evaluation_text:
        return evaluation_text
    try:
        lines = evaluation_text.split('\n')
        filtered_lines = [line for line in lines if "Compatibility score out of 100:" not in line]
        return "\n".join(filtered_lines).strip()
    except Exception as e:
        logging.error(f"Error removing score line: {e}", exc_info=True)
    return evaluation_text


def fetch_and_process_jobs(evaluate_job_fit):
    global driver, job_iterator, job_queue, stop_event
    job_counter_local = iter(range(1, 1000000))
    if not driver or not job_iterator:
        logging.error("Selenium session not active when starting job processing.")
        job_queue.put((101, {"message": "Error: Backend Selenium session not initialized."}))
        return
    logging.info("Starting job processing thread...")
    processed_count = 0
    job_file_cache = load_job_cache() # This now returns the diskcache.Cache instance
    while not stop_event.is_set():
        if job_queue.full():
            time.sleep(1)
            continue
        row = None
        job_details = None
        try:
            with selenium_lock:
                row = next(job_iterator)
                logging.info(f"Processing next job row (approx #{processed_count + 1})...")
                # check if job is already applied to/shortlisted
                try:
                    WebDriverWait(row, 2).until(
                        EC.presence_of_element_located((By.XPATH, ".//button[@aria-label='Apply']"))
                    )
                    # check if save to my jobs folder button is clickable
                    WebDriverWait(row, 2).until(
                        EC.element_to_be_clickable((By.XPATH,
                            ".//button[@aria-label='Save to My Jobs Folder' and @type='button']"))              
                    )
                except TimeoutException:
                    logging.warning("Apply button not found in the current row.")
                    continue
                # get the job ID from the row in the ID column
                try:
                    job_id = row.find_element(By.CSS_SELECTOR, "th:nth-child(1) :nth-child(1) > span").text.strip()
                except Exception as e:
                    logging.warning(f"Could not extract job_id for row {processed_count + 1}: {e}. Skipping.")
                    continue

                # --- Check file cache here ---
                if job_id in job_file_cache:
                    logging.info(f"Job details for job_id {job_id} loaded from file cache.")
                    job_details = job_file_cache[job_id]
                else:
                    # ...existing code to click and extract job details...
                    job_title_link = WebDriverWait(row, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "td:nth-child(2) a"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); window.scrollBy(0, -100);", job_title_link)
                    time.sleep(0.5)
                    job_title_link.click()
                    try:
                        job_info_panel = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.is--long-form-reading"))
                        )
                        logging.debug("Job info panel located.")
                        time.sleep(1)
                        job_details = extract_job_details(job_info_panel)
                    except TimeoutException:
                        logging.error("Timeout waiting for job info panel to appear.")
                        job_details = {"Job Title": "Error Loading Details", "Job Posting ID": f"Error_{time.time()}"}
                    except Exception as e:
                        logging.error(f"Unexpected error extracting details: {e}", exc_info=True)
                        job_details = {"Job Title": "Error Loading Details", "Job Posting ID": f"Error_{time.time()}"}
                    try:
                        close_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn__default--text') and .//i[text()='close']]"))
                        )
                        time.sleep(0.2)
                        close_button.click()
                        logging.debug("Clicked close button.")
                        time.sleep(1)
                    except TimeoutException:
                        logging.warning("Could not find or click close button via common selectors. Attempting browser back.")
                        try:
                            driver.back()
                            time.sleep(2)
                        except Exception as back_err:
                            logging.error(f"Failed to navigate back: {back_err}.")
                    except Exception as e:
                        logging.error(f"Error closing job panel: {e}")
                        try:
                            driver.back()
                            time.sleep(2)
                        except Exception as back_err:
                            logging.error(f"Failed to navigate back after close error: {back_err}")
            if job_details:
                # After extracting:
                if job_details and job_id:
                    job_file_cache[job_id] = job_details # diskcache will handle saving
                # --- End cache check ---
                logging.info(f"Performing AI evaluation for job ID: {job_id}...")

                # update global job dtails with the job ID

                with decisions_lock: # Access decisions safely
                    current_decision_history = list(user_decisions)

                if len(current_decision_history) > 3:
                    decision_history_evaluation = evaluate_decision_history(current_decision_history)
                else:
                    decision_history_evaluation = ""

                ai_evaluation_with_score = evaluate_job_fit(job_details, user_info, decision_history_evaluation)
                score, salary, cateogry = extract_score_salary_category(ai_evaluation_with_score) # Score extracted from original
                priority = 100 - score
                job_details['salary'] = salary
                job_details['category'] = cateogry
                all_job_details[job_id] = job_details

                # Remove score line before putting into queue for user display and history
                ai_evaluation_for_user = remove_score_salary_category(ai_evaluation_with_score)

                job_data_to_queue = {
                    "job_id": job_id,
                    "job_details": job_details,
                    "ai_evaluation": ai_evaluation_for_user,
                }
                job_cnt = next(job_counter_local) # Use local counter if defined, else global job_counter
                job_queue.put((priority, job_cnt, job_data_to_queue))
                logging.info(f"Job '{job_details.get('Job Title', 'N/A')}' (ID: {job_id}) added to queue with priority {priority}. Evaluation for user will not show score. Queue size: {job_queue.qsize()}")
                processed_count += 1
            else:
                logging.warning("No job details extracted for current row.")
        except StopIteration:
            logging.info("All job rows processed from the initial list.")
            job_queue.put((101, {"message": "No more jobs found."}))
            break
        except StaleElementReferenceException:
            logging.warning("Stale element reference encountered for job row.")
            continue
        except Exception as e:
            logging.error(f"Major error processing job row: {e}", exc_info=True)
            try:
                with selenium_lock:
                    panels = driver.find_elements(By.CSS_SELECTOR, "div.is--long-form-reading")
                    if panels:
                        logging.warning("Attempting recovery by closing potentially stuck panel.")
                        try:
                            close_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn__close-panel') or contains(@aria-label, 'Close') or .//i[text()='close']]")
                            close_button.click()
                            time.sleep(1)
                        except:
                            try:
                                driver.back()
                                time.sleep(2)
                            except Exception as back_err_rec:
                                logging.error(f"Recovery back navigation failed: {back_err_rec}")
            except Exception as recovery_err:
                logging.error(f"Recovery attempt failed: {recovery_err}")
            continue

    logging.info(f"Job processing thread finished after processing {processed_count} jobs.")

def apply_to_job(job_id: int, driver=None):
    drv = driver or globals()['driver']      # use injected or fallback
    global selenium_lock
    job_id_str = str(job_id)
    logging.info(f"Attempting to apply to job ID: {job_id_str}")
    with selenium_lock:
        drv.execute_script("window.open('');")
        new_tab = [h for h in drv.window_handles if h != config.main_window][-1]
        drv.switch_to.window(new_tab)
        try:
            # go to jobs page and search
            drv.get("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
            search_input = WebDriverWait(drv, 10).until(
                EC.presence_of_element_located((By.NAME, "emptyStateKeywordSearch"))
            )
            search_input.clear()
            search_input.send_keys(job_id_str, webdriver.common.keys.Keys.ENTER)
            # follow to tab opened when enter is pressed

            # click Apply button
            try:
                apply_btn = WebDriverWait(drv, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                        f"//tr[.//span[contains(text(),'{job_id_str}')]]//button[@aria-label='Apply']"))
                )
                drv.execute_script("arguments[0].scrollIntoView(true);", apply_btn)
                time.sleep(0.2)
                apply_btn.click()
                logging.info("Clicked Apply")

                time.sleep(3)
                drv.switch_to.window(drv.window_handles[-1])

                default_radio = WebDriverWait(drv, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//input[@type='radio' and @value='defaultPkg' and @name='applyOption']"))
                )
                # if default_radio:
                drv.execute_script("arguments[0].click();", default_radio)
                final_apply = WebDriverWait(drv, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//button[@type='button' and contains(@class, 'btn__hero--text') and contains(@class, 'btn--info') and contains(@class, 'js--ui-wizard-next-btn')]"))
                )
                drv.execute_script("arguments[0].click();", final_apply)
                logging.info("Application submitted")
                return True
                # else:
                #     logging.info("Default package not found; shortlisting instead")
                #     return shortlist_job(job_id)
            except (TimeoutException, NoSuchElementException):
                logging.warning("Apply flow failed or timeout; shortlisting instead")
                drv.close()
                return shortlist_job(job_id, driver=drv)
            except Exception as e:
                logging.error(f"Error in apply_to_job: {e}", exc_info=True)
                return False
        finally:
            # driver.close()
            drv.close()
            drv.switch_to.window(config.main_window)

def shortlist_job(job_id: int, driver=None):
    drv = driver or globals()['driver']
    global selenium_lock
    job_id_str = str(job_id)
    logging.info(f"Attempting to shortlist job ID: {job_id_str}")
    with selenium_lock:
        drv.execute_script("window.open('');")
        new_tab = [h for h in drv.window_handles if h != config.main_window][-1]
        drv.switch_to.window(new_tab)
        # go to jobs page and search
        drv.get("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
        search_input = WebDriverWait(drv, 10).until(
            EC.presence_of_element_located((By.NAME, "emptyStateKeywordSearch"))
        )
        search_input.clear()
        search_input.send_keys(job_id_str, webdriver.common.keys.Keys.ENTER)
        # time.sleep(2)

        # click Save to My Jobs Folder
        try:
            # time.sleep(1)
            # <button aria-label="Save to My Jobs Folder" type="button" class="btn__small--text btn--info plain btn--icon-only"><i class="material-icons">create_new_folder</i></button>
            save_to_my_jobs_btn = WebDriverWait(drv, 10).until(
                EC.element_to_be_clickable((By.XPATH,
                    f"//tr[.//span[contains(text(),'{job_id_str}')]]//button[@aria-label='Save to My Jobs Folder']"))
            )
            drv.execute_script("arguments[0].click();", save_to_my_jobs_btn)
            # toggle shortlist checkbox
            try:
                chk = WebDriverWait(drv, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//label[.//p[text()='AutoShortlist']]//input[@type='checkbox']"))
                )
                drv.execute_script("arguments[0].click();", chk)

            except TimeoutException:
                # <label data-v-1ebc3496-s="" class="toggle--single margin--a--none padding--a--none" style="justify-content: space-between; align-items: center;"><p data-v-1ebc3496-s="" class="label margin--a--none" style="margin: 0px !important;">Create a new folder</p><input data-v-1ebc3496-s="" type="checkbox"><i data-v-1ebc3496-s="" class="material-icons toggle-on">toggle_on</i><i data-v-1ebc3496-s="" class="material-icons toggle-off">toggle_off</i></label>
                chk = WebDriverWait(drv, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//label[.//p[text()='Create a new folder']]//input[@type='checkbox']"))
                )
                drv.execute_script("arguments[0].click();", chk)
                logging.info("Create a new folder checkbox clicked")
                # <input data-v-1ebc3496-s="" id="sidebarFolderNameInput" class="input--box display--block" type="text" maxlength="25" name="sidebarFolderNameInput">
                folder_name_input = WebDriverWait(drv, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//input[@id='sidebarFolderNameInput' and @class='input--box display--block']"))
                )
                folder_name_input.clear()
                folder_name_input.send_keys("AutoShortlist")

                # <button data-v-1ebc3496-s="" class="btn__hero--text btn--default margin--r--s width--100"> Save </button>
                logging.info("New folder created and saved")
          
            save_btn = WebDriverWait(drv, 10).until(
                EC.element_to_be_clickable((By.XPATH,
                "//button[@class='btn__hero--text btn--default margin--r--s width--100' and normalize-space()='Save']"))
            )
            
            drv.execute_script("arguments[0].click();", save_btn)
            logging.info("Clicked Save button")
            drv.close()
            return True
        except (TimeoutException, NoSuchElementException):
            logging.error("Failed to shortlist job", exc_info=True)
            drv.close()
            return False

def process_apply_queue(apply_queue):
    apply_driver = None
    while True:
        if apply_queue.empty():
            logging.info("Apply queue is empty, no jobs to process.")
            time.sleep(1)
            continue
        if not apply_driver:
              apply_driver = init_apply_driver() # NEW: separate window  
        job_id = apply_queue.get()
        logging.info(f"Processing apply request for job ID: {job_id}")
        try:
            shortlist_job(job_id, driver=apply_driver)  # pass the new driver
        except Exception as e:
            logging.error(f"Error processing apply for job {job_id}: {e}", exc_info=True)
        finally:
            apply_queue.task_done()