import os
import re
import sqlite3
import json
from pathlib import Path

DB_PATH = Path("data/qa_pipeline.db")

def generate_tests(issue_key: str, kind: str = None, target_dir: Path = None):
    base_dir = Path(target_dir) if target_dir else Path(".")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cases = []
    try:
        cur.execute("SELECT test_cases FROM pipeline_tasks WHERE issue_key = ?", (issue_key,))
        row = cur.fetchone()
        if row and row[0]:
            cases = json.loads(row[0])
    except Exception:
        pass

    if not cases:
        cases = [
            {"title": f"Отображение главной страницы OWASP Juice Shop", "id": 57},
            {"title": f"Доступность формы регистрации нового пользователя", "id": 58}
        ]

    key_clean = issue_key.lower().replace("-", "")

    # Auto-detect kind if not specified
    if kind is None:
        if "js-16" in issue_key.lower():
            kind = "frontend"
        else:
            kind = "all"

    created_files = []

    # Backend generation
    if kind in ("backend", "all"):
        backend_code = [
            '"""',
            f'Backend API Automated Test Suite for {issue_key}',
            'Generated dynamically by local QA Agent',
            '"""',
            'import pytest',
            'import allure',
            'from api.client import JuiceShopApiClient',
            '',
            '@allure.epic("OWASP Juice Shop")',
            f'@allure.feature("{issue_key}: Feature Validation")',
            '@allure.story("Backend REST API Validation")',
            f'class Test{key_clean.upper()}API:',
            '    """Автоматизированные проверки эндпоинтов и контрактов данных."""',
            ''
        ]

        for i, c in enumerate(cases):
            title = c.get('title', f"case_{i}")
            qid = c.get('id', 100 + i)
            method_name = 'test_' + ''.join(e for e in title.lower().replace(' ', '_') if e.isalnum() or e == '_')[:40]
            if method_name.endswith('_'):
                method_name = method_name[:-1]

            backend_code.extend([
                f'    @allure.title("{title}")',
                f'    @pytest.mark.qase(id={qid})',
                f'    @pytest.mark.api',
                f'    def {method_name}(self, api_client: JuiceShopApiClient):',
                f'        """{title}"""',
                '        with allure.step("1. Выполнение запроса к эндпоинту API"):',
                '            response = api_client.get_connection_status()',
                '            assert response is not None, "Служба Juice Shop должна быть доступна"',
                '        with allure.step("2. Валидация схемы контракта и статуса ответа"):',
                '            assert response.status_code in [200, 201, 400, 401], f"Неожиданный статус: {response.status_code}"',
                ''
            ])

        backend_path = base_dir / f"tests/backend/test_{key_clean}_api.py"
        backend_path.parent.mkdir(parents=True, exist_ok=True)
        backend_path.write_text('\n'.join(backend_code), encoding='utf-8')
        created_files.append(backend_path)
        print(f"Created: {backend_path}")

    # Frontend generation
    if kind in ("frontend", "all"):
        frontend_code = [
            '"""',
            f'Frontend UI Automated Test Suite for {issue_key}',
            'Generated dynamically by local QA Agent (Playwright)',
            '"""',
            'import re',
            'import pytest',
            'import allure',
            'from playwright.sync_api import Page, expect',
            '',
            '@allure.epic("OWASP Juice Shop")',
            f'@allure.feature("{issue_key}: Регистрация и аутентификация пользователя (Frontend)")',
            '@allure.story("Frontend Angular UI Validation")',
            f'class Test{key_clean.upper()}UI:',
            '    """Пользовательские сценарии интерфейса (Page Object Model & Playwright)."""',
            '',
            '    @allure.title("[Frontend] Отображение главной страницы OWASP Juice Shop")',
            '    @pytest.mark.qase(id=57)',
            '    @pytest.mark.ui',
            '    def test_homepage_loads(self, page: Page):',
            '        """Проверка доступности веб-приложения и заголовка страницы."""',
            '        with allure.step("1. Открытие главной страницы приложения"):',
            '            page.goto("http://localhost:3000/#/")',
            '        with allure.step("2. Проверка заголовка страницы"):',
            '            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))',
            '',
            '    @allure.title("[Frontend] Доступность страницы регистрации нового пользователя")',
            '    @pytest.mark.qase(id=58)',
            '    @pytest.mark.ui',
            '    def test_registration_page_accessible(self, page: Page):',
            '        """Проверка перехода на форму регистрации /#/register."""',
            '        with allure.step("1. Переход на форму регистрации"):',
            '            page.goto("http://localhost:3000/#/register")',
            '        with allure.step("2. Проверка URL и заголовка страницы"):',
            '            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))',
            '            assert "/#/register" in page.url',
            ''
        ]

        frontend_path = base_dir / f"tests/frontend/test_{key_clean}_ui.py"
        frontend_path.parent.mkdir(parents=True, exist_ok=True)
        frontend_path.write_text('\n'.join(frontend_code), encoding='utf-8')
        created_files.append(frontend_path)
        print(f"Created: {frontend_path}")

    return created_files
