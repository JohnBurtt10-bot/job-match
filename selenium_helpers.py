import time
import logging
import itertools
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from config import driver, job_iterator, job_queue, stop_event, selenium_lock, job_counter, WATERLOOWORKS_USERNAME, WATERLOOWORKS_PASSWORD, user_info, user_decisions, decisions_lock, served_job_evaluations, served_job_lock
import pdb as pbd

def start_selenium_session(username, password):
    global driver, job_iterator
    options = webdriver.ChromeOptions()
    # ...existing options...
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    try:
        logging.info("Initializing WebDriver...")
        driver = webdriver.Chrome(options=options)
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
        logging.info("Selenium session started successfully.")
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

def extract_score_from_evaluation(evaluation_text):
    import re
    if not evaluation_text:
        return 0
    match = re.search(r"Compatibility score out of 100:\s*(\d+)", evaluation_text, re.IGNORECASE)
    if match:
        try:
            score = int(match.group(1))
            return max(0, min(score, 100))
        except ValueError:
            logging.warning(f"Could not parse score from evaluation: {match.group(1)}")
            return 0
    else:
        logging.warning("Could not find compatibility score line in evaluation.")
        return 0

def _remove_score_line(evaluation_text: str) -> str:
    """Helper to remove the compatibility score line from evaluation text."""
    if not evaluation_text:
        return ""
    lines = evaluation_text.split('\n')
    lines_without_score = [line for line in lines if "Compatibility score out of 100:" not in line]
    return '\n'.join(lines_without_score).strip()

def fetch_and_process_jobs(evaluate_job_fit):
    global driver, job_iterator, job_queue, stop_event
    job_counter_local = iter(range(1, 1000000))
    if not driver or not job_iterator:
        logging.error("Selenium session not active when starting job processing.")
        job_queue.put((101, {"message": "Error: Backend Selenium session not initialized."}))
        return
    logging.info("Starting job processing thread...")
    processed_count = 0
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
                try:
                    job_title_link = WebDriverWait(row, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "td:nth-child(2) a"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); window.scrollBy(0, -100);", job_title_link)
                    time.sleep(0.5)
                    job_title_link.click()
                except (TimeoutException, StaleElementReferenceException) as e:
                    logging.warning(f"Could not click job link for row {processed_count + 1}: {e}. Skipping.")
                    continue
                try:
                    job_info_panel = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.is--long-form-reading"))
                    )
                    logging.debug("Job info panel located.")
                    time.sleep(1)
                    job_details = extract_job_details(job_info_panel)
                    # dump job details to file for debugging
                    with open(f"job_details_debug{time.time()}.txt", "a", encoding="utf-8") as f:
                        # f.write(f"Job ID: {job_details.get('Job Posting ID', 'Unknown')}\n")
                        f.write(f"Details: {job_details}\n\n")
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
                job_id = job_details.get('Job Posting ID', f"FallbackID_{processed_count}")
                logging.info(f"Performing AI evaluation for job ID: {job_id}...")

                with decisions_lock: # Access decisions safely
                    current_decision_history = list(user_decisions)

                ai_evaluation_with_score = evaluate_job_fit(job_details, user_info, current_decision_history)
                score = extract_score_from_evaluation(ai_evaluation_with_score) # Score extracted from original
                priority = 100 - score

                # Remove score line before putting into queue for user display and history
                ai_evaluation_for_user = _remove_score_line(ai_evaluation_with_score)

                job_data_to_queue = {
                    "job_id": job_id,
                    "job_details": job_details,
                    "ai_evaluation": ai_evaluation_for_user # Store version without score line
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