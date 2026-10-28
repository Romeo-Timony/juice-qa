import json
from playwright.sync_api import sync_playwright

def inspect_registration_ui():
    findings = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto("http://localhost:3000/#/register")
        page.wait_for_timeout(1000)
        
        # Dismiss overlays
        try:
            page.keyboard.press("Escape")
            if page.locator("a.cc-btn").is_visible():
                page.locator("a.cc-btn").click()
        except Exception:
            pass
        page.wait_for_timeout(500)
        
        # 1. Initial State
        btn = page.locator("#registerButton")
        findings["initial_button_disabled"] = btn.is_disabled()
        
        # 2. Email Validation: empty touch
        email_inp = page.locator("#emailControl")
        email_inp.click()
        email_inp.blur()
        err_email_req = page.locator("mat-error").first.inner_text() if page.locator("mat-error").count() > 0 else ""
        findings["email_required_error"] = err_email_req
        
        # Invalid email format
        email_inp.fill("invalid-email-format")
        email_inp.blur()
        err_email_fmt = page.locator("mat-error").first.inner_text() if page.locator("mat-error").count() > 0 else ""
        findings["email_format_error"] = err_email_fmt
        
        # 3. Password Validation: short password
        pwd_inp = page.locator("#passwordControl")
        pwd_inp.fill("1234")
        pwd_inp.blur()
        err_pwd = page.locator("mat-error:has-text('5-40')").inner_text() if page.locator("mat-error:has-text('5-40')").count() > 0 else ""
        findings["password_length_error"] = err_pwd
        
        # 4. Repeat Password Mismatch
        pwd_inp.fill("ValidPass123!")
        repeat_inp = page.locator("#repeatPasswordControl")
        repeat_inp.fill("DifferentPass123!")
        repeat_inp.blur()
        err_mismatch = page.locator("mat-error:has-text('match')").inner_text() if page.locator("mat-error:has-text('match')").count() > 0 else ""
        findings["password_mismatch_error"] = err_mismatch
        
        # 5. Password Advice Toggle
        toggle = page.locator("mat-slide-toggle")
        toggle.click()
        page.wait_for_timeout(300)
        advice_visible = page.locator("app-password-strength-info").is_visible()
        findings["password_advice_panel_visible"] = advice_visible
        
        # 6. Security Questions options count
        sq_select = page.locator("mat-select[name='securityQuestion'], .security-container mat-select").first
        sq_select.click(force=True)
        page.wait_for_selector("mat-option", state="visible", timeout=3000)
        options_count = page.locator("mat-option").count()
        first_option = page.locator("mat-option").first.inner_text()
        findings["security_questions_count"] = options_count
        findings["first_security_question"] = first_option
        page.locator("mat-option").first.click()
        
        # 7. Form Complete -> Button Enabled Check
        email_inp.fill("valid_unique_user@juice-sh.op")
        repeat_inp.fill("ValidPass123!")
        ans_inp = page.locator("#securityAnswerControl")
        ans_inp.fill("MySecretAnswer")
        findings["button_enabled_when_valid"] = not btn.is_disabled()
        
        browser.close()
        
    print(json.dumps(findings, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    inspect_registration_ui()
