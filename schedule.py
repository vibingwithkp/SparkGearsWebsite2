from playwright.sync_api import sync_playwright
import time

# ----------------------------------------------------
# CREDENTIALS
# ----------------------------------------------------
STUDENT_ID = "1074509"
PASSWORD = "Tiger410$!)python3 schedule.py"  # Put your actual password here

def run(playwright):
    print("🚀 Launching automated browser...")
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    try:
        print("🌐 Navigating to LCPS StudentVUE login...")
        page.goto("https://portal.lcps.org/PXP2_Login_Student.aspx?Skip1=true")

        print("🔑 Logging in...")
        page.fill("input[name='Account']", STUDENT_ID)
        page.fill("input[name='Password']", PASSWORD)
        page.click("input[name='btnEnter']")

        print("⏳ Waiting for dashboard...")
        page.wait_for_selector(".navigation", timeout=15000)

        print("📅 Navigating to Class Schedule...")
        page.click("text=Class Schedule")

        # 1. Wait for the schedule container/table to appear
        print("⏳ Waiting for schedule data to load...")
        schedule_selector = "table.dt-schedule, table.dx-datagrid-table, .panel-body, #divSchedule"
        page.wait_for_selector(schedule_selector, timeout=15000)
        time.sleep(2)  # Short pause to ensure full table rendering

        print("\n" + "="*60)
        print("                YOUR CLASS SCHEDULE DATA")
        print("="*60 + "\n")

        # 2. Query and extract all schedule rows
        rows = page.query_selector_all("tr")
        extracted_lines = []

        for row in rows:
            text = row.inner_text().strip()
            # Clean up spacing/tabs and ignore empty rows
            if text:
                clean_text = " | ".join([part.strip() for part in text.split("\t") if part.strip()])
                if clean_text not in extracted_lines:
                    extracted_lines.append(clean_text)

        # 3. Print extracted content to terminal
        if extracted_lines:
            for line in extracted_lines:
                print(f"  • {line}")
        else:
            # Fallback: grab full raw text block if table rows aren't standard <tr>
            raw_content = page.text_content(schedule_selector)
            print("--- Raw Schedule Text ---")
            print(raw_content.strip())

        print("\n" + "="*60)
        print("Browser closing in 10 seconds...")
        time.sleep(10)

    except Exception as e:
        print(f"\n❌ Scraping Error: {e}")
        time.sleep(5)
    
    finally:
        browser.close()

# Run automation
with sync_playwright() as p:
    run(p)