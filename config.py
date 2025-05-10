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


# High Q Technologies Jan. 2025 – Apr. 2025
# Incoming Software Developer Waterloo, ON
# OTTO Motors, a division of Clearpath Robotics Jan. 2024 – Apr. 2024
# DevOps Developer in Fleet Software Kitchener, ON
# • Designed and implemented a custom tool to automate the generation of Linux-compatible software package layers,
# reducing deployment time by 30%.
# • Developed a proprietary algorithm to optimize software layers, resulting in a 25% increase in system performance
# and resource utilization.
# • Created a responsive UI with Flask and Socket.IO for real-time layer generation updates, enhancing transparency
# and user experience.
# Swap Robotics Jan. 2022 – Apr. 2022, May 2023 – Sep. 2023
# Software Developer for Autonomous Robotics Kitchener, ON
# • Implemented a path recovery feature with PostgreSQL for environment restoration, reducing downtime by 20%.
# • Developed Python scripts for ROSbag management, integrating with AWS S3 for cloud storage and
# auto-deletion of older files to prevent data loss.
# • Enhanced coverage path planning with ROS, improving operational efficiency and coverage accuracy by reducing
# redundancy.
# • Upgraded architecture from ROS topic-based to service-based, reducing operational downtime by 15%.
# Department of National Defence-Royal Canadian Air Force Sep. 2022 – Dec. 2022
# Full Stack Developer Kitchener, ON
# • Implemented an event calendar to optimize workday calculations for the critical chain calculation of project
# timelines.
# • Engaged with clients and stakeholders, including an in-person visit to Halifax, to gather requirements and feedback,
# enhancing client satisfaction
# User information
user_info = {
    # "name": "John Burtt",
    "degree": "Computer Engineering",
    "skills": {
        "languages": ["Python", "SQL (PostgreSQL)", "JavaScript", "HTML/CSS", "Bash", "C/C++"],
        "frameworks": ["Flask", "React", "ROS", "Docker", "Fiber (Go)", "Terraform"]
    },
    "desired_salary": "$40/hour CAD",
    "desired_location": "Must be in the USA",
    "co-op_duration": "Must be 4 months",
    "work_experience": [
        {
            "company": "High Q Technologies",
            "role": "Incoming Software Developer",
            "location": "Waterloo, ON",
            "duration": "Jan. 2025 – Apr. 2025"
        },
        {
            "company": "OTTO Motors, a division of Clearpath Robotics",
            "role": "DevOps Developer in Fleet Software",
            "location": "Kitchener, ON",
            "duration": "Jan. 2024 – Apr. 2024"
        },
        {
            "company": "Swap Robotics",
            "role": "Software Developer for Autonomous Robotics",
            "location": "Kitchener, ON",
            "duration": ["Jan. 2022 – Apr. 2022", "May 2023 – Sep. 2023"]
        },
        {
            "company": "Department of National Defence-Royal Canadian Air Force",
            "role": "Full Stack Developer",
            "location": "Kitchener, ON",
            "duration": ["Sep. 2022 – Dec. 2022"]
        }
    ]
}

# Global state and thread-related globals used by Selenium helpers
driver = None
job_iterator = None
job_queue = queue.PriorityQueue(maxsize=15)
apply_to_job_queue = queue.Queue()          # NEW: queue for apply requests
job_counter = itertools.count()  # For tie-breaking in job queue
processing_thread = None
stop_event = threading.Event()
selenium_lock = threading.Lock()
user_decisions = []
decisions_lock = threading.Lock()
MAX_DECISION_HISTORY = 100
served_job_evaluations = {} # Stores {job_id: ai_evaluation} for jobs sent to frontend
served_job_lock = threading.Lock() # Lock for accessing served_job_evaluations
all_job_details = {} # Stores all job details for the current session

main_window = None                          # NEW: record the original window handle

# Flask app and the HTML template
app = Flask(__name__)