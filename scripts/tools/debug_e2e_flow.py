from playwright.sync_api import sync_playwright
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:3000/#/register')
    
    # Dismiss banner
    try:
        page.locator('button[aria-label="Close Welcome Banner"]').click(timeout=2000)
    except Exception:
        pass

    ts = int(time.time() * 1000)
    email = f'debug_user_{ts}@juice-sh.op'
    page.locator('#emailControl').fill(email)
    page.locator('#passwordControl').fill('Password123!')
    page.locator('#repeatPasswordControl').fill('Password123!')
    
    # select question
    page.locator('mat-select[name="securityQuestion"]').click()
    page.wait_for_selector('mat-option', timeout=3000)
    page.locator('mat-option').first.click()
    page.locator('#securityAnswerControl').fill('Answer123')
    
    page.locator('#registerButton').click()
    page.wait_for_timeout(2000)
    print('URL after register:', page.url)

    # now login
    page.goto('http://localhost:3000/#/login')
    page.locator('#email').fill(email)
    page.locator('#password').fill('Password123!')
    page.locator('#loginButton').click()
    
    try:
        page.wait_for_function('() => !!localStorage.getItem("token")', timeout=5000)
        token = page.evaluate('() => localStorage.getItem("token")')
        print('Token exists:', bool(token), 'Length:', len(token) if token else 0)
        print('URL after login:', page.url)
    except Exception as e:
        print('Login wait error:', e)
        print('Current URL:', page.url)
        print('Local storage dump:', page.evaluate('() => JSON.stringify(window.localStorage)'))

    browser.close()
