import os
import logging
import queue
import itertools
import threading
from flask import Flask
from html_template import HTML_TEMPLATE

# Logger configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load credentials securely (replace with your method, e.g., environment variables)
WATERLOOWORKS_USERNAME = os.environ.get("WW_USER", "jrburtt@uwaterloo.ca")
WATERLOOWORKS_PASSWORD = os.environ.get("WW_PASS", "Birchwood718#")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

# User information
user_info = {
    "name": "John Burtt",
    "degree": "Computer Engineering",
    "skills": {
        "languages": ["Python", "SQL (PostgreSQL)", "JavaScript", "HTML/CSS", "Bash", "C/C++"],
        "frameworks": ["Flask", "React", "ROS", "Docker", "Fiber (Go)", "Terraform"]
    },
    "salary_expectation": 60,
    "location_expectation": "California",
}

# Global state and thread-related globals used by Selenium helpers
driver = None
job_iterator = None
job_queue = queue.PriorityQueue(maxsize=50)
job_counter = itertools.count()  # For tie-breaking in job queue
processing_thread = None
stop_event = threading.Event()
selenium_lock = threading.Lock()
user_decisions = []
decisions_lock = threading.Lock()
MAX_DECISION_HISTORY = 20
served_job_evaluations = {} # Stores {job_id: ai_evaluation} for jobs sent to frontend
served_job_lock = threading.Lock() # Lock for accessing served_job_evaluations

# Flask app and the HTML template
app = Flask(__name__)