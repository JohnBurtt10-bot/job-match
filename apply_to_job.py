import asyncio
import logging

async def apply_to_job(job_id: int, context):
    job_id_str = str(job_id)
    logging.info(f"Attempting to apply to job ID: {job_id_str}")
    try:
        # # Open new tab
        # context = page.context
        # new_page = await context.new_page()
        page = await context.new_page()
        apply_page = None
        await page.goto("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
        # Search for job
        search_input = await page.wait_for_selector("[name='emptyStateKeywordSearch']", timeout=10000)
        await search_input.fill(job_id_str)
        await search_input.press("Enter")
        await asyncio.sleep(2)
        # Click Apply button
        try:
            try:
                apply_btn = await page.wait_for_selector(
                    f"//tr[.//span[contains(text(),'{job_id_str}')]]//button[@aria-label='Apply']",
                    timeout=10000
                )
            except Exception:
                await page.close()
                return True
            await asyncio.sleep(0.2)
            # Remove target attribute if present (prevents new tab)
            async with context.expect_page() as new_page_info:
                await apply_btn.click()
            apply_page = await new_page_info.value
            logging.info("Clicked Apply")
            try:
                default_radio = await apply_page.wait_for_selector(
                    "//input[@type='radio' and @value='defaultPkg' and @name='applyOption']",
                    timeout=1000
                )
            except Exception:
                if apply_page:
                    await apply_page.close()
                await page.close()
                await asyncio.sleep(1)
                return await shortlist_job(job_id, context=context)
            await default_radio.evaluate("el => el.click()")
            final_apply = await apply_page.wait_for_selector(
                "//button[@type='button' and contains(@class, 'btn__hero--text') and contains(@class, 'btn--info') and contains(@class, 'js--ui-wizard-next-btn')]",
                timeout=1000
            )
            await final_apply.click()
            logging.info("Application submitted")
            # Close any new page opened
            await apply_page.close()
            await page.close()
            return True
        except Exception as e:
            logging.error(f"Failed to apply to job ID {job_id_str}: {e}", exc_info=True)
            raise e
    except Exception as e:
        logging.error(f"Error in apply_to_job: {e}", exc_info=True)
        return False

async def shortlist_job(job_id: int, context=None):
    job_id_str = str(job_id)
    logging.info(f"Attempting to shortlist job ID: {job_id_str}")
    try:
        new_page = await context.new_page()
        await new_page.goto("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
        search_input = await new_page.wait_for_selector("[name='emptyStateKeywordSearch']", timeout=10000)
        await search_input.fill(job_id_str)
        await search_input.press("Enter")
        try:
            # check if a button exists
            try:
                await new_page.wait_for_selector(
                    "//button[@aria-label='Change My Jobs Folder' and @type='button' and contains(@class, 'btn__small--text') and contains(@class, 'btn--info') and contains(@class, 'plain') and contains(@class, 'btn--icon-only')]",
                    timeout=1000
                )
                logging.info("Job already shortlisted")
                await new_page.close()
                return True
            except Exception:
                pass
            # <button aria-label="Save to My Jobs Folder" type="button" class="btn__small--text btn--info plain btn--icon-only"><i class="material-icons">create_new_folder</i></button>
            save_to_my_jobs_folder_btn = await new_page.wait_for_selector(
                "//button[@aria-label='Save to My Jobs Folder' and @type='button' and contains(@class, 'btn__small--text') and contains(@class, 'btn--info') and contains(@class, 'plain') and contains(@class, 'btn--icon-only')]",
                timeout=10000
            )
            # Ensure the element is attached to the DOM before clicking
            for _ in range(3):
                try:
                    await save_to_my_jobs_folder_btn.is_visible()
                    await save_to_my_jobs_folder_btn.click()
                    break
                except Exception as e:
                    # Re-query the element if not attached
                    save_to_my_jobs_folder_btn = await new_page.query_selector(
                        "//button[@aria-label='Save to My Jobs Folder' and @type='button' and contains(@class, 'btn__small--text') and contains(@class, 'btn--info') and contains(@class, 'plain') and contains(@class, 'btn--icon-only')]"
                    )
                    if save_to_my_jobs_folder_btn is None:
                        pass
            else:
                pass
            # Try to toggle shortlist checkbox
            try:
                chk = await new_page.wait_for_selector(
                    "//label[.//p[text()='AutoShortlist']]//input[@type='checkbox']",
                    timeout=5000
                )
                for _ in range(3):
                    try:
                        await chk.is_visible()
                        # javascript click (correct syntax)
                        await chk.evaluate("el => el.click()")
                        break
                    except Exception as e:
                        chk = await new_page.query_selector(
                            "//label[.//p[text()='AutoShortlist']]//input[@type='checkbox']"
                        )
                        if chk is None:
                            raise e
                else:
                    raise Exception("AutoShortlist checkbox could not be clicked after retries")
            except Exception:
                # Try create new folder
                chk = await new_page.wait_for_selector(
                    "//label[.//p[text()='Create a new folder']]//input[@type='checkbox']",
                    timeout=5000
                )
                for _ in range(3):
                    try:
                        await chk.is_visible()
                        await chk.click()
                        break
                    except Exception as e:
                        chk = await new_page.query_selector(
                            "//label[.//p[text()='Create a new folder']]//input[@type='checkbox']"
                        )
                        if chk is None:
                            pass
                else:
                    raise Exception("Create a new folder checkbox could not be clicked after retries")
                logging.info("Create a new folder checkbox clicked")
                folder_name_input = await new_page.wait_for_selector(
                    "//input[@id='sidebarFolderNameInput' and @class='input--box display--block']",
                    timeout=5000
                )
                for _ in range(3):
                    try:
                        await folder_name_input.is_visible()
                        await folder_name_input.fill("AutoShortlist")
                        break
                    except Exception as e:
                        folder_name_input = await new_page.query_selector(
                            "//input[@id='sidebarFolderNameInput' and @class='input--box display--block']"
                        )
                        if folder_name_input is None:
                            pass
                else:
                    raise Exception("Folder name input could not be filled after retries")
                logging.info("New folder created and saved")
            save_btn = await new_page.wait_for_selector(
                "//button[@class='btn__hero--text btn--default margin--r--s width--100' and normalize-space()='Save']",
                timeout=10000
            )
            for _ in range(3):
                try:
                    await save_btn.is_visible()
                    await save_btn.click()
                    break
                except Exception as e:
                    save_btn = await new_page.query_selector(
                        "//button[@class='btn__hero--text btn--default margin--r--s width--100' and normalize-space()='Save']"
                    )
                    if save_btn is None:
                        pass
            else:
                raise Exception("Save button could not be clicked after retries")
            logging.info("Clicked Save button")
            await new_page.close()
            return True
        except Exception:
            logging.error("Failed to shortlist job", exc_info=True)
            await new_page.close()
            return False
    except Exception as e:
        logging.error(f"Error in shortlist_job: {e}", exc_info=True)
        return False