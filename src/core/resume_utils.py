import logging
from playwright.async_api import async_playwright
import os
import json
import shutil
from src.utils.config import user_info, test_data
import pdb  # Add pdb import
from PyPDF2 import PdfReader
import tempfile
# OCR and image conversion imports
try:
    from pdf2image import convert_from_path
    import pytesseract
    # Set absolute paths for Poppler and Tesseract
    POPPLER_PATH = r"C:\poppler\Library\bin"
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR"
    pytesseract.pytesseract.tesseract_cmd = os.path.join(TESSERACT_PATH, 'tesseract.exe')
except ImportError:
    convert_from_path = None
    pytesseract = None

def extract_text_from_pdf(pdf_path, username=None):
    """Extract text from a PDF file. Returns error message if PDF is image-based.
    For jrburtt@uwaterloo.ca, uses predefined resume data from config."""
    
    # Special case for jrburtt@uwaterloo.ca
    if username == "jrburtt@uwaterloo.ca":
        logging.info("Using predefined resume data for jrburtt@uwaterloo.ca")
        # Initialize user_info with test_data
        if "jrburtt@uwaterloo.ca" not in user_info:
            user_info["jrburtt@uwaterloo.ca"] = test_data
        
        # Format the work experience into a resume-like text
        resume_text = "WORK EXPERIENCE\n\n"
        for exp in user_info["jrburtt@uwaterloo.ca"]["work_experience"]:
            resume_text += f"{exp['company']} {exp['duration']}\n"
            resume_text += f"{exp['role']} {exp['location']}\n"
            resume_text += "\n"
        resume_text += "\nSKILLS\n\n"
        resume_text += "Languages: " + ", ".join(user_info["jrburtt@uwaterloo.ca"]["skills"]["languages"]) + "\n"
        resume_text += "Frameworks: " + ", ".join(user_info["jrburtt@uwaterloo.ca"]["skills"]["frameworks"]) + "\n"
        return resume_text

    try:
        logging.info(f"Attempting to extract text from PDF: {pdf_path}")
        reader = PdfReader(pdf_path)
        logging.info(f"PDF has {len(reader.pages)} pages")
        
        text = ""
        empty_pages = 0
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if not page_text or len(page_text.strip()) < 10:
                empty_pages += 1
            else:
                text += page_text + "\n"
            logging.info(f"Page {i+1} extracted text length: {len(page_text) if page_text else 0}")
        
        # If all pages are empty or nearly empty, assume image-based
        if empty_pages == len(reader.pages):
            error_msg = "This appears to be an image-based PDF. Text extraction is not possible. Please provide a text-based PDF."
            logging.error(error_msg)
            return error_msg
        
        logging.info(f"Total extracted text length: {len(text)}")
        return text.strip()
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return None

async def get_resume_details(page, username):
    """Extract resume text from the resume page."""
    # Special case for jrburtt@uwaterloo.ca - use test_data directly
    if username == "jrburtt@uwaterloo.ca":
        logging.info("Using predefined resume data for jrburtt@uwaterloo.ca")
        # Initialize user_info with test_data
        if "jrburtt@uwaterloo.ca" not in user_info:
            user_info["jrburtt@uwaterloo.ca"] = test_data
        
        # Format the work experience into a resume-like text
        resume_text = "WORK EXPERIENCE\n\n"
        for exp in user_info["jrburtt@uwaterloo.ca"]["work_experience"]:
            # Handle both string and list duration formats
            duration = exp['duration']
            if isinstance(duration, list):
                duration = ", ".join(duration)
            resume_text += f"{exp['company']} {duration}\n"
            resume_text += f"{exp['role']} {exp['location']}\n"
            resume_text += "\n"
        resume_text += "\nSKILLS\n\n"
        resume_text += "Languages: " + ", ".join(user_info["jrburtt@uwaterloo.ca"]["skills"]["languages"]) + "\n"
        resume_text += "Frameworks: " + ", ".join(user_info["jrburtt@uwaterloo.ca"]["skills"]["frameworks"]) + "\n"
        
        # Store resume text in user_info
        user_info["jrburtt@uwaterloo.ca"]["resume_text"] = resume_text
        logging.info("Resume text from test data stored in memory")
        return resume_text

    # For other users, proceed with PDF download and extraction
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
            my_program_btn = await page.wait_for_selector("button.btn__default--text.btn--info", timeout=10000)
            await my_program_btn.click()
            await page.wait_for_timeout(2000)  # Wait for any transitions/loading
        except Exception:
            # If not redirected, continue normally
            pass

        # Click on the resume link
        resume_link = await page.wait_for_selector("a.simple--stat-card__bottom.font--12.pdfPreview", timeout=20000)
        await resume_link.click()
        await page.wait_for_timeout(2000)  # Wait for any transitions/loading

        # Click on the download button
        download_btn = await page.wait_for_selector("button.btn__default--text.btn--info.js--btn--download-pdf", timeout=20000)
        
        # Set up download path in temp directory
        download_path = os.path.join(temp_dir, "resume.pdf")
        
        # Set up download listener and download the file
        async with page.expect_download() as download_info:
            await download_btn.click()
            download = await download_info.value
            await download.save_as(download_path)
            
        logging.info(f"Resume downloaded to temporary location: {download_path}")
        
        # Extract text from PDF
        resume_text = extract_text_from_pdf(download_path, username)
        
        # Delete the PDF file immediately after extracting text
        try:
            os.remove(download_path)
            logging.info(f"Deleted PDF file after text extraction: {download_path}")
        except Exception as e:
            logging.error(f"Error deleting PDF file {download_path}: {e}")
        
        if resume_text:
            # Store resume text in user_info
            if username not in user_info:
                user_info[username] = {}
            user_info[username]["resume_text"] = resume_text
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
    # Special case for jrburtt@uwaterloo.ca - skip PDF download
    if username == "jrburtt@uwaterloo.ca":
        logging.info("Using predefined resume data for jrburtt@uwaterloo.ca")
        # Initialize user_info with test_data
        if "jrburtt@uwaterloo.ca" not in user_info:
            user_info["jrburtt@uwaterloo.ca"] = test_data
        
        # Format the work experience into a resume-like text
        resume_text = "WORK EXPERIENCE\n\n"
        for exp in user_info["jrburtt@uwaterloo.ca"]["work_experience"]:
            # Handle both string and list duration formats
            duration = exp['duration']
            if isinstance(duration, list):
                duration = ", ".join(duration)
            resume_text += f"{exp['company']} {duration}\n"
            resume_text += f"{exp['role']} {exp['location']}\n"
            resume_text += "\n"
        resume_text += "\nSKILLS\n\n"
        resume_text += "Languages: " + ", ".join(user_info["jrburtt@uwaterloo.ca"]["skills"]["languages"]) + "\n"
        resume_text += "Frameworks: " + ", ".join(user_info["jrburtt@uwaterloo.ca"]["skills"]["frameworks"]) + "\n"
        
        # Store resume text in user_info
        user_info["jrburtt@uwaterloo.ca"]["resume_text"] = resume_text
        logging.info("Resume text from test data stored in memory")
        return {"resume_text": resume_text, "resume_path": None}  # Return a dict to match expected format

    # For other users, proceed with normal resume download
    try:
        if context is None:
            logging.error("No browser context provided")
            return None
            
        # Use provided context
        page = await context.new_page()
        try:
            # Get resume details and download the file
            result = await get_resume_details(page, username)
            if result:
                return {"resume_text": result, "resume_path": None}  # Return a dict to match expected format
            return None
        finally:
            await page.close()
    except Exception as e:
        logging.error(f"Error in get_resume_and_details: {e}")
        return None 