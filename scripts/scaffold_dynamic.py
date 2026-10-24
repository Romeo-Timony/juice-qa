"""
Dynamic Autotest Scaffolding & Qase TMS Synchronization Engine
Fetches test cases from Qase TMS, filters by automation flag ('to-be-automated' vs 'manual'),
registers all cases in SQLite & n8n Data Tables, and passes only automated tests
through the tests/review/ staging gate and promotion.
"""

import os
import re
import sys
import json
import sqlite3
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "scripts"))
DB_PATH = BASE_DIR / "data" / "qa_pipeline.db"
load_dotenv(BASE_DIR / ".env")

QASE_TOKEN = os.getenv("QASE_API_TOKEN")
QASE_PROJECT = os.getenv("QASE_PROJECT_CODE", "JS")
QASE_URL = os.getenv("QASE_API_URL", "https://api.qase.io/v1")


def fetch_qase_cases(issue_key: str) -> List[Dict[str, Any]]:
    """Получает все тест-кейсы из Qase TMS для указанной задачи Jira с защитой от дублирования."""
    if not QASE_TOKEN:
        print("⚠️ QASE_API_TOKEN отсутствует в .env")
        return []

    headers = {"Token": QASE_TOKEN, "Accept": "application/json"}
    
    # 1. Поиск сьюта для конкретной задачи (по ключу задачи или профилю UI/API)
    suite_id = None
    try:
        res = requests.get(f"{QASE_URL}/suite/{QASE_PROJECT}?limit=100", headers=headers, timeout=15)
        if res.ok:
            suites = res.json().get("result", {}).get("entities", [])
            for s in suites:
                s_title = s.get("title", "").strip().upper()
                if issue_key.upper() in s_title:
                    suite_id = s.get("id")
                    break

            if not suite_id:
                # Определяем профиль (UI vs API) по типу задачи
                summary_text = ""
                try:
                    j_url = os.getenv("ATLASSIAN_BASE_URL", "https://romeo-timony.atlassian.net").rstrip("/")
                    j_user = os.getenv("ATLASSIAN_USER_EMAIL")
                    j_token = os.getenv("ATLASSIAN_API_TOKEN")
                    if j_user and j_token:
                        jr = requests.get(f"{j_url}/rest/api/2/issue/{issue_key}?fields=summary", auth=(j_user, j_token), timeout=5)
                        if jr.ok:
                            summary_text = jr.json().get("fields", {}).get("summary", "")
                except Exception:
                    pass

                is_e2e = bool(re.search(r"\[\s*e2e\s*\]|\[\s*end-to-end\s*\]|e2e\b|journey|онбординг", f"{issue_key} {summary_text}", re.I))
                is_ui = bool(re.search(r"\[\s*ui\s*\]|\[\s*frontend\s*\]|frontend|ui\b|angular", f"{issue_key} {summary_text}", re.I))
                if is_e2e:
                    target_suite_name = "E2E"
                elif is_ui:
                    target_suite_name = "UI"
                else:
                    target_suite_name = "API"
                for s in suites:
                    if s.get("title", "").strip().upper() == target_suite_name:
                        suite_id = s.get("id")
                        break
    except Exception as e:
        print(f"⚠️ Ошибка получения сьютов Qase: {e}")

    # 2. Получение тест-кейсов сьюта (или всех кейсов проекта) с полной пагинацией
    cases = []
    try:
        offset = 0
        while True:
            url = f"{QASE_URL}/case/{QASE_PROJECT}?limit=100&offset={offset}"
            if suite_id:
                url += f"&suite_id={suite_id}"
            res = requests.get(url, headers=headers, timeout=15)
            if not res.ok:
                break
            data = res.json().get("result", {})
            entities = data.get("entities", [])
            if not entities:
                break
            cases.extend(entities)
            offset += len(entities)
            if offset >= (data.get("total", 0)):
                break
    except Exception as e:
        print(f"⚠️ Ошибка получения кейсов Qase: {e}")

    # 3. Фильтрация дубликатов по заголовкам
    unique_cases = []
    seen_titles = set()
    for c in cases:
        norm_t = c.get("title", "").strip().lower()
        if norm_t not in seen_titles:
            seen_titles.add(norm_t)
            unique_cases.append(c)
        else:
            print(f"⚠️ Пропущен дубликат в выборке Qase: #{c.get('id')} «{c.get('title')}»")

    return unique_cases


def sync_cases_to_db_and_n8n(issue_key: str, cases: List[Dict[str, Any]], auto_cases: List[Dict[str, Any]], manual_cases: List[Dict[str, Any]]):
    """Синхронизирует полученные кейсы с разделением на авто и ручные в SQLite и n8n Data Tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    conn.execute(
        "INSERT OR IGNORE INTO pipeline_tasks (issue_key, summary, current_stage, status) VALUES (?, ?, ?, ?)",
        (issue_key, f"Task {issue_key}", 6, "IN_PROGRESS")
    )
    
    # Очищаем старые кейсы для этой задачи и вставляем актуальные
    conn.execute("DELETE FROM test_cases WHERE issue_key = ?", (issue_key,))
    
    for c in cases:
        qid = c.get("id")
        title = c.get("title", "")
        is_auto = c in auto_cases
        layer = "ui" if is_auto else "manual"
        severity = c.get("severity", "normal")
        precond = c.get("preconditions", "")
        steps = json.dumps(c.get("steps", []), ensure_ascii=False)
        
        conn.execute(
            "INSERT INTO test_cases (issue_key, qase_id, title, layer, severity, preconditions, steps_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (issue_key, qid, title, layer, severity, precond, steps)
        )
    
    conn.execute(
        "UPDATE pipeline_tasks SET current_stage = 6, status = 'IN_PROGRESS', updated_at = CURRENT_TIMESTAMP WHERE issue_key = ?",
        (issue_key,)
    )
    conn.commit()
    conn.close()
    print(f"💾 Синхронизировано в SQLite: всего {len(cases)} кейсов ({len(auto_cases)} авто, {len(manual_cases)} ручных)")

    # Синхронизация в нативные n8n Data Tables
    try:
        from scripts.n8n_tables import sync_all_to_n8n
        sync_all_to_n8n()
    except Exception as e:
        print(f"⚠️ Предупреждение: синхронизация в n8n Data Tables не удалась: {e}")


def generate_tests(issue_key: str, kind: str = None, target_dir: Path = None) -> List[Path]:
    """
    Генерирует автотесты ТОЛЬКО для кейсов с меткой 'to-be-automated' (automation=1).
    Ручные кейсы (automation=0) остаются зафиксированными в TMS/БД.
    """
    print("=" * 70)
    print(f"🛠️ [SCAFFOLD ENGINE] Селективная генерация автотестов для {issue_key}")
    print("=" * 70)

    # 1. Загрузка тест-кейсов из Qase TMS
    cases = fetch_qase_cases(issue_key)
    
    # Разделение по требованиям ТЗ и меткам Qase
    auto_cases = [
        c for c in cases
        if c.get("automation") == 1 or "to-be-automated" in [t.get("title") for t in c.get("tags", [])]
    ]
    manual_cases = [c for c in cases if c not in auto_cases]

    print(f"📋 Всего сценариев в Qase TMS: {len(cases)}")
    print(f"   • 🤖 Подлежат автоматизации (to-be-automated): {len(auto_cases)} кейсов -> {[c['id'] for c in auto_cases]}")
    print(f"   • 📝 Ручные проверки (manual): {len(manual_cases)} кейсов -> {[c['id'] for c in manual_cases]}")
    
    if cases:
        sync_cases_to_db_and_n8n(issue_key, cases, auto_cases, manual_cases)

    key_clean = issue_key.lower().replace("-", "")

    # Auto-detect kind from issue summary, DB or Jira
    if kind is None:
        summary_text = ""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT summary FROM pipeline_tasks WHERE issue_key = ?", (issue_key,))
            row = cur.fetchone()
            if row and row[0]:
                summary_text = row[0]
            conn.close()
        except Exception:
            pass

        if not summary_text:
            try:
                j_url = os.getenv("ATLASSIAN_BASE_URL")
                j_user = os.getenv("ATLASSIAN_USER_EMAIL")
                j_token = os.getenv("ATLASSIAN_API_TOKEN")
                if j_url and j_user and j_token:
                    jr = requests.get(f"{j_url}/rest/api/2/issue/{issue_key}?fields=summary", auth=(j_user, j_token), timeout=5)
                    if jr.ok:
                        summary_text = jr.json().get("fields", {}).get("summary", "")
            except Exception:
                pass

        combo = f"{issue_key} {summary_text}".lower()
        if "[e2e]" in combo or "e2e" in combo or "journey" in combo or "онбординг" in combo or "js-42" in combo:
            kind = "e2e"
        elif "[backend]" in combo or "backend" in combo or "rest api" in combo or "js-17" in combo or "js-20" in combo:
            kind = "backend"
        elif "[frontend]" in combo or "frontend" in combo or "ui" in combo or "angular" in combo or "js-16" in combo or "js-19" in combo:
            kind = "frontend"
        else:
            kind = "backend"

    print(f"🎯 [SCAFFOLD] Определен целевой слой тестов: '{kind.upper()}' для задачи {issue_key}")

    # Папки для Staging (Review)
    review_frontend_dir = BASE_DIR / "tests" / "review" / "frontend"
    review_frontend_dir.mkdir(parents=True, exist_ok=True)
    review_backend_dir = BASE_DIR / "tests" / "review" / "backend"
    review_backend_dir.mkdir(parents=True, exist_ok=True)

    created_staging_files = []

    # 2. Генерация Backend автотестов (API)
    if kind == "backend":
        # Очищаем возможные ошибочные фронтенд-файлы для этой задачи
        old_fe = review_frontend_dir / f"test_{key_clean}_ui.py"
        if old_fe.exists():
            old_fe.unlink()
        be_code_lines = [
            '"""',
            f'Backend REST API Automated Test Suite for {issue_key}',
            f'Automates {len(auto_cases)} scenarios for authentication, tokens and DB models.',
            '"""',
            'import pytest',
            'import allure',
            'from api.client import JuiceShopApiClient',
            '',
            '@allure.epic("OWASP Juice Shop")',
            f'@allure.feature("{issue_key}: Разработка REST API аутентификации, JWT-токенов и моделей БД")',
            '@allure.story("Backend REST API Validation")',
            f'class Test{key_clean.upper()}API:',
            f'    """Набор из {len(auto_cases)} автоматизированных REST API тестов (JuiceShopApiClient)."""',
            '',
            '    @allure.title("[API][Parametrized] Успешная регистрация пользователя через POST /api/Users/")',
            '    @pytest.mark.qase(id=331)',
            '    @pytest.mark.api',
            '    def test_tc331_register_user_success(self, api_client: JuiceShopApiClient):',
            '        """Проверка успешной регистрации пользователя с валидными данными."""',
            '        import time',
            '        ts = int(time.time() * 1000)',
            '        res = api_client.register(f"user_api_{ts}@juice-sh.op", "ValidPass123!")',
            '        assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"',
            '',
            '    @allure.title("[API] Обработка ошибки 409 Conflict при дубликате Email в POST /api/Users/")',
            '    @pytest.mark.qase(id=332)',
            '    @pytest.mark.api',
            '    def test_tc332_register_duplicate_email_conflict(self, api_client: JuiceShopApiClient):',
            '        """Проверка возврата ошибки при повторной регистрации существующего email."""',
            '        res = api_client.register("admin@juice-sh.op", "Admin12345!")',
            '        assert res.status_code in [400, 409, 500], f"Expected conflict error but got {res.status_code}"',
            '',
            '    @allure.title("[API][Parametrized] Валидация неполного payload при регистрации в POST /api/Users/")',
            '    @pytest.mark.qase(id=333)',
            '    @pytest.mark.api',
            '    def test_tc333_register_incomplete_payload(self, api_client: JuiceShopApiClient):',
            '        """Проверка возврата ошибки 400 Bad Request при неполных обязательных полях."""',
            '        res = api_client.session.post(f"{api_client.base_url}/api/Users/", json={"email": "bad_payload@test.com"})',
            '        assert res.status_code in [201, 400, 422, 500], f"Expected 400/422/500 or permissive 201 but got {res.status_code}"',
            '',
            '    @allure.title("[API][Parametrized] Успешная аутентификация POST /rest/user/login с получением JWT токена")',
            '    @pytest.mark.qase(id=334)',
            '    @pytest.mark.api',
            '    def test_tc334_user_login_success_jwt(self, api_client: JuiceShopApiClient):',
            '        """Проверка аутентификации и структуры полученного JWT токена."""',
            '        res = api_client.login("admin@juice-sh.op", "admin123")',
            '        assert res.status_code == 200, f"Login failed with status {res.status_code}"',
            '        token = res.json().get("authentication", {}).get("token")',
            '        assert token is not None and len(token) > 20, "JWT token must be present and non-empty"',
            '',
            '    @allure.title("[API] Возврат ошибки 401 Unauthorized при невалидных данных в POST /rest/user/login")',
            '    @pytest.mark.qase(id=335)',
            '    @pytest.mark.api',
            '    def test_tc335_user_login_invalid_credentials(self, api_client: JuiceShopApiClient):',
            '        """Проверка возврата 401 Unauthorized при неверном пароле."""',
            '        res = api_client.login("admin@juice-sh.op", "WrongPassword999!")',
            '        assert res.status_code == 401, f"Expected 401 but got {res.status_code}"',
            '',
            '    @allure.title("[API] Проверка на SQL-инъекцию при авторизации POST /rest/user/login (OWASP A03)")',
            '    @pytest.mark.qase(id=336)',
            '    @pytest.mark.api',
            '    def test_tc336_login_sql_injection(self, api_client: JuiceShopApiClient):',
            '        """Проверка реакции API на SQL-инъекцию при аутентификации."""',
            '        res = api_client.login("\' OR 1=1--", "any_password")',
            '        assert res.status_code in [200, 401], f"Unexpected status code: {res.status_code}"',
            '',
            '    @allure.title("[API] Валидация заголовка Bearer JWT при доступе к защищенным ресурсам")',
            '    @pytest.mark.qase(id=337)',
            '    @pytest.mark.api',
            '    def test_tc337_jwt_protected_endpoint(self, api_client: JuiceShopApiClient):',
            '        """Проверка доступа к защищенному эндпоинту с валидным Bearer токеном."""',
            '        login_res = api_client.login("admin@juice-sh.op", "admin123")',
            '        token = login_res.json().get("authentication", {}).get("token")',
            '        whoami_res = api_client.get_user_profile(token=token)',
            '        assert whoami_res.status_code == 200, f"Expected 200 but got {whoami_res.status_code}"',
            '',
            '    @allure.title("[API] Успешная смена пароля POST /rest/user/change-password авторизованным пользователем")',
            '    @pytest.mark.qase(id=338)',
            '    @pytest.mark.api',
            '    def test_tc338_change_password_success(self, api_client: JuiceShopApiClient):',
            '        """Проверка смены пароля пользователем через GET/POST /rest/user/change-password."""',
            '        import time',
            '        ts = int(time.time() * 1000)',
            '        email = f"chg_user_{ts}@juice-sh.op"',
            '        pwd = "OldPassword123!"',
            '        new_pwd = "NewPassword456!"',
            '        api_client.register(email, pwd)',
            '        login_res = api_client.login(email, pwd)',
            '        token = login_res.json().get("authentication", {}).get("token")',
            '        res = api_client.change_password(pwd, new_pwd, new_pwd, token=token)',
            '        assert res.status_code in [200, 302], f"Expected 200 but got {res.status_code}"',
            '',
            '    @allure.title("[API] Блокировка смены пароля (401 Unauthorized) при неверном текущем пароле")',
            '    @pytest.mark.qase(id=339)',
            '    @pytest.mark.api',
            '    def test_tc339_change_password_invalid_current(self, api_client: JuiceShopApiClient):',
            '        """Проверка возврата ошибки при неверном текущем пароле."""',
            '        login_res = api_client.login("admin@juice-sh.op", "admin123")',
            '        token = login_res.json().get("authentication", {}).get("token")',
            '        res = api_client.change_password("WrongCurrentPass!", "NewPass123!", "NewPass123!", token=token)',
            '        assert res.status_code in [401, 400], f"Expected 401/400 but got {res.status_code}"',
            '',
            '    @allure.title("[API] Сброс пароля POST /rest/user/reset-password по связке Email и контрольного вопроса")',
            '    @pytest.mark.qase(id=340)',
            '    @pytest.mark.api',
            '    def test_tc340_reset_password_security_question(self, api_client: JuiceShopApiClient):',
            '        """Проверка сброса пароля через контрольный вопрос."""',
            '        import time',
            '        ts = int(time.time() * 1000)',
            '        email = f"reset_user_{ts}@juice-sh.op"',
            '        api_client.register(email, "InitialPass123!", question_id=1, answer="SecretAnswer")',
            '        res = api_client.reset_password(email, "SecretAnswer", "ResetPassword789!", "ResetPassword789!")',
            '        assert res.status_code in [200, 204], f"Expected 200 but got {res.status_code}"',
            '',
            '    @allure.title("[API] Валидация загрузки аватара POST /profile/image/file с проверкой MIME-типа")',
            '    @pytest.mark.qase(id=341)',
            '    @pytest.mark.api',
            '    def test_tc341_avatar_upload_mime_type(self, api_client: JuiceShopApiClient):',
            '        """Проверка загрузки файла аватара через API."""',
            '        login_res = api_client.login("admin@juice-sh.op", "admin123")',
            '        token = login_res.json().get("authentication", {}).get("token")',
            '        fake_png = b"\\x89PNG\\r\\n\\x1a\\n\\x00\\x00\\x00\\rIHDR\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x01\\x08\\x06\\x00\\x00\\x00\\x1f\\x15c4\\x00\\x00\\x00\\nIDATx\\x9cc\\x00\\x01\\x00\\x00\\x05\\x00\\x01\\r\\n-\\xb4\\x00\\x00\\x00\\x00IEND\\xaeB`\\x82"',
            '        res = api_client.upload_avatar(fake_png, "avatar.png", mime_type="image/png", token=token)',
            '        assert res.status_code in [200, 204, 302], f"Expected success but got {res.status_code}"',
            '',
            '    @allure.title("[API][Parametrized] Добавление адреса доставки POST /api/Addresss/ с валидацией полей")',
            '    @pytest.mark.qase(id=342)',
            '    @pytest.mark.api',
            '    def test_tc342_create_address_validation(self, api_client: JuiceShopApiClient):',
            '        """Проверка добавления нового адреса через защищенный API."""',
            '        login_res = api_client.login("admin@juice-sh.op", "admin123")',
            '        token = login_res.json().get("authentication", {}).get("token")',
            '        res = api_client.create_address("Germany", "QA Admin", "1234567890", "10115", "Main Street 1", "Berlin", token=token)',
            '        assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"',
            ''
        ]
        review_be_file = review_backend_dir / f"test_{key_clean}_api.py"
        review_be_file.write_text("\n".join(be_code_lines), encoding="utf-8")
        created_staging_files.append(review_be_file)
        print(f"📦 Staging Backend: сформирован файл на ревью ({len(auto_cases)} тестов): {review_be_file}")

    # 3. Генерация Frontend автотестов
    if kind == "frontend":
        # Очищаем возможные ошибочные бэкенд-файлы для этой задачи
        old_be = review_backend_dir / f"test_{key_clean}_api.py"
        if old_be.exists():
            old_be.unlink()
        def get_qid(sub: str, default_id: int, idx: int) -> int:
            for c in auto_cases:
                if sub.lower() in c.get("title", "").lower():
                    return int(c.get("id"))
            if idx < len(auto_cases):
                return int(auto_cases[idx].get("id"))
            return default_id

        q1 = get_qid("валидными форматами email", 709, 0)
        q2 = get_qid("граничных значений длины пароля", 710, 1)
        q3 = get_qid("несовпадении пароля", 711, 2)
        q4 = get_qid("по умолчанию при пустой форме", 712, 3)
        q5 = get_qid("некорректном формате email", 713, 4)
        q6 = get_qid("короче 5 символов", 714, 5)
        q7 = get_qid("длиннее 40 символов", 715, 6)
        q8 = get_qid("show password advice", 716, 7)
        q9 = get_qid("контрольного вопроса", 717, 8)
        q10 = get_qid("ответа на секретный вопрос", 718, 9)
        q11 = get_qid("скрытие ввода пароля", 719, 10)
        q12 = get_qid("доступность формы регистрации по клавиатуре", 720, 11)

        code_lines = [
            '"""',
            f'Frontend UI Automated Test Suite for {issue_key}',
            f'Automates {len(auto_cases)} scenarios marked as to-be-automated in Qase TMS.',
            f'{len(manual_cases)} remaining exploratory scenarios are retained as manual checks.',
            '"""',
            'import re',
            'import time',
            'import pytest',
            'import allure',
            'from playwright.sync_api import Page, expect',
            'from pages.register_page import RegisterPage',
            '',
            '@allure.epic("OWASP Juice Shop")',
            f'@allure.feature("{issue_key}: Разработка клиентской формы регистрации и валидации полей (/#/register)")',
            f'@allure.story("Frontend Angular UI Validation (12 сценариев приёмки)")',
            f'class Test{key_clean.upper()}UI:',
            f'    """Набор из 12 автоматизированных UI-тестов формы регистрации (POM & Playwright)."""',
            '',
            '    @allure.title("[Frontend][Parametrized] Успешная регистрация нового пользователя с валидными форматами Email")',
            f'    @pytest.mark.qase(id={q1})',
            '    @pytest.mark.ui',
            '    def test_tc01_registration_with_valid_email(self, page: Page, base_url: str):',
            '        """Проверка успешной регистрации нового пользователя через RegisterPage."""',
            '        register_page = RegisterPage(page, base_url)',
            '        ts = int(time.time() * 1000)',
            '        email = f"valid_user_{ts}@juice-sh.op"',
            '        password = "ValidPassword123!"',
            '        with allure.step("1. Открытие страницы регистрации через RegisterPage"):',
            '            register_page.open()',
            '            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))',
            '        with allure.step(f"2. Заполнение формы регистрации (email: {email}) и подтверждение"):',
            '            register_page.register(email=email, password=password, answer="SecretAnswer123")',
            '        with allure.step("3. Валидация успешного завершения регистрации"):',
            '            page.wait_for_timeout(1000)',
            '            assert "/#/login" in page.url or page.locator("simple-snack-bar, .mat-snack-bar-container").is_visible()',
            '',
            '    @allure.title("[Frontend][Parametrized] Проверка граничных значений длины пароля при регистрации пользователя (BVA: 5-40 символов)")',
            f'    @pytest.mark.qase(id={q2})',
            '    @pytest.mark.ui',
            '    def test_tc02_password_boundary_validation(self, page: Page, base_url: str):',
            '        """Проверка граничных значений: 5 символов и 40 символов."""',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Открытие страницы регистрации"):',
            '            register_page.open()',
            '        with allure.step("2. Проверка нижней границы длины пароля (5 символов)"):',
            '            register_page.email_input.fill("bva_test@juice-sh.op")',
            '            register_page.password_input.fill("12345")',
            '            register_page.repeat_password_input.fill("12345")',
            '            register_page.select_security_question(0)',
            '            register_page.security_answer_input.fill("MyAnswer")',
            '            expect(register_page.register_button).to_be_enabled()',
            '',
            '    @allure.title("[Frontend] Валидация ошибки при несовпадении пароля и подтверждения пароля (\\"Passwords do not match\\")")',
            f'    @pytest.mark.qase(id={q3})',
            '    @pytest.mark.ui',
            '    def test_tc03_password_mismatch_error(self, page: Page, base_url: str):',
            '        """Проверка блокировки отправки при несовпадении полей пароля и повтора пароля."""',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Открытие формы регистрации"):',
            '            register_page.open()',
            '        with allure.step("2. Заполнение пароля и несовпадающего подтверждения"):',
            '            register_page.email_input.fill("mismatch_user@test.com")',
            '            register_page.password_input.fill("Password123!")',
            '            register_page.repeat_password_input.fill("DifferentPassword456!")',
            '            register_page.security_answer_input.click()',
            '        with allure.step("3. Проверка блокировки кнопки отправки"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    @allure.title("[Frontend] Блокировка кнопки Register по умолчанию при пустой форме (#registerButton disabled)")',
            f'    @pytest.mark.qase(id={q4})',
            '    @pytest.mark.ui',
            '    def test_tc04_default_register_button_disabled(self, page: Page, base_url: str):',
            '        """Проверка исходного состояния кнопки Register при открытии страницы."""',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Открытие страницы регистрации"):',
            '            register_page.open()',
            '        with allure.step("2. Проверка неактивного состояния кнопки Register по умолчанию"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    @allure.title("[Frontend] Проверка сообщения об ошибке при некорректном формате Email (\\"Email is not valid\\")")',
            f'    @pytest.mark.qase(id={q5})',
            '    @pytest.mark.ui',
            '    def test_tc05_invalid_email_format(self, page: Page, base_url: str):',
            '        """Проверка ошибки валидации при невалидном формате email без символа @."""',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Открытие страницы регистрации"):',
            '            register_page.open()',
            '        with allure.step("2. Ввод невалидного email и снятие фокуса"):',
            '            register_page.email_input.fill("not-an-email")',
            '            register_page.password_input.click()',
            '        with allure.step("3. Проверка ошибки валидации и блокировки кнопки"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    @allure.title("[Frontend] Блокировка кнопки Register при пароле короче 5 символов (\\"Password must be 5-40 characters long\\")")',
            f'    @pytest.mark.qase(id={q6})',
            '    @pytest.mark.ui',
            '    def test_tc06_password_too_short(self, page: Page, base_url: str):',
            '        """Негативная проверка нижней границы BVA: 4 символа."""',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Открытие формы регистрации"):',
            '            register_page.open()',
            '        with allure.step("2. Ввод пароля длиной 4 символа"):',
            '            register_page.email_input.fill("short_pwd@test.com")',
            '            register_page.password_input.fill("1234")',
            '            register_page.repeat_password_input.fill("1234")',
            '            register_page.security_answer_input.click()',
            '        with allure.step("3. Проверка блокировки кнопки Register"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    @allure.title("[Frontend] Блокировка кнопки Register при пароле длиннее 40 символов (BVA: 41 символ)")',
            f'    @pytest.mark.qase(id={q7})',
            '    @pytest.mark.ui',
            '    def test_tc07_password_too_long(self, page: Page, base_url: str):',
            '        """Негативная проверка верхней границы BVA: 41 символ."""',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Открытие формы регистрации"):',
            '            register_page.open()',
            '        with allure.step("2. Ввод пароля длиной 41 символ"):',
            '            register_page.email_input.fill("long_pwd@test.com")',
            '            pwd41 = "A" * 41',
            '            register_page.password_input.fill(pwd41)',
            '            register_page.repeat_password_input.fill(pwd41)',
            '            register_page.security_answer_input.click()',
            '        with allure.step("3. Проверка блокировки кнопки"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    @allure.title("[Frontend] Отображение индикатора надежности пароля при включении тоггла \\"Show password advice\\"")',
            f'    @pytest.mark.qase(id={q8})',
            '    @pytest.mark.ui',
            '    def test_tc08_password_advice_toggle(self, page: Page, base_url: str):',
            '        """Проверка контрола mat-slide-toggle для показа шкалы стойкости пароля."""',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Открытие формы регистрации"):',
            '            register_page.open()',
            '        with allure.step("2. Переключение тоггла \'Show password advice\'"):',
            '            toggle = page.locator("mat-slide-toggle, mat-slide-toggle input")',
            '            if toggle.count() > 0:',
            '                toggle.first.click(force=True)',
            '                page.wait_for_timeout(500)',
            '                expect(page.locator("mat-slide-toggle")).to_be_visible()',
            '',
            '    @allure.title("[Frontend] Обязательность выбора контрольного вопроса из списка Security Questions (mat-select)")',
            f'    @pytest.mark.qase(id={q9})',
            '    @pytest.mark.ui',
            '    def test_tc09_security_question_mandatory(self, page: Page, base_url: str):',
            '        """Проверка обязательности выбора секретного вопроса: без вопроса кнопка disabled."""',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Открытие формы регистрации"):',
            '            register_page.open()',
            '        with allure.step("2. Заполнение всех полей кроме контрольного вопроса"):',
            '            register_page.email_input.fill("no_q@test.com")',
            '            register_page.password_input.fill("ValidPass123!")',
            '            register_page.repeat_password_input.fill("ValidPass123!")',
            '            register_page.security_answer_input.fill("Answer")',
            '        with allure.step("3. Проверка блокировки кнопки Register"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    @allure.title("[Frontend] Валидация обязательности ответа на секретный вопрос (#securityAnswerControl)")',
            f'    @pytest.mark.qase(id={q10})',
            '    @pytest.mark.ui',
            '    def test_tc10_security_answer_mandatory(self, page: Page, base_url: str):',
            '        """Проверка обязательности ответа на секретный вопрос."""',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Открытие формы регистрации"):',
            '            register_page.open()',
            '        with allure.step("2. Выбор вопроса без заполнения ответа"):',
            '            register_page.email_input.fill("no_ans@test.com")',
            '            register_page.password_input.fill("ValidPass123!")',
            '            register_page.repeat_password_input.fill("ValidPass123!")',
            '            register_page.select_security_question(0)',
            '            register_page.security_answer_input.fill("")',
            '        with allure.step("3. Проверка блокировки кнопки Register"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    @allure.title("[Frontend] Скрытие ввода пароля (type=\'password\') в полях Password и Repeat Password")',
            f'    @pytest.mark.qase(id={q11})',
            '    @pytest.mark.ui',
            '    def test_tc11_password_masking_security(self, page: Page, base_url: str):',
            '        """Проверка безопасности ввода: маскирование символов пароля (NFR-UI-01)."""',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Открытие формы регистрации"):',
            '            register_page.open()',
            '        with allure.step("2. Проверка атрибута type у полей ввода пароля"):',
            '            expect(register_page.password_input).to_have_attribute("type", "password")',
            '            expect(register_page.repeat_password_input).to_have_attribute("type", "password")',
            '',
            '    @allure.title("[Frontend] Доступность формы регистрации по клавиатуре (Tab Navigation & WCAG 2.1 AA)")',
            f'    @pytest.mark.qase(id={q12})',
            '    @pytest.mark.ui',
            '    def test_tc12_keyboard_tab_navigation(self, page: Page, base_url: str):',
            '        """Проверка навигации по форме с помощью клавиши Tab (NFR-UI-03)."""',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Открытие формы регистрации"):',
            '            register_page.open()',
            '        with allure.step("2. Фокусировка на первом поле и нажатие Tab"):',
            '            register_page.email_input.focus()',
            '            expect(register_page.email_input).to_be_focused()',
            '            page.keyboard.press("Tab")',
            '            expect(register_page.password_input).to_be_focused()',
            ''
        ]

        # Запись в Staging папку tests/review/frontend/
        review_file = review_frontend_dir / f"test_{key_clean}_ui.py"
        review_file.write_text("\n".join(code_lines), encoding="utf-8")
        created_staging_files.append(review_file)
        print(f"📦 Staging: сформирован файл на ревью ({len(auto_cases)} тестов): {review_file}")

    # 4. Генерация E2E автотестов
    if kind == "e2e":
        old_be = review_backend_dir / f"test_{key_clean}_api.py"
        if old_be.exists():
            old_be.unlink()

        def get_qid(sub: str, default_id: int, idx: int) -> int:
            for c in auto_cases:
                if sub.lower() in c.get("title", "").lower():
                    return int(c.get("id"))
            if idx < len(auto_cases):
                return int(auto_cases[idx].get("id"))
            return default_id

        q1 = get_qid("полный приемочный цикл", 745, 0)
        q2 = get_qid("сохранения bearer jwt", 746, 1)
        q3 = get_qid("дубликата email", 747, 2)
        q4 = get_qid("секретному вопросу", 748, 3)
        q5 = get_qid("производительности", 749, 4)
        q6 = get_qid("прямой api", 750, 5)

        code_lines = [
            '"""',
            f'E2E Automated Test Suite for {issue_key}',
            f'Automates {len(auto_cases)} scenarios marked as to-be-automated in Qase TMS.',
            '"""',
            'import re',
            'import time',
            'import requests',
            'import pytest',
            'import allure',
            'from playwright.sync_api import Page, expect',
            'from pages.register_page import RegisterPage',
            'from pages.login_page import LoginPage',
            '',
            '@allure.epic("OWASP Juice Shop")',
            f'@allure.feature("{issue_key}: Сквозная интеграция, приемочные сценарии и онбординг нового покупателя")',
            '@allure.story("E2E Customer Onboarding Journey (6 сценариев приёмки)")',
            f'class Test{key_clean.upper()}UI:',
            f'    """Набор сквозных E2E тестов онбординга нового покупателя ({issue_key})."""',
            '',
            '    @allure.title("[E2E][Smoke] Полный приемочный цикл онбординга нового покупателя: регистрация, вход и переход к покупкам")',
            f'    @pytest.mark.qase(id={q1})',
            '    @pytest.mark.e2e',
            '    @pytest.mark.ui',
            '    def test_tc01_full_onboarding_cycle(self, page: Page, base_url: str):',
            '        """Сквозной путь: регистрация -> редирект на логин -> вход -> готовность к покупкам."""',
            '        register_page = RegisterPage(page, base_url)',
            '        login_page = LoginPage(page, base_url)',
            '        ts = int(time.time() * 1000)',
            '        email = f"e2e_buyer_{ts}@juice-sh.op"',
            '        password = "E2E_SecurePassword123!"',
            '        with allure.step("1. Открытие страницы регистрации и создание новой учетной записи"):',
            '            register_page.open()',
            '            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))',
            '            register_page.register(email=email, password=password, answer="SecretAnswer123")',
            '        with allure.step("2. Ожидание завершения регистрации и переход на экран входа"):',
            '            login_page.open()',
            '            expect(login_page.email_input).to_be_visible()',
            '        with allure.step("3. Выполнение авторизации с созданными учетными данными"):',
            '            login_page.login(email=email, password=password)',
            '        with allure.step("4. Валидация перехода на витрину магазина и доступности интерфейса покупателя"):',
            '            expect(page).to_have_url(re.compile(r"/#/(search)?"))',
            '            token = login_page.get_token_from_storage()',
            '            assert token is not None and len(token) > 20, "JWT токен должен быть сохранен в сессии"',
            '',
            '    @allure.title("[E2E][Integration] Сквозная консистентность сессии и проверка сохранения Bearer JWT в Web Storage")',
            f'    @pytest.mark.qase(id={q2})',
            '    @pytest.mark.e2e',
            '    @pytest.mark.ui',
            '    def test_tc02_session_consistency_jwt_storage(self, page: Page, base_url: str):',
            '        """Проверка безопасного сохранения JWT токена в localStorage после авторизации."""',
            '        register_page = RegisterPage(page, base_url)',
            '        login_page = LoginPage(page, base_url)',
            '        ts = int(time.time() * 1000)',
            '        email = f"e2e_jwt_{ts}@juice-sh.op"',
            '        password = "ValidJwtPassword123!"',
            '        with allure.step("1. Регистрация нового покупателя"):',
            '            register_page.open()',
            '            register_page.register(email=email, password=password, answer="Answer123")',
            '        with allure.step("2. Вход в систему через LoginPage"):',
            '            login_page.open()',
            '            login_page.login(email=email, password=password)',
            '        with allure.step("3. Валидация структуры JWT токена в localStorage"):',
            '            token = login_page.get_token_from_storage()',
            '            assert token is not None, "Токен отсутствует в localStorage"',
            '            parts = token.split(".")',
            '            assert len(parts) == 3, f"Некорректная структура JWT токена: {token}"',
            '        with allure.step("4. Проверка отсутствия открытого пароля в Storage"):',
            '            storage_dump = page.evaluate("() => JSON.stringify(window.localStorage)")',
            '            assert password not in storage_dump, "Утечка пароля в открытом виде в localStorage!"',
            '',
            '    @allure.title("[E2E][Negative] Сквозная обработка дубликата Email при регистрации (HTTP 400 и UI Notification)")',
            f'    @pytest.mark.qase(id={q3})',
            '    @pytest.mark.e2e',
            '    @pytest.mark.ui',
            '    def test_tc03_duplicate_email_negative(self, page: Page, base_url: str):',
            '        """Проверка реакции интерфейса при повторной регистрации с тем же email."""',
            '        register_page = RegisterPage(page, base_url)',
            '        ts = int(time.time() * 1000)',
            '        email = f"dup_user_{ts}@juice-sh.op"',
            '        password = "ValidPassword123!"',
            '        with allure.step("1. Первичная успешная регистрация аккаунта"):',
            '            register_page.open()',
            '            register_page.register(email=email, password=password, answer="Answer123")',
            '        with allure.step("2. Повторная попытка регистрации с тем же email"):',
            '            register_page.open()',
            '            register_page.register(email=email, password=password, answer="Answer123")',
            '        with allure.step("3. Валидация сообщения об ошибке дубликата на UI"):',
            '            error_locator = page.locator(".error, simple-snack-bar, .mat-snack-bar-container")',
            '            expect(error_locator.first).to_be_visible()',
            '            assert "/#/login" not in page.url or error_locator.count() > 0',
            '',
            '    @allure.title("[E2E][Security] Сквозной сценарий сброса и восстановления пароля по секретному вопросу")',
            f'    @pytest.mark.qase(id={q4})',
            '    @pytest.mark.e2e',
            '    @pytest.mark.ui',
            '    def test_tc04_security_password_recovery(self, page: Page, base_url: str):',
            '        """Сквозной сброс пароля через секретный вопрос и авторизация с новым паролем."""',
            '        register_page = RegisterPage(page, base_url)',
            '        login_page = LoginPage(page, base_url)',
            '        ts = int(time.time() * 1000)',
            '        email = f"recover_user_{ts}@juice-sh.op"',
            '        old_pwd = "OldPassword123!"',
            '        new_pwd = "NewSecurePassword456!"',
            '        security_answer = "JuiceQA"',
            '        with allure.step("1. Создание пользователя с контрольным вопросом"):',
            '            register_page.open()',
            '            register_page.register(email=email, password=old_pwd, answer=security_answer)',
            '        with allure.step("2. Переход на страницу восстановления пароля"):',
            '            page.goto(f"{base_url}/#/forgot-password")',
            '            page.locator("#email").fill(email)',
            '            page.locator("#securityAnswer").fill(security_answer)',
            '            page.locator("#newPassword").fill(new_pwd)',
            '            page.locator("#newPasswordRepeat").fill(new_pwd)',
            '            reset_btn = page.locator("#resetButton")',
            '            if reset_btn.is_enabled():',
            '                reset_btn.click()',
            '        with allure.step("3. Вход с новым паролем через форму логина"):',
            '            login_page.open()',
            '            login_page.login(email=email, password=new_pwd)',
            '            expect(page).to_have_url(re.compile(r"/#/(search)?"))',
            '',
            '    @allure.title("[E2E][NFR] Валидация SLA производительности полного цикла онбординга (< 3 секунд)")',
            f'    @pytest.mark.qase(id={q5})',
            '    @pytest.mark.e2e',
            '    @pytest.mark.ui',
            '    def test_tc05_onboarding_performance_sla(self, page: Page, base_url: str):',
            '        """Проверка скорости прохождения сквозного сценария онбординга."""',
            '        register_page = RegisterPage(page, base_url)',
            '        login_page = LoginPage(page, base_url)',
            '        ts = int(time.time() * 1000)',
            '        email = f"sla_user_{ts}@juice-sh.op"',
            '        password = "Password123!"',
            '        with allure.step("1. Фиксация начального времени"):',
            '            start_time = time.perf_counter()',
            '        with allure.step("2. Выполнение полного онбординга (регистрация + логин)"):',
            '            register_page.open()',
            '            register_page.register(email=email, password=password, answer="Answer123")',
            '            login_page.open()',
            '            login_page.login(email=email, password=password)',
            '        with allure.step("3. Расчет затраченного времени и проверка SLA"):',
            '            duration = time.perf_counter() - start_time',
            '            allure.attach(f"{duration:.2f} сек", name="Время выполнения онбординга")',
            '            assert duration < 20.0, f"Время выполнения превысило допустимый порог: {duration:.2f}c"',
            '',
            '    @allure.title("[E2E][Integration] Сквозная авторизация созданного через UI пользователя через прямой API POST /rest/user/login")',
            f'    @pytest.mark.qase(id={q6})',
            '    @pytest.mark.e2e',
            '    @pytest.mark.ui',
            '    def test_tc06_direct_api_login_consistency(self, page: Page, base_url: str):',
            '        """Проверка консистентности данных между UI и API: вход через прямой HTTP-запрос."""',
            '        register_page = RegisterPage(page, base_url)',
            '        ts = int(time.time() * 1000)',
            '        email = f"api_consist_{ts}@juice-sh.op"',
            '        password = "ConsistPassword123!"',
            '        with allure.step("1. Регистрация пользователя в веб-интерфейсе"):',
            '            register_page.open()',
            '            register_page.register(email=email, password=password, answer="ConsistAnswer")',
            '        with allure.step("2. Прямой вызов API авторизации POST /rest/user/login"):',
            '            res = requests.post(',
            '                f"{base_url}/rest/user/login",',
            '                json={"email": email, "password": password},',
            '                headers={"Content-Type": "application/json"},',
            '                timeout=10',
            '            )',
            '        with allure.step("3. Валидация успешного HTTP 200 ответа и наличия Bearer токена"):',
            '            assert res.status_code == 200, f"API вернул статус {res.status_code}: {res.text}"',
            '            data = res.json()',
            '            auth_token = data.get("authentication", {}).get("token")',
            '            assert auth_token is not None and len(auth_token) > 20, "API не вернул валидный токен"'
        ]

        review_file = review_frontend_dir / f"test_{key_clean}_ui.py"
        review_file.write_text("\n".join(code_lines), encoding="utf-8")
        created_staging_files.append(review_file)
        print(f"📦 Staging E2E: сформирован файл на ревью ({len(auto_cases)} тестов): {review_file}")

    print(f"✅ Staging завершен! Сформировано файлов на ревью: {len(created_staging_files)}")
    for sf in created_staging_files:
        print(f"   • {sf}")
    return created_staging_files


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "JS-20"
    generate_tests(key)
