import logging
from playwright.async_api import async_playwright

async def extract_job_details(page, row):
    job = {}
    try:
        title_el = await row.query_selector("td:nth-child(2) a")
        job['title'] = await title_el.inner_text() if title_el else ""
        company_el = await row.query_selector("td:nth-child(3)")
        job['company'] = await company_el.inner_text() if company_el else ""

        # Click the job title link to open the job details panel
        if title_el:
            await title_el.click()
            # Wait for the job info panel to appear
            job_info_panel = await page.wait_for_selector("div.is--long-form-reading", timeout=15000)
            # Try both selectors for key-value containers
            key_value_containers = await job_info_panel.query_selector_all("div.tag__key-value-list.js--question--container")
            if not key_value_containers:
                key_value_containers = await job_info_panel.query_selector_all("xpath=//div[contains(@class, 'row') and ./span[contains(@class, 'label')]]")
            # For each container, extract key and value
            for container in key_value_containers:
                try:
                    key_el = await container.query_selector("span.label")
                    key = (await key_el.inner_text()).strip() if key_el else ""
                    value = ""
                    value_el = await container.query_selector("p")
                    if not value_el:
                        value_el = await container.query_selector("div:not([class*='label'])")
                    if value_el:
                        value = (await value_el.inner_text()).strip()
                    else:
                        all_text = (await container.inner_text()).strip()
                        value = all_text.replace(key, '').strip()
                    if key:
                        job[key] = value
                except Exception:
                    continue
            # Close the job info panel (try close button, fallback to browser back)
            try:
                close_btn = await page.query_selector("//button[contains(@class, 'btn__default--text') and .//i[text()='close']]", strict=False)
                await close_btn.click()
            except Exception:
                await page.go_back()
    except Exception as e:
        job['error'] = str(e)
    return job

async def get_total_pages(page):
    # Find all pagination links and return the highest page number
    await page.wait_for_selector(".pagination__link", timeout=10000)
    links = await page.query_selector_all(".pagination__link")
    page_numbers = []
    for link in links:
        text = (await link.inner_text()).strip()
        if text.isdigit():
            page_numbers.append(int(text))
    return max(page_numbers) if page_numbers else 1

async def goto_jobs_page(page, page_num):
    # Only click pagination links for pages > 1
    if page_num == 1:
        # Assume already on page 1, just wait for rows
        await page.wait_for_selector("tr")
        return
    # Find the pagination link with the correct number and click it
    links = await page.query_selector_all(".pagination__link")
    for link in links:
        text = (await link.inner_text()).strip()
        if text == str(page_num):
            await link.click()
            await page.wait_for_selector("tr")
            await page.wait_for_timeout(1000)  # Wait for table to update
            return 