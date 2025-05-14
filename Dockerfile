FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# The browser is already installed in the base image
# No need to run playwright install

# Expose the port the app runs on
EXPOSE $PORT

# Command to run the application using shell form to handle environment variables
CMD python -m flask --app src.web.app:app run --host=0.0.0.0 --port=${PORT:-5000} 