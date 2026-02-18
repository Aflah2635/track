from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    # 1. Login
    print("Logging in...")
    page.goto("http://127.0.0.1:8000/users/login/")
    page.fill("input[name='username']", "test_pw_user")
    page.fill("input[name='password']", "password123")
    page.click("button[type='submit']")
    
    # Wait for dashboard
    page.wait_for_url("**/dashboard/")
    print("Logged in successfully.")

    # 2. Go to Manage Accounts
    print("Navigating to Manage Accounts...")
    page.goto("http://127.0.0.1:8000/accounts/manage/")
    
    # 3. Take Screenshot
    page.screenshot(path="accounts_managed.png", full_page=True)
    print("Screenshot saved to accounts_managed.png")
    
    # 4. Verify presence of "Frozen" text
    content = page.content()
    if "Frozen" in content:
        print("SUCCESS: 'Frozen' label found on page.")
        # Check count of frozen text
        count = content.count("Frozen")
        print(f"Found 'Frozen' {count} times.")
    else:
        print("FAILURE: 'Frozen' label NOT found.")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
