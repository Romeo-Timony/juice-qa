# QA Automation Framework — OWASP Juice Shop

Комплексный фреймворк автоматизированного тестирования на Python, построенный вокруг оркестрации **n8n**, задач **Jira (DoR Gate)**, тест-дизайна в **Qase TMS** и отчетности **Allure Report**.

---

## 📁 Структура проекта

```text
qa-automation/
├── .env                          # Локальные переменные окружения и токены
├── .gitignore                    # Игнорируемые артефакты, кеши и видео
├── conftest.py                   # Глобальные фикстуры, Playwright сессии, перехват скриншотов/видео
├── pytest.ini                    # Конфигурация Pytest, маркеры qase, api, ui
├── requirements.txt              # Зависимости Python
├── sync_qase_tests.py            # Синхронизация и аудит покрытия Qase TMS (AST-парсер)
│
├── api/                          # HTTP REST клиент для соковых эндпоинтов
│   ├── __init__.py
│   └── client.py                 # JuiceShopApiClient (auth, users, addresses, uploads)
│
├── pages/                        # Page Object Model для Angular интерфейса
│   ├── __init__.py
│   ├── base_page.py              # Базовый класс страницы
│   ├── login_page.py             # Форма авторизации (/#/login)
│   ├── register_page.py          # Форма регистрации (/#/register)
│   ├── profile_page.py           # Страница профиля и аватара (/#/profile)
│   └── change_password_page.py   # Форма смены пароля (/#/privacy-security/change-password)
│
├── schemas/                      # Pydantic v2 модели контрактов API
│   ├── __init__.py
│   └── models.py                 # UserRegistrationResponse, LoginResponse, AddressResponse, ApiErrorResponse
│
├── tests/                        # Тестовые сьюты с привязкой к User Story (Jira)
│   ├── review/                   # Карантинная зона (Staging) перед ревью команды и AI
│   │   ├── backend/
│   │   ├── frontend/
│   │   ├── REVIEW_REPORT.md      # Автоматический отчет независимого AI-аудитора
│   │   └── QASE_MANUAL_AUDIT_REPORT.md # Отчет валидации ручных кейсов в Qase
│   ├── backend/
│   │   ├── __init__.py
│   │   └── test_js16_user_profile.py   # Все API тесты по задаче JS-16 (12 кейсов)
│   └── frontend/
│       ├── __init__.py
│       └── test_js16_user_profile.py   # Все UI тесты по задаче JS-16 (9 автоматизированных кейсов)
│
├── n8n/                          # Интеграции и воркфлоу оркестратора
│   ├── dor-workflow/             # Контур 1: DoR Gate, AI Test Design & Qase Sync
│   └── autotest-workflow/        # Контур 2: Auto-Test Scaffolding, Execution & DoD
│
└── scripts/                      # Вспомогательные скрипты
    ├── hitl_review_gate.py       # Двухэтапный Human-in-the-Loop & Independent AI Review Gate
    └── provisioning/             # Скрипты первичного засева Jira, Confluence и Qase
```

---

## 🚀 Быстрый старт

### 1. Установка окружения
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Запуск автотестов
```bash
# Запуск всех автотестов (API + UI)
pytest

# Запуск только Backend API тестов задачи JS-16
pytest tests/backend/test_js16_user_profile.py

# Запуск только Frontend UI тестов задачи JS-16
pytest tests/frontend/test_js16_user_profile.py

# Запуск конкретного тест-кейса по маркеру Qase
pytest -m "qase and api"
```

### 3. Аудит соответствия Qase TMS
```bash
python sync_qase_tests.py
```

### 4. Двусторонняя синхронизация с Qase TMS (Жизненный цикл тестов)
```bash
# Проверка расхождений (Drift Detection) между Qase TMS и автотестами в коде
python scripts/qase_lifecycle_sync.py --drift

# Адаптация автотеста при изменении/удалении кейса в Qase (с помещением в tests/review/)
python scripts/qase_lifecycle_sync.py --sync-case 81
```

### 5. Human-in-the-Loop & Независимый AI-Аудит (Review Gate)
```bash
# Gate 1: Независимая AI-валидация ручных тест-кейсов в Qase TMS
python scripts/hitl_review_gate.py --audit-qase --issue JS-16

# Gate 2: Статический анализ и независимое AI-код-ревью автотестов в staging (tests/review/)
python scripts/hitl_review_gate.py --audit

# Gate 2: Акцепт и промоушн автотестов в боевую кодовую базу (tests/backend/ и tests/frontend/)
python scripts/hitl_review_gate.py --promote --approved-by "QA Lead" --issue JS-16
```

### 6. Просмотр отчета Allure
```bash
allure serve allure-results
```

---

## 🛡️ Ключевые архитектурные решения

1. **Task-Driven организация**:
   Тесты сгруппированы в файлы по бизнес-задачам Jira (`test_<issue_key>_<slug>.py`). Внутри файлов тесты структурированы по классам тестовых сьютов (`class TestUserRegistrationAPI`, `class TestAuthenticationAPI` и др.).
2. **Пирамида тестирования и селективная автоматизация**:
   * **Backend**: 100% покрытие API кейсов с Pydantic валидацией схем (`to-be-automated = 1`).
   * **Frontend**: автоматизация критических пользовательских путей (`to-be-automated = 1`), исследовательские и сложные визуальные кейсы остаются ручными (`to-be-automated = 0`).
3. **Автоматический сбор артефактов при падениях**:
   * При сбое UI теста в Allure автоматически прикрепляется полный скриншот экрана (`.png`) и видео-скринкаст сессии (`.webm`).
   * При успешном прохождении тестов видео удаляются для экономии дискового пространства.
4. **Трассируемость (Traceability)**:
   Каждый тест содержит ссылки на задачу Jira, тест-кейс Qase, подробное Gherkin-описание в docstring и исполняемые шаги Allure.
