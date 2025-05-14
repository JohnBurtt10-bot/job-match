# Job Match: Smarter Job Swiping for WaterlooWorks

## 🚀 Quick Start

**Waterloo Students:**
- Use the main app here: [https://job-match.onrender.com/](https://job-match.onrender.com/)  
(Log in with your WaterlooWorks credentials to see your real jobs, AI-ranked and swipable!)

**Just want to try it?**
- Try the live demo (no login required): [https://job-match.onrender.com/demo](https://job-match.onrender.com/demo)
  - The demo uses sample resume and job data, but shows the full AI-powered swiping experience.

---

## Why I Built This

As a student at the University of Waterloo, I noticed a persistent gap in how AI tools approach job applications: they rarely optimize the order in which jobs are shown to users. At the same time, many students (myself included) have been frustrated with the new WaterlooWorks UI/UX, which can be slow, unintuitive, and overwhelming—especially during co-op application season.

**Job Match** was created to streamline the job search and application process for Waterloo students. By leveraging AI, it not only automates tedious tasks but also intelligently prioritizes job postings, helping students focus on the most relevant opportunities first.

---

## Features

- **AI-Powered Job Ranking:** Uses your resume and preferences to evaluate and prioritize job postings.
- **Automated Job Parsing:** Scrapes and parses jobs from WaterlooWorks using Playwright.
- **Smart Swiping UI:** Presents jobs in an optimized order, allowing you to accept/reject with a single click.
- **Automated Application:** Optionally auto-applies to jobs you approve.
- **Resume Extraction:** Handles both text-based and (optionally) image-based resumes.
- **Persistent User Sessions:** Remembers your progress and preferences.
- **Robust Error Handling:** Designed to handle WaterlooWorks quirks and login flows, including DUO authentication.

---

## Technical Overview

### Stack

- **Backend:** Python, Flask, Playwright (for browser automation)
- **Frontend:** HTML/CSS (rendered via Flask templates)
- **AI/ML:** OpenAI API for job fit evaluation
- **PDF Parsing:** PyPDF2 (with optional OCR support via Tesseract and pdf2image)
- **Data Storage:** Diskcache (for job details and user sessions)
- **Containerization:** Docker
- **Deployment:** Render.com

### Key Modules

- `src/core/playwright_job_parser.py`: Orchestrates browser automation, login, job scraping, and AI evaluation.
- `src/core/resume_utils.py`: Extracts and processes resume data, with special handling for test/demo users.
- `src/core/apply_to_job.py`: Automates the application process for selected jobs.
- `src/core/job_evaluator.py`: Evaluates job fit using AI.
- `src/web/app.py`: Flask web server, handles user sessions, job swiping UI, and API endpoints.
- `src/utils/config.py`: Centralized configuration and shared state.

### Frontend

- The UI is rendered using HTML templates (see `index_template.py`), designed for a clean, modern, and mobile-friendly experience.
- Users swipe through jobs, see detailed job info, and can accept/reject/apply with one click.

---

## How It Works

1. **Login:** User logs in with their WaterlooWorks credentials (handled securely in the backend).
2. **Resume Extraction:** The system downloads and parses the user's resume to understand their background.
3. **Job Scraping:** Playwright automates the browser to log in, navigate, and scrape all available job postings.
4. **AI Evaluation:** Each job is scored for fit using the user's resume and preferences.
5. **Job Swiping:** The user is presented with jobs in order of predicted fit, and can accept/reject/apply.
6. **Automated Application:** For accepted jobs, the system can auto-apply on the user's behalf.

---

## Local Development

### Prerequisites

- Python 3.8+
- [Node.js](https://nodejs.org/) (for Playwright browser install, if running locally)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and [Poppler](https://poppler.freedesktop.org/) (optional, for image-based PDF resume support)
- Docker (for containerized deployment)

### Setup

1. **Clone the repo:**
   ```bash
   git clone <your-repo-url>
   cd job-match
   ```

2. **Install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   playwright install
   ```

4. **(Optional) Install Tesseract and Poppler for OCR:**
   - On Ubuntu: `sudo apt-get install tesseract-ocr poppler-utils`
   - On Windows: Download and add to PATH (see code comments in `resume_utils.py`).

5. **Run the app:**
   ```bash
   export FLASK_APP=src.web.app:app
   flask run
   ```

6. **Access the UI:**  
   Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Deployment

### Docker

The app is fully containerized. The provided `Dockerfile` uses the official Playwright Python image for maximum compatibility.

**Build and run locally:**
```bash
docker build -t job-match .
docker run -p 5000:5000 job-match
```

### Render.com

Deployment is automated via `render.yaml`. On push, Render will:

- Build the Docker image
- Set environment variables (including a secret key)
- Expose the app on a public URL

**Health checks** and **auto-deploy** are enabled.

### Production Infrastructure

#### Hosting

The production instance of this application is hosted on a user-managed EC2 server (Ubuntu) for reliability and security, with regular backups and monitoring. The public domain name is provided and managed by Duckorg.

#### Nginx Reverse Proxy

Nginx is used as a reverse proxy in front of the Flask application. This setup provides several benefits:

- **TLS/SSL Termination:** Nginx handles HTTPS connections, ensuring secure communication between users and the server.
- **Load Balancing & Security:** Nginx can be configured to limit request rates, block malicious traffic, and serve static files efficiently.
- **Process Management:** The Flask app runs behind a WSGI server (such as Gunicorn or uWSGI), and Nginx forwards incoming requests to the backend, ensuring smooth operation and better resource management.

#### Deployment Workflow

- The Flask app is deployed on the EC2 instance, typically using Docker for environment consistency.
- Nginx is configured to listen on ports 80 (HTTP) and 443 (HTTPS), forwarding requests to the Flask backend running on an internal port (e.g., 29000).
- The `render.yaml` and `Dockerfile` in the repository provide reproducible deployment instructions.
- For updates, the app can be redeployed using the provided `redeploy.sh` script.

#### Example Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-duckorg-domain.com;

    location / {
        proxy_pass http://localhost:29000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

> **Note:** For production, always enable HTTPS and use strong TLS certificates. The domain name and DNS are managed by Duckorg.

---

## Configuration

- All configuration and shared state are managed in `src/utils/config.py`.
- Environment variables (for secrets, ports, etc.) are set in `render.yaml` and/or your local environment.

---

## Testing

- Tests are located in the `tests/` directory.
- Example: `tests/test_resume_utils.py` covers resume extraction logic.

Run tests with:
```bash
pytest tests/
```

---

## Known Limitations

- **WaterlooWorks UI changes:** If WaterlooWorks updates their UI, selectors may need to be updated.
- **DUO/MFA:** The system supports DUO, but manual intervention may be required for new devices.
- **PDF OCR:** Image-based resumes require Tesseract/Poppler and may not be as accurate as text-based PDFs.
- **OpenAI API:** Requires a valid API key and may incur costs.

---

## Contributing

Pull requests and issues are welcome! Please open an issue for bugs, feature requests, or selector breakage due to WaterlooWorks changes.

---

## License

MIT License

---

## Acknowledgements

- University of Waterloo students for feedback and testing
- OpenAI for AI APIs
- Playwright for robust browser automation

---

**Let's make job searching smarter, faster, and less painful for everyone!** 