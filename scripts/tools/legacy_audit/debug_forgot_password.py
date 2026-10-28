import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright
from pages.register_page import RegisterPage
from pages.login_page import LoginPage

ts = int(time.time() * 1000)
email = f'recovery_ui_{ts}@juice-sh.op'
password = 'OriginalPassword123!'
new_password = 'NewSecurePassword456!'
security_answer = 'MySecret123'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 1. Register via RegisterPage
    reg = RegisterPage(page, 'http://localhost:3000')
    reg.open()
    reg.email_input.fill(email)
    reg.password_input.fill(password)
    reg.repeat_password_input.fill(password)
    reg.select_security_question(0)
    reg.security_answer_input.fill(security_answer)
    reg.register_button.click()
    page.wait_for_timeout(2000)
    print('Registered! Current URL:', page.url)

    # 2. Go to forgot password
    page.goto('http://localhost:3000/#/forgot-password')
    page.wait_for_timeout(1000)
    email_inp = page.locator('#email')
    email_inp.press_sequentially(email, delay=30)
    
    page.wait_for_selector('#securityAnswer:not([disabled])', timeout=5000)
    print('Security answer enabled for UI-registered user!')
    
    page.locator('#securityAnswer').fill(security_answer)
    page.locator('#newPassword').fill(new_password)
    page.locator('#newPasswordRepeat').fill(new_password)
    
    reset_btn = page.locator('#resetButton')
    print('Reset button disabled?', reset_btn.is_disabled())
    reset_btn.click()
    page.wait_for_timeout(2000)
    print('URL after reset:', page.url)
    
    # Check login with new password
    login_res = requests.post(
        'http://localhost:3000/rest/user/login',
        json={'email': email, 'password': new_password}
    )
    print('Login with new password status:', login_res.status_code)
    browser.close()
