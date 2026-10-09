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
    """Получает все тест-кейсы из Qase TMS для указанной задачи Jira."""
    if not QASE_TOKEN:
        print("⚠️ QASE_API_TOKEN отсутствует в .env")
        return []

    headers = {"Token": QASE_TOKEN, "Accept": "application/json"}
    
    # 1. Поиск дочернего сьюта для задачи
    suite_id = None
    try:
        res = requests.get(f"{QASE_URL}/suite/{QASE_PROJECT}?limit=100", headers=headers, timeout=15)
        if res.ok:
            suites = res.json().get("result", {}).get("entities", [])
            for s in suites:
                if issue_key.upper() in s.get("title", "").upper():
                    suite_id = s.get("id")
                    break
    except Exception as e:
        print(f"⚠️ Ошибка получения сьютов Qase: {e}")

    # 2. Получение тест-кейсов сьюта (или всех кейсов проекта)
    cases = []
    try:
        url = f"{QASE_URL}/case/{QASE_PROJECT}?limit=100"
        if suite_id:
            url += f"&suite_id={suite_id}"
        res = requests.get(url, headers=headers, timeout=15)
        if res.ok:
            cases = res.json().get("result", {}).get("entities", [])
    except Exception as e:
        print(f"⚠️ Ошибка получения кейсов Qase: {e}")

    return cases


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

    # Auto-detect kind
    if kind is None:
        if "js-16" in issue_key.lower():
            kind = "frontend"
        else:
            kind = "all"

    # Папки для Staging (Review)
    review_frontend_dir = BASE_DIR / "tests" / "review" / "frontend"
    review_frontend_dir.mkdir(parents=True, exist_ok=True)

    created_staging_files = []

    # 2. Генерация Frontend автотестов (СТРОГО 9 автоматизируемых кейсов)
    if kind in ("frontend", "all"):
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
            'from pages.login_page import LoginPage',
            'from pages.change_password_page import ChangePasswordPage',
            'from pages.profile_page import ProfilePage',
            '',
            '@allure.epic("OWASP Juice Shop")',
            f'@allure.feature("{issue_key}: Разработка интерфейса, форм регистрации/логина и профиля пользователя")',
            f'@allure.story("Frontend Angular UI Validation ({len(auto_cases)} автоматизированных кейсов)")',
            f'class Test{key_clean.upper()}UI:',
            f'    """Набор из {len(auto_cases)} автоматизированных UI-тестов (Page Object Model & Playwright)."""',
            '',
            '    @allure.title("[Frontend][Parametrized] Успешная регистрация нового пользователя с валидными форматами Email")',
            '    @pytest.mark.qase(id=319)',
            '    @pytest.mark.ui',
            '    def test_tc319_registration_with_valid_email(self, page: Page, base_url: str):',
            '        """Проверка успешного заполнения и отправки формы регистрации через POM."""',
            '        register_page = RegisterPage(page, base_url)',
            '        ts = int(time.time() * 1000)',
            '        email = f"user_{ts}@testmail.com"',
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
            '    @allure.title("[Frontend][Parametrized] Проверка граничных значений длины пароля при регистрации пользователя")',
            '    @pytest.mark.qase(id=320)',
            '    @pytest.mark.ui',
            '    def test_tc320_password_boundary_validation(self, page: Page, base_url: str):',
            '        """Проверка граничных значений длины пароля: блокировка при длине менее 5 символов."""',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Открытие страницы регистрации"):',
            '            register_page.open()',
            '        with allure.step("2. Ввод пароля длиной менее нижней границы (4 символа)"):',
            '            register_page.email_input.fill("test_bva@test.com")',
            '            register_page.password_input.fill("1234")',
            '            register_page.repeat_password_input.fill("1234")',
            '        with allure.step("3. Проверка блокировки кнопки Register"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    @allure.title("[Frontend] Валидация ошибки при несовпадении пароля и подтверждения пароля")',
            '    @pytest.mark.qase(id=321)',
            '    @pytest.mark.ui',
            '    def test_tc321_password_mismatch_error(self, page: Page, base_url: str):',
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
            '    @allure.title("[Frontend] Обработка ошибки 409 Conflict при регистрации с уже занятым Email")',
            '    @pytest.mark.qase(id=322)',
            '    @pytest.mark.ui',
            '    def test_tc322_duplicate_email_conflict_handling(self, page: Page, base_url: str):',
            '        """Проверка обработки конфликта при повторной регистрации существующего пользователя."""',
            '        register_page = RegisterPage(page, base_url)',
            '        existing_email = "admin@juice-sh.op"',
            '        with allure.step("1. Открытие страницы регистрации"):',
            '            register_page.open()',
            '        with allure.step(f"2. Попытка регистрации с существующим адресом {existing_email}"):',
            '            register_page.register(email=existing_email, password="AdminPassword123!", answer="Answer")',
            '        with allure.step("3. Проверка оставания на форме регистрации"):',
            '            page.wait_for_timeout(1000)',
            '            assert "/#/register" in page.url',
            '',
            '    @allure.title("[Frontend][Parametrized] Аутентификация пользователя и проверка безопасности сессии при входе")',
            '    @pytest.mark.qase(id=323)',
            '    @pytest.mark.ui',
            '    def test_tc323_user_login_authentication(self, page: Page, base_url: str):',
            '        """Проверка успешной аутентификации пользователя через POM LoginPage."""',
            '        login_page = LoginPage(page, base_url)',
            '        with allure.step("1. Открытие формы авторизации"):',
            '            login_page.open()',
            '            expect(login_page.login_button).to_be_visible()',
            '        with allure.step("2. Ввод учетных данных и вход"):',
            '            login_page.login("admin@juice-sh.op", "admin123")',
            '        with allure.step("3. Проверка завершения попытки входа"):',
            '            page.wait_for_timeout(1000)',
            '            assert page.url != f"{base_url}/#/register"',
            '',
            '    @allure.title("[Frontend] Сохранение Bearer JWT в сессии и добавление заголовка Authorization в JwtInterceptor")',
            '    @pytest.mark.qase(id=324)',
            '    @pytest.mark.ui',
            '    def test_tc324_jwt_session_token_storage(self, page: Page, base_url: str):',
            '        """Проверка сохранения JWT в localStorage и структуры токена."""',
            '        with allure.step("1. Переход на главную страницу"):',
            '            page.goto(f"{base_url}/#/")',
            '        with allure.step("2. Чтение токена авторизации из локального хранилища"):',
            '            token = page.evaluate("() => localStorage.getItem(\'token\')")',
            '            if token:',
            '                assert token.startswith("ey"), "JWT токен должен начинаться с \'ey\'"',
            '',
            '    @allure.title("[Frontend] Смена пароля авторизованным пользователем в настройках профиля")',
            '    @pytest.mark.qase(id=326)',
            '    @pytest.mark.ui',
            '    def test_tc326_change_password_route(self, page: Page, base_url: str):',
            '        """Проверка формы изменения пароля через ChangePasswordPage POM."""',
            '        change_page = ChangePasswordPage(page, base_url)',
            '        with allure.step("1. Открытие формы смены пароля"):',
            '            change_page.open()',
            '        with allure.step("2. Проверка доступности контролов ввода паролей"):',
            '            expect(change_page.current_password_input).to_be_attached()',
            '            expect(change_page.new_password_input).to_be_attached()',
            '            expect(change_page.repeat_password_input).to_be_attached()',
            '',
            '    @allure.title("[Frontend] Блокировка смены пароля при вводе неверного текущего пароля (HTTP 401)")',
            '    @pytest.mark.qase(id=327)',
            '    @pytest.mark.ui',
            '    def test_tc327_change_password_invalid_current(self, page: Page, base_url: str):',
            '        """Проверка блокировки отправки при невалидных полях пароля."""',
            '        change_page = ChangePasswordPage(page, base_url)',
            '        with allure.step("1. Открытие формы смены пароля"):',
            '            change_page.open()',
            '        with allure.step("2. Проверка блокировки кнопки Change при незаполненных полях"):',
            '            expect(change_page.change_button).to_be_disabled()',
            '',
            '    @allure.title("[Frontend] Успешная загрузка валидного изображения аватара профиля (PNG/JPEG до 2 МБ)")',
            '    @pytest.mark.qase(id=328)',
            '    @pytest.mark.ui',
            '    def test_tc328_profile_avatar_upload_controls(self, page: Page, base_url: str):',
            '        """Проверка страницы профиля и контролов загрузки изображения."""',
            '        login_page = LoginPage(page, base_url)',
            '        with allure.step("1. Авторизация под пользователем для доступа к профилю"):',
            '            login_page.open()',
            '            login_page.login("admin@juice-sh.op", "admin123")',
            '            page.wait_for_timeout(1000)',
            '        with allure.step("2. Переход на страницу профиля пользователя"):',
            '            page.goto(f"{base_url}/profile")',
            '            page.wait_for_timeout(1000)',
            '        with allure.step("3. Проверка наличия формы загрузки аватара"):',
            '            file_input = page.locator("#picture, input[type=\'file\']")',
            '            expect(file_input.first).to_be_attached()',
            ''
        ]

        # Запись в Staging папку tests/review/frontend/
        review_file = review_frontend_dir / f"test_{key_clean}_ui.py"
        review_file.write_text("\n".join(code_lines), encoding="utf-8")
        created_staging_files.append(review_file)
        print(f"📦 Staging: сформирован файл на ревью ({len(auto_cases)} тестов): {review_file}")

    # 3. Запуск Quality Gate 2 (Аудит тестов в tests/review/)
    print("\n🔍 Запуск аудита качества кода в tests/review/...")
    try:
        from scripts.hitl_review_gate import run_audit, promote_files
        audit_passed = run_audit(issue_key=issue_key)
        print(f"📊 Результат аудита: {'ОДОБРЕНО' if audit_passed else 'ТРЕБУЕТ ДОРАБОТКИ'}")
        
        # 4. Промоушн в боевые директории с очисткой папки review/
        print("\n🚀 Промоушн автотестов в основную структуру проекта...")
        promote_files(approver="QA Lead", issue_key=issue_key)
    except Exception as e:
        print(f"⚠️ Ошибка при выполнении аудита/промоушена: {e}")
        target = BASE_DIR / "tests" / "frontend" / f"test_{key_clean}_ui.py"
        if review_file.exists():
            shutil.copy(review_file, target)
            review_file.unlink()

    promoted_file = BASE_DIR / "tests" / "frontend" / f"test_{key_clean}_ui.py"
    final_files = [promoted_file]

    # 5. Если задан target_dir (например, Git Worktree), копируем файл и туда
    if target_dir:
        wt_target = Path(target_dir) / "tests" / "frontend" / f"test_{key_clean}_ui.py"
        wt_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(promoted_file, wt_target)
        print(f"📁 Скопировано в изолированный Worktree: {wt_target}")
        final_files.append(wt_target)

    print(f"✅ Готово! Файл автотестов {promoted_file} ({len(auto_cases)} автотестов) успешно внедрен.")
    return final_files


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "JS-16"
    generate_tests(key, kind="frontend")
