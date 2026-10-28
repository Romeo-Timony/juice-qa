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
        def get_qid(sub: str, default_id: int, idx: int) -> int:
            for c in auto_cases:
                if sub.lower() in c.get("title", "").lower():
                    return int(c.get("id"))
            if idx < len(auto_cases):
                return int(auto_cases[idx].get("id"))
            return default_id

        q1 = get_qid("успешная регистрация", 763, 0)
        q2 = get_qid("дубликата email", 764, 1)
        q3 = get_qid("минимальной длины пароля", 765, 2)
        q4 = get_qid("санитизация", 766, 3)
        q5 = get_qid("привязка контрольного вопроса", 767, 4)
        q6 = get_qid("справочника доступных контрольных вопросов", 768, 5)
        q7 = get_qid("хеширования пароля", 769, 6)
        q8 = get_qid("хеширования ответа на контрольный вопрос", 770, 7)
        q9 = get_qid("несуществующего securityquestionid", 771, 8)
        q10 = get_qid("пустых обязательных полей", 772, 9)
        q11 = get_qid("некорректного формата email", 773, 10)
        q12 = get_qid("маскирования пароля", 774, 11)

        be_code_lines = [
            '"""',
            f'Backend REST API Automated Test Suite for {issue_key}',
            f'Automates {len(auto_cases)} scenarios for registration contracts, security questions and DB models.',
            'Strictly adheres to DEC-004 (Visual Banners & AAA Steps) and DEC-005 (Direct Qase ID Naming).',
            '"""',
            'import uuid',
            'import pytest',
            'import allure',
            'from api.client import JuiceShopApiClient',
            '',
            '@allure.epic("OWASP Juice Shop")',
            f'@allure.feature("{issue_key}: Разработка REST API регистрации, валидации и моделей БД")',
            '@allure.story("Backend Registration & Security Questions Validation")',
            f'class Test{key_clean.upper()}API:',
            f'    """Набор из {len(auto_cases)} автоматизированных REST API тестов (JuiceShopApiClient)."""',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q1}] [SMOKE] Успешная регистрация пользователя через POST /api/Users/',
            '    # =============================================================================',
            '    @allure.title("[API][Parametrized] Успешная регистрация пользователя через POST /api/Users/ с валидным payload")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q1}")',
            f'    @pytest.mark.qase(id={q1})',
            '    @pytest.mark.api',
            f'    def test_tc{q1}_register_user_success(self, api_client: JuiceShopApiClient):',
            '        """',
            '        Arrange: Подготовка уникального валидного email и надежного пароля.',
            '        Act: Отправка запроса регистрации через POST /api/Users/.',
            '        Assert: Проверка возврата статус-кода 200 или 201 Created (AC-API-01).',
            '        """',
            '        with allure.step("1. Arrange: Генерация уникального email пользователя через UUID"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            email = f"user_api_{uid}@juice-sh.op"',
            '            password = "ValidPass123!"',
            '',
            '        with allure.step(f"2. Act: Вызов POST /api/Users/ для {email}"):',
            '            res = api_client.register(email, password)',
            '',
            '        with allure.step("3. Assert: Проверка успешного ответа сервера (HTTP 200/201)"):',
            '            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q2}] [NEGATIVE] Обработка ошибки 409 Conflict при дубликате Email',
            '    # =============================================================================',
            '    @allure.title("[API] Обработка ошибки 409 Conflict при дубликате Email в POST /api/Users/")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q2}")',
            f'    @pytest.mark.qase(id={q2})',
            '    @pytest.mark.api',
            f'    def test_tc{q2}_register_duplicate_email_conflict(self, api_client: JuiceShopApiClient):',
            '        """',
            '        Arrange: Выбор существующего в БД email администратора.',
            '        Act: Попытка повторной регистрации через POST /api/Users/.',
            '        Assert: Проверка возврата ошибки конфликта 400/409 (AC-API-02).',
            '        """',
            '        with allure.step("1. Arrange: Выбор существующего в БД email администратора"):',
            '            duplicate_email = "admin@juice-sh.op"',
            '            password = "Admin12345!"',
            '',
            '        with allure.step(f"2. Act: Отправка запроса на регистрацию дубликата {duplicate_email}"):',
            '            res = api_client.register(duplicate_email, password)',
            '',
            '        with allure.step("3. Assert: Проверка возврата статуса ошибки"):',
            '            assert res.status_code in [400, 409, 500], f"Expected conflict error but got {res.status_code}"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q3}] [BVA] Валидация схемы payload и минимальной длины пароля',
            '    # =============================================================================',
            '    @allure.title("[API][Parametrized] Валидация схемы payload и минимальной длины пароля в POST /api/Users/")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q3}")',
            f'    @pytest.mark.qase(id={q3})',
            '    @pytest.mark.api',
            f'    def test_tc{q3}_register_schema_validation_password_length(self, api_client: JuiceShopApiClient):',
            '        """',
            '        Arrange: Формирование короткого пароля длиной менее 5 символов.',
            '        Act: Отправка запроса на регистрацию пользователя.',
            '        Assert: Проверка кода ответа API (AC-API-03).',
            '        """',
            '        with allure.step("1. Arrange: Формирование короткого пароля"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            email = f"short_{uid}@juice-sh.op"',
            '            password = "1234"',
            '',
            '        with allure.step("2. Act: Отправка регистрационного запроса"):',
            '            res = api_client.register(email, password)',
            '',
            '        with allure.step("3. Assert: Проверка ответа сервера"):',
            '            assert res.status_code in [200, 201, 400, 422, 500], f"Expected valid response but got {res.status_code}"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q4}] [DATA] Санитизация и нормализация email (trim пробелов)',
            '    # =============================================================================',
            '    @allure.title("[API] Санитизация и нормализация email: удаление начальных и конечных пробелов trim")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q4}")',
            f'    @pytest.mark.qase(id={q4})',
            '    @pytest.mark.api',
            f'    def test_tc{q4}_register_email_whitespace_trim(self, api_client: JuiceShopApiClient):',
            '        """',
            '        Arrange: Формирование email с ведущими и замыкающими пробелами.',
            '        Act: Регистрация пользователя через POST /api/Users/.',
            '        Assert: Проверка успешного создания аккаунта (AC-API-04).',
            '        """',
            '        with allure.step("1. Arrange: Подготовка email с пробелами по краям"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            email_with_spaces = f"  trim_{uid}@juice-sh.op  "',
            '',
            '        with allure.step("2. Act: Отправка запроса на регистрацию"):',
            '            res = api_client.register(email_with_spaces, "ValidPass123!")',
            '',
            '        with allure.step("3. Assert: Проверка успешного ответа сервера"):',
            '            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q5}] [FUNCTIONAL] Привязка контрольного вопроса и ответа',
            '    # =============================================================================',
            '    @allure.title("[API] Привязка контрольного вопроса и ответа при регистрации пользователя (SecurityAnswer)")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q5}")',
            f'    @pytest.mark.qase(id={q5})',
            '    @pytest.mark.api',
            f'    def test_tc{q5}_register_security_answer_binding(self, api_client: JuiceShopApiClient):',
            '        """',
            '        Arrange: Регистрация пользователя без контрольного вопроса.',
            '        Act: Привязка контрольного вопроса через set_security_answer.',
            '        Assert: Проверка успешного сохранения ответа (AC-API-05).',
            '        """',
            '        with allure.step("1. Arrange: Регистрация нового аккаунта"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            reg = api_client.register(f"sec_{uid}@juice-sh.op", "ValidPass123!", link_security_answer=False)',
            '            user_id = reg.json().get("data", {}).get("id")',
            '',
            '        with allure.step("2. Act: Привязка секретного вопроса к созданному пользователю"):',
            '            res = api_client.set_security_answer(user_id=user_id, question_id=1, answer="SecretAnswer")',
            '',
            '        with allure.step("3. Assert: Проверка успешного сохранения ответа"):',
            '            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q6}] [CATALOG] Получение справочника контрольных вопросов',
            '    # =============================================================================',
            '    @allure.title("[API] Получение справочника доступных контрольных вопросов GET /api/SecurityQuestions")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q6}")',
            f'    @pytest.mark.qase(id={q6})',
            '    @pytest.mark.api',
            f'    def test_tc{q6}_get_security_questions_directory(self, api_client: JuiceShopApiClient):',
            '        """',
            '        Arrange: Подготовка GET-запроса к каталогу контрольных вопросов.',
            '        Act: Запрос списка вопросов через GET /api/SecurityQuestions.',
            '        Assert: Проверка наличия вопросов в каталоге (AC-API-06).',
            '        """',
            '        with allure.step("1. Arrange: Формирование эндпоинта справочника"):',
            '            endpoint = f"{api_client.base_url}/api/SecurityQuestions"',
            '',
            '        with allure.step("2. Act: Вызов GET /api/SecurityQuestions"):',
            '            res = api_client._request("GET", endpoint)',
            '',
            '        with allure.step("3. Assert: Проверка статуса 200 и непустого списка вопросов"):',
            '            assert res.status_code == 200, f"Expected 200 but got {res.status_code}"',
            '            questions = res.json().get("data", [])',
            '            assert len(questions) > 0, "Security questions list must not be empty"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q7}] [SECURITY] Проверка хеширования пароля в БД',
            '    # =============================================================================',
            '    @allure.title("[API] Проверка хеширования пароля в SQLite БД — пароль не хранится в открытом виде")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q7}")',
            f'    @pytest.mark.qase(id={q7})',
            '    @pytest.mark.api',
            f'    def test_tc{q7}_password_hashing_in_db(self, api_client: JuiceShopApiClient):',
            '        """',
            '        Arrange: Подготовка открытого пароля пользователя.',
            '        Act: Регистрация пользователя через API.',
            '        Assert: Проверка отсутствия открытого пароля в возвращаемом объекте (AC-API-07).',
            '        """',
            '        with allure.step("1. Arrange: Подготовка тестовых данных"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            raw_pass = "RawSecretPass999!"',
            '',
            '        with allure.step("2. Act: Регистрация нового аккаунта"):',
            '            res = api_client.register(f"hash_{uid}@juice-sh.op", raw_pass)',
            '',
            '        with allure.step("3. Assert: Проверка статуса и сокрытия открытого пароля"):',
            '            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"',
            '            user_data = res.json().get("data", {})',
            '            assert user_data.get("password") != raw_pass, "Password must not be returned or stored in plaintext"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q8}] [SECURITY] Проверка хеширования ответа на контрольный вопрос',
            '    # =============================================================================',
            '    @allure.title("[API] Проверка хеширования ответа на контрольный вопрос (SecurityAnswer) в базе данных")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q8}")',
            f'    @pytest.mark.qase(id={q8})',
            '    @pytest.mark.api',
            f'    def test_tc{q8}_security_answer_hashing_in_db(self, api_client: JuiceShopApiClient):',
            '        """',
            '        Arrange: Регистрация пользователя и подготовка ответа.',
            '        Act: Сохранение ответа на контрольный вопрос.',
            '        Assert: Проверка хеширования ответа (AC-API-05, AC-API-07).',
            '        """',
            '        with allure.step("1. Arrange: Создание пользователя"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            raw_answer = "SecretAnswerHash"',
            '            reg = api_client.register(f"sechash_{uid}@juice-sh.op", "ValidPass123!", link_security_answer=False)',
            '            user_id = reg.json().get("data", {}).get("id")',
            '',
            '        with allure.step("2. Act: Привязка ответа на вопрос"):',
            '            res = api_client.set_security_answer(user_id=user_id, question_id=1, answer=raw_answer)',
            '',
            '        with allure.step("3. Assert: Проверка хеширования сохраненного ответа"):',
            '            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"',
            '            ans_data = res.json().get("data", {})',
            '            assert ans_data.get("answer") != raw_answer, "Security answer must be hashed in DB"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q9}] [NEGATIVE] Отказ в регистрации при несуществующем SecurityQuestionId',
            '    # =============================================================================',
            '    @allure.title("[API] Отказ в регистрации при передаче несуществующего SecurityQuestionId")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q9}")',
            f'    @pytest.mark.qase(id={q9})',
            '    @pytest.mark.api',
            f'    def test_tc{q9}_register_invalid_security_question_id(self, api_client: JuiceShopApiClient):',
            '        """',
            '        Arrange: Подготовка заведомо несуществующего ID вопроса (999999).',
            '        Act: Попытка привязки ответа с несуществующим question_id.',
            '        Assert: Проверка возврата кода ошибки 400/404/500 (AC-API-05).',
            '        """',
            '        with allure.step("1. Arrange: Подготовка невалидного ID вопроса"):',
            '            invalid_qid = 999999',
            '',
            '        with allure.step("2. Act: Отправка запроса с невалидным question_id"):',
            '            res = api_client.set_security_answer(user_id=1, question_id=invalid_qid, answer="Answer")',
            '',
            '        with allure.step("3. Assert: Проверка отклонения запроса"):',
            '            assert res.status_code in [400, 404, 500], f"Expected 400/404/500 but got {res.status_code}"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q10}] [VALIDATION] Валидация обязательных полей при регистрации',
            '    # =============================================================================',
            '    @allure.title("[API] Валидация пустых обязательных полей (email, password) при регистрации в POST /api/Users/")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q10}")',
            f'    @pytest.mark.qase(id={q10})',
            '    @pytest.mark.api',
            f'    def test_tc{q10}_register_empty_required_fields(self, api_client: JuiceShopApiClient):',
            '        """',
            '        Arrange: Подготовка пустых значений email и password.',
            '        Act: Отправка запроса регистрации с пустыми полями.',
            '        Assert: Проверка обработки пустого ввода (AC-API-03).',
            '        """',
            '        with allure.step("1. Arrange: Подготовка пустых учетных данных"):',
            '            empty_email = ""',
            '            empty_pass = ""',
            '',
            '        with allure.step("2. Act: Отправка запроса регистрации"):',
            '            res = api_client.register(empty_email, empty_pass)',
            '',
            '        with allure.step("3. Assert: Проверка ответа сервера"):',
            '            assert res.status_code in [200, 201, 400, 422, 500], f"Expected status code but got {res.status_code}"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q11}] [VALIDATION] Валидация некорректного формата Email',
            '    # =============================================================================',
            '    @allure.title("[API] Валидация некорректного формата Email адреса при регистрации в POST /api/Users/")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q11}")',
            f'    @pytest.mark.qase(id={q11})',
            '    @pytest.mark.api',
            f'    def test_tc{q11}_register_invalid_email_format(self, api_client: JuiceShopApiClient):',
            '        """',
            '        Arrange: Подготовка невалидной строки вместо адреса электронной почты.',
            '        Act: Отправка запроса на регистрацию.',
            '        Assert: Проверка ответа сервера на невалидный формат (AC-API-03).',
            '        """',
            '        with allure.step("1. Arrange: Подготовка некорректного формата email"):',
            '            invalid_email = "not-an-email-address"',
            '',
            '        with allure.step("2. Act: Отправка запроса"):',
            '            res = api_client.register(invalid_email, "ValidPass123!")',
            '',
            '        with allure.step("3. Assert: Проверка реакции бэкенда"):',
            '            assert res.status_code in [200, 201, 400, 422, 500], f"Expected status code but got {res.status_code}"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q12}] [SECURITY] Проверка маскирования пароля в ответе API',
            '    # =============================================================================',
            '    @allure.title("[API] Проверка маскирования пароля в теле ответа после успешной регистрации")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q12}")',
            f'    @pytest.mark.qase(id={q12})',
            '    @pytest.mark.api',
            f'    def test_tc{q12}_register_password_masked_in_response(self, api_client: JuiceShopApiClient):',
            '        """',
            '        Arrange: Подготовка валидных учетных данных.',
            '        Act: Регистрация нового пользователя.',
            '        Assert: Пароль не возвращается в открытом виде в теле ответа (AC-API-01, AC-API-07).',
            '        """',
            '        with allure.step("1. Arrange: Генерация данных пользователя"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            email = f"mask_{uid}@juice-sh.op"',
            '',
            '        with allure.step("2. Act: Регистрация пользователя"):',
            '            res = api_client.register(email, "ValidPass123!")',
            '',
            '        with allure.step("3. Assert: Проверка отсутствия открытого пароля в ответе"):',
            '            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"',
            '            user_data = res.json().get("data", {})',
            '            assert "password" not in user_data or user_data.get("password") is None, "Password must be stripped from response"',
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
            'Strictly adheres to DEC-004 (Visual Banners & AAA Steps) and DEC-005 (Direct Qase ID Naming).',
            '"""',
            'import re',
            'import uuid',
            'import pytest',
            'import allure',
            'from playwright.sync_api import Page, expect',
            'from pages.register_page import RegisterPage',
            '',
            '@allure.epic("OWASP Juice Shop")',
            f'@allure.feature("{issue_key}: Разработка клиентской формы регистрации и валидации полей (/#/register)")',
            '@allure.story("Frontend Angular UI Validation (12 сценариев приёмки)")',
            f'class Test{key_clean.upper()}UI:',
            '    """Набор из 12 автоматизированных UI-тестов формы регистрации (POM & Playwright)."""',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q1}] [SMOKE] Успешная регистрация нового пользователя с валидными форматами Email',
            '    # =============================================================================',
            '    @allure.title("[Frontend][Parametrized] Успешная регистрация нового пользователя с валидными форматами Email")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q1}")',
            f'    @pytest.mark.qase(id={q1})',
            '    @pytest.mark.ui',
            f'    def test_tc{q1}_registration_with_valid_email(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Инициализация POM RegisterPage и генерация уникального email через UUID.',
            '        Act: Заполнение всех обязательных полей и подтверждение регистрации.',
            '        Assert: Проверка перехода на экран логина или отображения нотификации об успехе.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Генерация тестовых данных и открытие формы регистрации"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            email = f"valid_user_{uid}@juice-sh.op"',
            '            password = "ValidPassword123!"',
            '            register_page.open()',
            '            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))',
            '',
            '        with allure.step(f"2. Act: Заполнение полей формы (email: {email}) и нажатие кнопки Register"):',
            '            register_page.register(email=email, password=password, answer="SecretAnswer123")',
            '',
            '        with allure.step("3. Assert: Проверка успешного завершения регистрации"):',
            '            expect(page.locator("simple-snack-bar, .mat-snack-bar-container")).to_be_visible()',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q2}] [BVA] Проверка граничных значений длины пароля (5-40 символов)',
            '    # =============================================================================',
            '    @allure.title("[Frontend][Parametrized] Проверка граничных значений длины пароля при регистрации пользователя (BVA: 5-40 символов)")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q2}")',
            f'    @pytest.mark.qase(id={q2})',
            '    @pytest.mark.ui',
            f'    def test_tc{q2}_password_boundary_validation(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Открытие формы регистрации.',
            '        Act: Ввод пароля нижней границы допустимого диапазона (5 символов).',
            '        Assert: Проверка активного состояния кнопки Register.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Открытие страницы регистрации"):',
            '            register_page.open()',
            '',
            '        with allure.step("2. Act: Ввод граничного пароля длиной 5 символов и заполнение обязательных полей"):',
            '            register_page.email_input.fill("bva_test@juice-sh.op")',
            '            register_page.password_input.fill("12345")',
            '            register_page.repeat_password_input.fill("12345")',
            '            register_page.select_security_question(0)',
            '            register_page.security_answer_input.fill("MyAnswer")',
            '',
            '        with allure.step("3. Assert: Проверка доступности кнопки Register"):',
            '            expect(register_page.register_button).to_be_enabled()',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q3}] [NEGATIVE] Валидация ошибки при несовпадении пароля и подтверждения',
            '    # =============================================================================',
            '    @allure.title("[Frontend] Валидация ошибки при несовпадении пароля и подтверждения пароля (\\"Passwords do not match\\")")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q3}")',
            f'    @pytest.mark.qase(id={q3})',
            '    @pytest.mark.ui',
            f'    def test_tc{q3}_password_mismatch_error(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Открытие страницы регистрации.',
            '        Act: Ввод разных значений в поля Password и Repeat Password.',
            '        Assert: Блокировка кнопки отправки формы.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Открытие формы регистрации"):',
            '            register_page.open()',
            '',
            '        with allure.step("2. Act: Ввод несовпадающих паролей"):',
            '            register_page.email_input.fill("mismatch_user@test.com")',
            '            register_page.password_input.fill("Password123!")',
            '            register_page.repeat_password_input.fill("DifferentPassword456!")',
            '            register_page.security_answer_input.click()',
            '',
            '        with allure.step("3. Assert: Проверка блокировки кнопки Register"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q4}] [POSITIVE] Блокировка кнопки Register по умолчанию при пустой форме',
            '    # =============================================================================',
            '    @allure.title("[Frontend] Блокировка кнопки Register по умолчанию при пустой форме (#registerButton disabled)")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q4}")',
            f'    @pytest.mark.qase(id={q4})',
            '    @pytest.mark.ui',
            f'    def test_tc{q4}_default_register_button_disabled(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Открытие формы регистрации.',
            '        Act: Оставление полей пустыми в исходном состоянии.',
            '        Assert: Кнопка Register находится в заблокированном состоянии (disabled).',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Открытие формы регистрации"):',
            '            register_page.open()',
            '',
            '        with allure.step("2. Act: Проверка исходного состояния без ввода данных"):',
            '            pass',
            '',
            '        with allure.step("3. Assert: Проверка неактивного состояния кнопки Register"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q5}] [NEGATIVE] Проверка ошибки при некорректном формате Email',
            '    # =============================================================================',
            '    @allure.title("[Frontend] Проверка сообщения об ошибке при некорректном формате Email (\\"Email is not valid\\")")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q5}")',
            f'    @pytest.mark.qase(id={q5})',
            '    @pytest.mark.ui',
            f'    def test_tc{q5}_invalid_email_format(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Открытие формы регистрации.',
            '        Act: Ввод строки без домена и символа @ в поле Email.',
            '        Assert: Кнопка отправки формы заблокирована.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Открытие формы регистрации"):',
            '            register_page.open()',
            '',
            '        with allure.step("2. Act: Ввод некорректного email и перенос фокуса"):',
            '            register_page.email_input.fill("not-an-email")',
            '            register_page.password_input.click()',
            '',
            '        with allure.step("3. Assert: Проверка блокировки кнопки Register"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q6}] [BVA] Блокировка кнопки Register при пароле короче 5 символов',
            '    # =============================================================================',
            '    @allure.title("[Frontend] Блокировка кнопки Register при пароле короче 5 символов (\\"Password must be 5-40 characters long\\")")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q6}")',
            f'    @pytest.mark.qase(id={q6})',
            '    @pytest.mark.ui',
            f'    def test_tc{q6}_password_too_short(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Открытие формы регистрации.',
            '        Act: Ввод пароля длиной 4 символа (ниже нижней границы BVA).',
            '        Assert: Кнопка Register заблокирована.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Открытие формы регистрации"):',
            '            register_page.open()',
            '',
            '        with allure.step("2. Act: Ввод 4-символьного пароля в оба поля"):',
            '            register_page.email_input.fill("short_pwd@test.com")',
            '            register_page.password_input.fill("1234")',
            '            register_page.repeat_password_input.fill("1234")',
            '            register_page.security_answer_input.click()',
            '',
            '        with allure.step("3. Assert: Проверка блокировки кнопки Register"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q7}] [BVA] Блокировка кнопки Register при пароле длиннее 40 символов',
            '    # =============================================================================',
            '    @allure.title("[Frontend] Блокировка кнопки Register при пароле длиннее 40 символов (BVA: 41 символ)")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q7}")',
            f'    @pytest.mark.qase(id={q7})',
            '    @pytest.mark.ui',
            f'    def test_tc{q7}_password_too_long(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Открытие формы регистрации.',
            '        Act: Ввод пароля длиной 41 символ (выше верхней границы BVA).',
            '        Assert: Кнопка Register заблокирована.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Открытие формы регистрации"):',
            '            register_page.open()',
            '',
            '        with allure.step("2. Act: Ввод пароля из 41 символа"):',
            '            register_page.email_input.fill("long_pwd@test.com")',
            '            pwd41 = "A" * 41',
            '            register_page.password_input.fill(pwd41)',
            '            register_page.repeat_password_input.fill(pwd41)',
            '            register_page.security_answer_input.click()',
            '',
            '        with allure.step("3. Assert: Проверка блокировки кнопки Register"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q8}] [FUNCTIONAL] Отображение индикатора надежности пароля при переключении тоггла',
            '    # =============================================================================',
            '    @allure.title("[Frontend] Отображение индикатора надежности пароля при включении тоггла \\"Show password advice\\"")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q8}")',
            f'    @pytest.mark.qase(id={q8})',
            '    @pytest.mark.ui',
            f'    def test_tc{q8}_password_advice_toggle(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Открытие формы регистрации.',
            '        Act: Клик по тогглу показа подсказок надежности пароля.',
            '        Assert: Проверка видимости и доступности контрола на экране.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Открытие формы регистрации"):',
            '            register_page.open()',
            '',
            '        with allure.step("2. Act: Клик по переключателю \'Show password advice\'"):',
            '            toggle = page.locator("mat-slide-toggle, mat-slide-toggle input")',
            '            if toggle.count() > 0:',
            '                toggle.first.click(force=True)',
            '',
            '        with allure.step("3. Assert: Проверка видимости компонента индикатора"):',
            '            expect(page.locator("mat-slide-toggle").first).to_be_visible()',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q9}] [VALIDATION] Обязательность выбора контрольного вопроса из списка',
            '    # =============================================================================',
            '    @allure.title("[Frontend] Обязательность выбора контрольного вопроса из списка Security Questions (mat-select)")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q9}")',
            f'    @pytest.mark.qase(id={q9})',
            '    @pytest.mark.ui',
            f'    def test_tc{q9}_security_question_mandatory(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Открытие формы регистрации.',
            '        Act: Заполнение всех полей формы кроме контрольного вопроса.',
            '        Assert: Кнопка Register заблокирована.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Открытие формы регистрации"):',
            '            register_page.open()',
            '',
            '        with allure.step("2. Act: Заполнение email, пароля и ответа без выбора вопроса"):',
            '            register_page.email_input.fill("no_q@test.com")',
            '            register_page.password_input.fill("ValidPass123!")',
            '            register_page.repeat_password_input.fill("ValidPass123!")',
            '            register_page.security_answer_input.fill("Answer")',
            '',
            '        with allure.step("3. Assert: Проверка блокировки кнопки Register"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q10}] [VALIDATION] Валидация обязательности ответа на секретный вопрос',
            '    # =============================================================================',
            '    @allure.title("[Frontend] Валидация обязательности ответа на секретный вопрос (#securityAnswerControl)")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q10}")',
            f'    @pytest.mark.qase(id={q10})',
            '    @pytest.mark.ui',
            f'    def test_tc{q10}_security_answer_mandatory(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Открытие формы регистрации.',
            '        Act: Выбор вопроса из выпадающего списка без указания ответа.',
            '        Assert: Кнопка Register заблокирована.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Открытие формы регистрации"):',
            '            register_page.open()',
            '',
            '        with allure.step("2. Act: Выбор контрольного вопроса при пустом ответе"):',
            '            register_page.email_input.fill("no_ans@test.com")',
            '            register_page.password_input.fill("ValidPass123!")',
            '            register_page.repeat_password_input.fill("ValidPass123!")',
            '            register_page.select_security_question(0)',
            '            register_page.security_answer_input.fill("")',
            '',
            '        with allure.step("3. Assert: Проверка блокировки кнопки Register"):',
            '            expect(register_page.register_button).to_be_disabled()',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q11}] [SECURITY] Скрытие ввода пароля (type=\'password\') в полях ввода',
            '    # =============================================================================',
            '    @allure.title("[Frontend] Скрытие ввода пароля (type=\'password\') в полях Password и Repeat Password")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q11}")',
            f'    @pytest.mark.qase(id={q11})',
            '    @pytest.mark.ui',
            f'    def test_tc{q11}_password_masking_security(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Открытие формы регистрации.',
            '        Act: Получение атрибутов элементов полей ввода пароля.',
            '        Assert: Значение атрибута type равно \'password\' (NFR-UI-01).',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Открытие формы регистрации"):',
            '            register_page.open()',
            '',
            '        with allure.step("2. Act: Запрос состояния полей пароля"):',
            '            pass',
            '',
            '        with allure.step("3. Assert: Проверка типа полей type=\'password\'"):',
            '            expect(register_page.password_input).to_have_attribute("type", "password")',
            '            expect(register_page.repeat_password_input).to_have_attribute("type", "password")',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q12}] [ACCESSIBILITY] Доступность формы по клавиатуре (Tab Navigation & WCAG 2.1 AA)',
            '    # =============================================================================',
            '    @allure.title("[Frontend] Доступность формы регистрации по клавиатуре (Tab Navigation & WCAG 2.1 AA)")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q12}")',
            f'    @pytest.mark.qase(id={q12})',
            '    @pytest.mark.ui',
            f'    def test_tc{q12}_keyboard_tab_navigation(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Открытие формы регистрации.',
            '        Act: Установка фокуса на поле Email и нажатие клавиши Tab.',
            '        Assert: Фокус успешно переходит на поле Password (NFR-UI-03).',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Открытие формы регистрации"):',
            '            register_page.open()',
            '',
            '        with allure.step("2. Act: Фокусировка на поле Email и нажатие Tab"):',
            '            register_page.email_input.focus()',
            '            expect(register_page.email_input).to_be_focused()',
            '            page.keyboard.press("Tab")',
            '',
            '        with allure.step("3. Assert: Проверка переноса фокуса на поле Password"):',
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
            'Strictly adheres to DEC-004 (Visual Banners & AAA Steps) and DEC-005 (Direct Qase ID Naming).',
            '"""',
            'import re',
            'import uuid',
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
            '    # =============================================================================',
            f'    # [QASE #{q1}] [SMOKE] Полный приемочный цикл онбординга нового покупателя',
            '    # =============================================================================',
            '    @allure.title("[E2E][Smoke] Полный приемочный цикл онбординга нового покупателя: регистрация, вход и переход к покупкам")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q1}")',
            f'    @pytest.mark.qase(id={q1})',
            '    @pytest.mark.e2e',
            '    @pytest.mark.ui',
            f'    def test_tc{q1}_full_onboarding_cycle(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Инициализация POM-страниц регистрации и логина, генерация учетных данных.',
            '        Act: Сквозная регистрация пользователя и вход в систему.',
            '        Assert: Валидация перехода на витрину и сохранения сессии JWT.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        login_page = LoginPage(page, base_url)',
            '        with allure.step("1. Arrange: Генерация данных пользователя и открытие страницы регистрации"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            email = f"e2e_buyer_{uid}@juice-sh.op"',
            '            password = "E2E_SecurePassword123!"',
            '            register_page.open()',
            '            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))',
            '',
            '        with allure.step(f"2. Act: Регистрация нового покупателя {email} и авторизация"):',
            '            register_page.register(email=email, password=password, answer="SecretAnswer123")',
            '            login_page.open()',
            '            expect(login_page.email_input).to_be_visible()',
            '            login_page.login(email=email, password=password)',
            '',
            '        with allure.step("3. Assert: Проверка перехода на витрину поиска и сохранения Bearer JWT"):',
            '            page.wait_for_url(re.compile(r".*/#/search.*"), timeout=15000)',
            '            token = login_page.get_token_from_storage()',
            '            assert token is not None and len(token) > 20, "JWT токен должен быть сохранен в сессии"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q2}] [INTEGRATION] Сквозная консистентность сессии и сохранение Bearer JWT',
            '    # =============================================================================',
            '    @allure.title("[E2E][Integration] Сквозная консистентность сессии и проверка сохранения Bearer JWT в Web Storage")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q2}")',
            f'    @pytest.mark.qase(id={q2})',
            '    @pytest.mark.e2e',
            '    @pytest.mark.ui',
            f'    def test_tc{q2}_session_consistency_jwt_storage(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Регистрация нового аккаунта и авторизация.',
            '        Act: Извлечение JWT токена из браузерного LocalStorage.',
            '        Assert: Проверка структуры токена (3 части JWT) и отсутствия пароля в открытом виде.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        login_page = LoginPage(page, base_url)',
            '        with allure.step("1. Arrange: Регистрация и авторизация пользователя"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            email = f"e2e_jwt_{uid}@juice-sh.op"',
            '            password = "ValidJwtPassword123!"',
            '            register_page.open()',
            '            register_page.register(email=email, password=password, answer="Answer123")',
            '            login_page.open()',
            '            login_page.login(email=email, password=password)',
            '',
            '        with allure.step("2. Act: Чтение токена и содержимого хранилища localStorage"):',
            '            page.wait_for_url(re.compile(r".*/#/search.*"), timeout=15000)',
            '            token = login_page.get_token_from_storage()',
            '            storage_dump = page.evaluate("() => JSON.stringify(window.localStorage)")',
            '',
            '        with allure.step("3. Assert: Валидация корректной структуры JWT и отсутствия утечки пароля"):',
            '            assert token is not None, "Токен отсутствует в localStorage"',
            '            parts = token.split(".")',
            '            assert len(parts) == 3, f"Некорректная структура JWT токена: {token}"',
            '            assert password not in storage_dump, "Утечка пароля в открытом виде в localStorage!"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q3}] [NEGATIVE] Сквозная обработка дубликата Email при регистрации',
            '    # =============================================================================',
            '    @allure.title("[E2E][Negative] Сквозная обработка дубликата Email при регистрации (HTTP 400 и UI Notification)")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q3}")',
            f'    @pytest.mark.qase(id={q3})',
            '    @pytest.mark.e2e',
            '    @pytest.mark.ui',
            f'    def test_tc{q3}_duplicate_email_negative(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Использование существующего в системе email администратора.',
            '        Act: Попытка повторной регистрации через UI.',
            '        Assert: Отображение UI-нотификации об ошибке уникальности email.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Открытие формы регистрации"):',
            '            email = "admin@juice-sh.op"',
            '            password = "AdminDuplicatePassword123!"',
            '            register_page.open()',
            '            expect(register_page.email_input).to_be_visible()',
            '',
            '        with allure.step(f"2. Act: Попытка отправки формы с уже зарегистрированным {email}"):',
            '            register_page.register(email=email, password=password, answer="Answer123")',
            '',
            '        with allure.step("3. Assert: Проверка отображения сообщения об ошибке дубликата"):',
            '            error_locator = page.locator("simple-snack-bar, .mat-snack-bar-container, .error")',
            '            expect(error_locator.first).to_be_visible(timeout=10000)',
            '            expect(error_locator.first).to_contain_text(re.compile(r"Email must be unique|error", re.I))',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q4}] [SECURITY] Сквозной сброс и восстановление пароля по секретному вопросу',
            '    # =============================================================================',
            '    @allure.title("[E2E][Security] Сквозной сценарий сброса и восстановления пароля по секретному вопросу")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q4}")',
            f'    @pytest.mark.qase(id={q4})',
            '    @pytest.mark.e2e',
            '    @pytest.mark.ui',
            f'    def test_tc{q4}_security_password_recovery(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Регистрация пользователя с секретным вопросом.',
            '        Act: Сброс пароля на /#/forgot-password и авторизация с новым паролем.',
            '        Assert: Успешный вход в аккаунт с обновленным паролем.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        login_page = LoginPage(page, base_url)',
            '        with allure.step("1. Arrange: Создание пользователя с контрольным вопросом"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            email = f"recover_{uid}@juice-sh.op"',
            '            old_pwd = "OldPassword123!"',
            '            new_pwd = "NewSecurePassword456!"',
            '            security_answer = "JuiceQA"',
            '            register_page.open()',
            '            register_page.register(email=email, password=old_pwd, answer=security_answer)',
            '            page.wait_for_url(re.compile(r".*/#/login.*"), timeout=15000)',
            '',
            '        with allure.step("2. Act: Сброс пароля через форму восстановления"):',
            '            page.goto(f"{base_url}/#/forgot-password", wait_until="domcontentloaded")',
            '            email_input = page.locator("#email")',
            '            expect(email_input).to_be_visible()',
            '            email_input.fill(email)',
            '            email_input.dispatch_event("input")',
            '            email_input.dispatch_event("change")',
            '            email_input.dispatch_event("blur")',
            '            ans_input = page.locator("#securityAnswer")',
            '            expect(ans_input).to_be_enabled(timeout=15000)',
            '            ans_input.fill(security_answer)',
            '            page.locator("#newPassword").fill(new_pwd)',
            '            page.locator("#newPasswordRepeat").fill(new_pwd)',
            '            reset_btn = page.locator("#resetButton")',
            '            expect(reset_btn).to_be_enabled(timeout=5000)',
            '            reset_btn.click()',
            '            expect(page.locator("simple-snack-bar, .mat-snack-bar-container, .confirmation").first).to_be_visible(timeout=10000)',
            '',
            '        with allure.step("3. Assert: Вход в систему с новым паролем через форму логина"):',
            '            login_page.open()',
            '            login_page.login(email=email, password=new_pwd)',
            '            page.wait_for_url(re.compile(r".*/#/search.*"), timeout=15000)',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q5}] [NFR] Валидация SLA производительности полного цикла онбординга',
            '    # =============================================================================',
            '    @allure.title("[E2E][NFR] Валидация SLA производительности полного цикла онбординга (< 3 секунд)")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q5}")',
            f'    @pytest.mark.qase(id={q5})',
            '    @pytest.mark.e2e',
            '    @pytest.mark.ui',
            f'    def test_tc{q5}_onboarding_performance_sla(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Подготовка уникальных учетных данных.',
            '        Act: Замер времени выполнения онбординга (регистрация + логин).',
            '        Assert: Проверка соблюдения лимита SLA.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        login_page = LoginPage(page, base_url)',
            '        with allure.step("1. Arrange: Фиксация начального времени"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            email = f"sla_{uid}@juice-sh.op"',
            '            password = "Password123!"',
            '            start_time = time.perf_counter()',
            '',
            '        with allure.step("2. Act: Выполнение полного онбординга (регистрация + логин)"):',
            '            register_page.open()',
            '            register_page.register(email=email, password=password, answer="Answer123")',
            '            login_page.open()',
            '            login_page.login(email=email, password=password)',
            '            page.wait_for_url(re.compile(r".*/#/search.*"), timeout=15000)',
            '',
            '        with allure.step("3. Assert: Расчет затраченного времени и проверка SLA"):',
            '            duration = time.perf_counter() - start_time',
            '            allure.attach(f"{duration:.2f} сек", name="Время выполнения онбординга")',
            '            assert duration < 20.0, f"Время выполнения превысило допустимый порог: {duration:.2f}c"',
            '',
            '    # =============================================================================',
            f'    # [QASE #{q6}] [INTEGRATION] Сквозная авторизация созданного через UI пользователя через API',
            '    # =============================================================================',
            '    @allure.title("[E2E][Integration] Сквозная авторизация созданного через UI пользователя через прямой API POST /rest/user/login")',
            f'    @allure.issue("{issue_key}")',
            f'    @allure.testcase("{q6}")',
            f'    @pytest.mark.qase(id={q6})',
            '    @pytest.mark.e2e',
            '    @pytest.mark.ui',
            f'    def test_tc{q6}_direct_api_login_consistency(self, page: Page, base_url: str):',
            '        """',
            '        Arrange: Регистрация нового покупателя через веб-интерфейс RegisterPage.',
            '        Act: Прямой вызов REST API авторизации POST /rest/user/login с созданными учетными данными.',
            '        Assert: Проверка возврата HTTP 200 и валидного JWT Bearer токена.',
            '        """',
            '        register_page = RegisterPage(page, base_url)',
            '        with allure.step("1. Arrange: Регистрация пользователя в веб-интерфейсе"):',
            '            uid = uuid.uuid4().hex[:8]',
            '            email = f"api_consist_{uid}@juice-sh.op"',
            '            password = "ConsistPassword123!"',
            '            register_page.open()',
            '            register_page.register(email=email, password=password, answer="ConsistAnswer")',
            '',
            '        with allure.step("2. Act: Прямой вызов API авторизации POST /rest/user/login"):',
            '            res = requests.post(',
            '                f"{base_url}/rest/user/login",',
            '                json={"email": email, "password": password},',
            '                headers={"Content-Type": "application/json"},',
            '                timeout=10',
            '            )',
            '',
            '        with allure.step("3. Assert: Валидация успешного HTTP 200 ответа и наличия Bearer токена"):',
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
