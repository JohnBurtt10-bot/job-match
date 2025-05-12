import os
import logging
import json
from flask import Flask

# Logger configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
# Example user_info structure (commented out)
# user_info = {
#     "jrburtt@uwaterloo.ca": {
#         "degree": "Computer Engineering",
#         "skills": {
#             "languages": ["Python", "SQL (PostgreSQL)", "JavaScript", "HTML/CSS", "Bash", "C/C++"],
#             "frameworks": ["Flask", "React", "ROS", "Docker", "Fiber (Go)", "Terraform"]
#         },
#         "desired_salary": "$40/hour CAD",
#         "desired_location": "Must be in the USA",
#         "co-op_duration": "Must be 4 months",
#         "work_experience": [
#             {
#                 "company": "High Q Technologies",
#                 "role": "Incoming Software Developer",
#                 "location": "Waterloo, ON",
#                 "duration": "Jan. 2025 – Apr. 2025"
#             },
#             {
#                 "company": "OTTO Motors, a division of Clearpath Robotics",
#                 "role": "DevOps Developer in Fleet Software",
#                 "location": "Kitchener, ON",
#                 "duration": "Jan. 2024 – Apr. 2024"
#             },
#             {
#                 "company": "Swap Robotics",
#                 "role": "Software Developer for Autonomous Robotics",
#                 "location": "Kitchener, ON",
#                 "duration": ["Jan. 2022 – Apr. 2022", "May 2023 – Sep. 2023"]
#             },
#             {
#                 "company": "Department of National Defence-Royal Canadian Air Force",
#                 "role": "Full Stack Developer",
#                 "location": "Kitchener, ON",
#                 "duration": ["Sep. 2022 – Dec. 2022"]
#             }
#         ]
#     }
# }

# Initialize empty user_info dictionary
user_info = {}

# Global state and thread-related globals used by Selenium helpers
driver = None

# Replace single global state with per-user dictionaries
job_queue = {}                # {username: PriorityQueue}
apply_to_job_queue = {}       # {username: Queue}
job_counter = {}              # {username: itertools.count()}
processing_thread = {}        # {username: Thread}
stop_event = {}               # {username: threading.Event()}
user_decisions = {}           # {username: list}
decisions_lock = {}           # {username: threading.Lock()}
served_job_evaluations = {}   # {username: dict}
served_job_lock = {}          # {username: threading.Lock()}
all_job_details = {}          # {username: dict}
main_window = {}              # {username: window_handle}

MAX_DECISION_HISTORY = 10

USER_DECISIONS_FILE = "user_decisions.json"

def load_user_decisions(username):
    user_file = f"user_decisions_{username}.json"
    if os.path.exists(user_file):
        try:
            with open(user_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load user_decisions for {username}: {e}")
    return []

def save_user_decisions(username, user_decisions_list):
    user_file = f"user_decisions_{username}.json"
    try:
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(user_decisions_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Failed to save user_decisions for {username}: {e}")

# Flask app and the HTML template
app = Flask(__name__)