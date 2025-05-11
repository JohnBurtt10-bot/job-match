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