import pytest
import asyncio
import os
from src.core.resume_utils import get_resume_and_details, get_resume_details, download_resume
from playwright.async_api import async_playwright

# Test credentials - replace with test credentials
TEST_USERNAME = "jrburtt@uwaterloo.ca"
TEST_PASSWORD = "Birchwood718#"

@pytest.mark.asyncio
async def test_get_resume_and_details():
    """Test the main function that gets both resume and details."""
    result = await get_resume_and_details(TEST_USERNAME, TEST_PASSWORD)
    
    assert result is not None, "Function returned None"
    assert "resume_details" in result, "Missing resume_details in result"
    assert "resume_path" in result, "Missing resume_path in result"
    
    # Check if resume file exists
    assert os.path.exists(result["resume_path"]), "Resume file was not downloaded"
    
    # Check if resume details are not empty
    assert result["resume_details"], "Resume details are empty"

@pytest.mark.asyncio
async def test_get_resume_details():
    """Test getting resume details from a page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            os.path.join("user_data", TEST_USERNAME),
            headless=True
        )
        
        try:
            page = await browser.new_page()
            
            # Login
            await page.goto("https://waterlooworks.uwaterloo.ca/waterloo.htm?action=login")
            await page.fill("#userNameInput", TEST_USERNAME)
            await page.click("#nextButton")
            await page.fill("#passwordInput", TEST_PASSWORD)
            await page.click("#submitButton")
            
            # Wait for login to complete
            await page.wait_for_selector("a.items.active", timeout=10000)
            
            # Navigate to resume page
            await page.goto("https://waterlooworks.uwaterloo.ca/myAccount/co-op/resume.htm")
            
            # Get resume details
            details = await get_resume_details(page)
            
            assert details is not None, "Resume details are None"
            assert isinstance(details, dict), "Resume details should be a dictionary"
            assert len(details) > 0, "Resume details are empty"
            
        finally:
            await browser.close()

@pytest.mark.asyncio
async def test_download_resume():
    """Test downloading the resume."""
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            os.path.join("user_data", TEST_USERNAME),
            headless=True
        )
        
        try:
            page = await browser.new_page()
            
            # Login
            await page.goto("https://waterlooworks.uwaterloo.ca/waterloo.htm?action=login")
            await page.fill("#userNameInput", TEST_USERNAME)
            await page.click("#nextButton")
            await page.fill("#passwordInput", TEST_PASSWORD)
            await page.click("#submitButton")
            
            # Wait for login to complete
            await page.wait_for_selector("a.items.active", timeout=10000)
            
            # Download resume
            resume_path = await download_resume(page, TEST_USERNAME)
            
            assert resume_path is not None, "Resume path is None"
            assert os.path.exists(resume_path), "Resume file was not downloaded"
            assert os.path.getsize(resume_path) > 0, "Resume file is empty"
            
        finally:
            await browser.close()

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 