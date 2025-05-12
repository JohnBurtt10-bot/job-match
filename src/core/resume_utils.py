import logging
from playwright.async_api import async_playwright
import os
import json
import shutil
from src.utils.config import user_info
import pdb  # Add pdb import
from PyPDF2 import PdfReader
import tempfile

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return None

async def get_resume_details(page, username):
    """Extract resume text from the resume page."""
    temp_dir = None
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"resume_{username}_")
        logging.info(f"Created temporary directory for resume: {temp_dir}")
        
        # Wait for the resume section to load
        await page.goto("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
        
        # Check if we got redirected to dashboard
        try:
            await page.wait_for_url("**/myAccount/dashboard.htm", timeout=5000)
            my_program_btn = await page.wait_for_selector("button.btn__default--text.btn--info", timeout=5000)
            await my_program_btn.click()
            await page.wait_for_timeout(2000)  # Wait for any transitions/loading
        except Exception:
            # If not redirected, continue normally
            pass

        # Click on the resume link
        resume_link = await page.wait_for_selector("a.simple--stat-card__bottom.font--12.pdfPreview", timeout=10000)
        await resume_link.click()
        await page.wait_for_timeout(2000)  # Wait for any transitions/loading

        # Click on the download button
        download_btn = await page.wait_for_selector("button.btn__default--text.btn--info.js--btn--download-pdf", timeout=10000)
        
        # Set up download path in temp directory
        download_path = os.path.join(temp_dir, "resume.pdf")
        
        # Set up download listener and download the file
        async with page.expect_download() as download_info:
            await download_btn.click()
            download = await download_info.value
            await download.save_as(download_path)
            
        logging.info(f"Resume downloaded to temporary location: {download_path}")
        
        # Extract text from PDF
        resume_text = extract_text_from_pdf(download_path)
        
        # Delete the PDF file immediately after extracting text
        try:
            os.remove(download_path)
            logging.info(f"Deleted PDF file after text extraction: {download_path}")
        except Exception as e:
            logging.error(f"Error deleting PDF file {download_path}: {e}")
        
        if resume_text:
            # Update user_info with just the resume text
            user_info[username] = resume_text
            logging.info("Resume text extracted and stored in memory")
        
        return resume_text
    except Exception as e:
        logging.error(f"Error getting resume details: {e}")
        return None
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logging.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logging.error(f"Error cleaning up temporary directory {temp_dir}: {e}")

async def get_resume_and_details(username, password, context=None):
    """Get both resume file and details."""
    try:
        if context is None:
            logging.error("No browser context provided")
            return None
            
        # Use provided context
        page = await context.new_page()
        try:
            # Get resume details and download the file
            result = await get_resume_details(page, username)
            return result
        finally:
            await page.close()
    except Exception as e:
        logging.error(f"Error in get_resume_and_details: {e}")
        return None 