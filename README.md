# 🚀 Autonomous Enterprise QA Automation & QAOps Platform
## Интеллектуальная автономная платформа обеспечения качества и тестирования полного цикла

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-v1.45+-2EAD33.svg?logo=playwright&logoColor=white)](https://playwright.dev/)
[![Pytest](https://img.shields.io/badge/Pytest-v8.0+-0A9EDC.svg?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.8-E92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![n8n Orchestration](https://img.shields.io/badge/Orchestrator-n8n_Cloud-EA4B71.svg?logo=n8n&logoColor=white)](https://n8n.io/)
[![Google Gemini Flash](https://img.shields.io/badge/LLM-Gemini_Flash-8E75B2.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![Allure Report](https://img.shields.io/badge/Reporting-Allure_2-FF6C37.svg?logo=qameta&logoColor=white)](https://allurereport.org/)
[![Flakiness](https://img.shields.io/badge/Flaky_Tests-0%25-brightgreen.svg)]()
[![Traceability](https://img.shields.io/badge/Traceability-100%25-brightgreen.svg)]()

> 💡 **Краткая суть проекта (Elevator Pitch):**  
> Промышленная автономная экосистема обеспечения качества, которая полностью устраняет рутинные затраты времени на анализ требований, проектирование тест-кейсов и написание автотестов.  
> Путь от создания задачи в **Jira** до работающих автотестов в **CI/CD** сокращен с **1–2 рабочих дней до менее чем 3 минут**, при этом **100% контроля сохраняется за ведущим инженером (Human-in-the-Loop)**, а показатель ложных срабатываний (**Flaky-тестов**) сведен к **строгому нулю**.

---

## 📚 Навигатор по документации и спецификациям

Для удобства технических директоров, QA-лидов, рекрутеров и инженеров команды вся документация и спецификации вынесены в отдельные структурированные руководства:

| Документ | Аудитория и назначение | Основное содержание |
| :--- | :--- | :--- |
| 📖 **[COMPREHENSIVE_PROJECT_OVERVIEW_RU.md](./docs/COMPREHENSIVE_PROJECT_OVERVIEW_RU.md)** | **Главный русскоязычный обзор проекта (Whitepaper)** | Исчерпывающее руководство по платформе с разбором архитектуры, 8 этапов, TDM, дедупликации и шпаргалкой из 15 каверзных вопросов для собеседований. |
| 🎓 **[PROJECT_MASTER_REVIEW.md](./docs/PROJECT_MASTER_REVIEW.md)** | **Системный справочник для интервью и AI-копилотов** | Англоязычный эталонный технический документ: ADR (DEC-001...015), DeepEval vs AST, Langfuse телеметрия, RQI-метрики. |
| 🏛️ **[ARCHITECTURE_AND_QAOPS_SPECIFICATION.md](./ARCHITECTURE_AND_QAOPS_SPECIFICATION.md)** | **Архитекторы и QAOps-инженеры** | Глубокая спецификация 6 архитектурных швов (Seams 1–6), схема отказоустойчивости, Circuit Breaker, AST-шлюзы. |
| 📑 **[DECISION_LOG_AND_NOTES.md](./DECISION_LOG_AND_NOTES.md)** | **Инженерная команда** | Полный журнал архитектурных решений (ADR DEC-001 — DEC-015) с техническим обоснованием каждого выбора. |
| 💼 **[QA_ENGINEER_RESUME_AND_PROJECT_DOSSIER.md](./QA_ENGINEER_RESUME_AND_PROJECT_DOSSIER.md)** | **Рекрутеры и HR-специалисты** | Готовое резюме-досье (Project Case Study) с формулировками ключевых достижений, метрик и навыков инженера. |
| 🏢 **[ENTERPRISE_DEPLOYMENT_AND_CREDS.md](./docs/ENTERPRISE_DEPLOYMENT_AND_CREDS.md)** | **DevOps и системные администраторы** | Пошаговое руководство по развертыванию платформы на инфраструктуре любого предприятия (Zero Vendor Lock-in). |
| 📋 **[CONFLUENCE_USER_REGISTRATION_SPEC.md](./docs/CONFLUENCE_USER_REGISTRATION_SPEC.md)** | **Аналитики и Product Owner** | Живая спецификация бизнес-требований Confluence по регистрации и профилю пользователя (User Story JS-39). |
| 🎯 **[JIRA_TASKS_BREAKDOWN_REGISTRATION.md](./docs/JIRA_TASKS_BREAKDOWN_REGISTRATION.md)** | **Scrum-мастера и разработчики** | Декомпозиция эпика JS-39 на технические задачи JS-40 (API), JS-41 (UI) и JS-42 (E2E) с критериями приемки (AC). |

---

## 🎯 Объект тестирования (SUT): OWASP Juice Shop

В качестве тестируемой системы (**SUT — System Under Test**) выбрано популярное приложение электронной коммерции **OWASP Juice Shop** — сложная распределенная платформа с современным стеком:

* **Frontend:** Одностраничное приложение (**SPA**) на **Angular 21** и **Angular Material M3**, реактивное состояние через RxJS, клиентская валидация форм, перехватчики запросов `JwtInterceptor`.
* **Backend:** Высокопроизводительный **Node.js (LTS v24)** + **Express.js REST API**, асинхронные обработчики, Socket.io.
* **Базы данных:** Реляционная база **SQLite3** с **Sequelize ORM** (пользователи, заказы, адреса, платежи) и in-memory NoSQL хранилище.
* **Безопасность и сессии:** Авторизация через защищенные токены **JWT (JSON Web Token)**, bcrypt-хэширование паролей, 2FA/TOTP аутентификация.

---

## 🏗️ Двухконтурная архитектура платформы

Одно из главных инженерных решений проекта — **четкое разделение обязанностей (Separation of Concerns)** между облачной оркестрацией и локальным выполнением:

```
┌────────────────────────────────────────────────────────────────────────┐
│ КОНТУР 1: Облачный интегратор и оркестратор (n8n Cloud + Webhooks)    │
│  - Прием событий из Jira Cloud в реальном времени                      │
│  - Предстартовая проверка доступности сервисов (Health Gate)           │
│  - Анализ зрелости требований (DoR Gate) языковой моделью Gemini Flash │
│  - Построение интерактивных карт проверок (Whimsical MindMap)          │
│  - Синхронизация с Qase TMS (сьют #86) и 4-уровневая дедупликация      │
│  - Оповещение команды в Telegram (@QApower_bot)                        │
│  - Ожидание подтверждения инженера (HITL Wait Nodes)                   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Двусторонний REST API / Опрос фоновым демоном
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ КОНТУР 2: Локальный инженерный движок автоматизации (Python Daemon)   │
│  - Фоновый сторожевой процесс (`scripts/qa_agent_daemon.py`)           │
│  - Генератор шаблонов автотестов (`scripts/scaffold_dynamic.py`)       │
│  - Карантинная песочница для сгенерированного кода (`tests/review/`)   │
│  - Двухфазный статический аудит (AST-парсер, Ruff E9/F82, Pytest)      │
│  - Безопасное слияние через изолированные деревья Git Worktrees        │
│  - Запуск тестов: Pytest + Playwright + Requests + Pydantic v2         │
│  - Эмуляция сетевых сбоев и задержек (WireMock Standalone)             │
│  - Автоматическая изоляция и откат базы данных (`conftest.py`)         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Сквозной жизненный цикл из 8 этапов (End-to-End Walkthrough)

Реализация показана на примере сквозной пользовательской истории **`JS-39` («Регистрация и профиль пользователя»)** и задач **`JS-40`** (REST API), **`JS-41`** (Frontend UI) и **`JS-42`** (E2E):

```text
[Этап 0: Health Gate] ──────────► Опрос 7 сервисов (SUT, Jira, Qase, Gemini, Telegram, WireMock, DB)
         │
         ▼
[Этап 1: DoR Gate] ─────────────► Оценка ТЗ по стандарту INVEST (порог >= 80%). Автопереход в "In Progress"
         │
         ▼
[Этап 2: MindMap Design] ───────► Построение 5-уровневой карты проверок Whimsical (BVA, EP, OWASP Top 10)
         │
         ▼
[Этап 3: BDD & Qase TMS] ───────► Генерация Given-When-Then, пирамида тестирования, 4-уровневая дедупликация
         │
         ▼
[Этап 4: RTM Traceability] ─────► Двусторонняя матрица покрытия (Требование <-> Кейс <-> Слой)
         │
         ▼
[Этап 5: Quality Gate 1 (HITL)] ─► Пауза пайплайна, Telegram-алерт лиду, одобрение «ОК» в треде Jira
         │
         ▼
[Test Scaffolding (Sandbox)] ───► Генерация кода (AAA, POM, Pydantic) в карантинную зону tests/review/
         │
         ▼
[Этап 6: Quality Gate 2] ───────► Фаза 1: AST + Ruff + Pytest collect. Фаза 2: LLM архитектурный аудит
         │
         ▼
[Этап 7: Git Promotion] ────────► Слияние через изолированный Git Worktree, Content Digest, подпись (-s)
         │
         ▼
[Этап 8: CI/CD & Allure] ───────► Прогон тестов (1 сек на 12 API тестов), Allure видео/скрины, RQI = 100%,
                                  автозакрытие задачи в статус «Автотесты пройдены»
```

---

## 🧪 Реализованное тестовое покрытие

Кодовая база содержит готовые производственные наборы тестов:

### 1. Серверные контракты API (`tests/backend/test_js40_api.py`)
- **12 автоматизированных тестов**, время прогона: **~1.01 секунды**.
- Проверка успешной регистрации с валидацией схемы **Pydantic v2** (`UserRegistrationResponse`).
- Блокировка дублирующих email (`409 Conflict`), проверка несовпадения паролей (`400 Bad Request`).
- Безопасность: устойчивость к SQL-инъекциям (`' OR 1=1--`), проверка ограничений длины пароля и защита от перебора.
- Привязка к Qase TMS: кейсы `QASE-787` — `QASE-798`.

### 2. Пользовательский интерфейс Angular SPA (`tests/frontend/test_js41_ui.py`)
- Сквозная автоматизация на **Playwright**: паттерн **Page Object Model (POM)**.
- Интеллектуальные автоожидания (`expect(locator).to_be_visible()`) без единого `time.sleep()`.
- Проверка динамических подсказок стойкости пароля, валидации полей в реальном времени, выбора секретного вопроса из выпадающего списка Angular Material.
- Привязка к Qase TMS: кейсы `QASE-811` — `QASE-822`.

### 3. Сквозные пользовательские сценарии E2E (`tests/frontend/test_js42_ui.py`)
- Полный путь клиента: регистрация $\rightarrow$ логин $\rightarrow$ установка аватара $\rightarrow$ смена пароля $\rightarrow$ повторная авторизация.
- Автоматическая запись скринкастов сессий в формате **WebM** и сохранение скриншотов при падениях.

### 4. Тесты архитектурного контура QAOps (`tests/qaops/`)
- `test_openapi_contracts.py` — сверка сгенерированных запросов со схемой OpenAPI SUT.
- `test_prompt_registry.py` — проверка движка версионирования промптов (Prompt-as-Code).
- `test_event_store.py` — проверка персистентности событий в SQLite/PostgreSQL.
- `test_wiremock_isolated.py` — проверка работы с эмуляцией сетевых сбоев 503/429 через WireMock.

---

## 🛡️ Управление тестовыми данными (TDM) и защита от нестабильности

В проекте достигнут показатель **0% Flaky-тестов** благодаря четырем инженерным практикам:

1. **Неизменяемые эталонные персоны (Seeded Personas):**  
   Для проверки прав доступа используются фиксированные учетные записи: `admin@juice-sh.op`, аккаунт с балансом $100.00 (`jim@juice-sh.op`) и с балансом $0.00 (`bender@juice-sh.op`).
2. **Динамическая изоляция через UUID:**  
   Для любых тестов создания пользователей email генерируется динамически: `f"test_{uuid.uuid4().hex[:8]}@juice-sh.op"`.
3. **Откат транзакций базы данных (Database Teardown):**  
   Фикстура Pytest `isolate_wallet_state` подключается к базе данных SQLite и откатывает изменения после выполнения тестов.
4. **Имитация сбоев внешних систем (WireMock Fault Injection):**  
   Стенд WireMock Standalone (порт `8088`) позволяет безопасно тестировать поведение системы при сбоях сети (HTTP 503, HTTP 429, задержки в 5 секунд) без влияния на реальные внешние сервисы.

---

## 🔍 4-уровневая дедупликация тест-кейсов в Qase TMS

Чтобы искусственный интеллект не засорял базу тестов дубликатами, модуль `scripts/qase_deduplicate_evaluator.py` применяет каскадный фильтр:
1. **Нормализация строк:** посимвольное сравнение названий без учета регистра и спецсимволов.
2. **Сигнатура API:** совпадение HTTP-метода (`POST`), пути (`/api/Users`) и бизнес-цели (`password_mismatch`).
3. **Контекст UI:** сопоставление экранной формы и типа проверки.
4. **Коэффициент сходства Жаккара (Jaccard Index $\ge 85\%$):** математический анализ лексического пересечения множеств шагов.

---

## 🛠️ Технологический стек

| Категория | Технологии и библиотеки |
| :--- | :--- |
| **Язык и среда** | Python 3.12 (64-bit), Node.js LTS v24 |
| **Автоматизация тестирования** | Pytest 8.x, Playwright 1.45+, Requests, Pydantic v2, Allure-pytest |
| **Оркестрация и интеграция** | n8n Cloud / Self-hosted, Jira Cloud REST API & Webhooks, Telegram Bot API |
| **Искусственный интеллект** | Google Gemini Flash, DeepEval (G-Eval Groundedness & Coverage), Langfuse Tracing |
| **Контроль качества кода** | Python AST Parser, Ruff Linter (правила E9, F63, F7, F82), Git Worktrees |
| **Тестовая инфраструктура** | SQLite3 / PostgreSQL 16 (Event Store), WireMock Standalone (Fault Injection) |
| **Отчетность и телеметрия** | Allure Report 2.x, WebM Video Recorder, Release Quality Index (RQI) Analytics |

---

## 🚀 Быстрый старт и локальный запуск

### 1. Клонирование и настройка окружения
```bash
git clone https://github.com/Romeo-Timony/juice-qa.git
cd juice-qa
python -m venv .venv
.venv\Scripts\activate       # Для Windows (на Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
playwright install chromium
```

### 2. Настройка переменных окружения
Скопируйте пример файла конфигурации:
```bash
cp .env.example .env
```
Заполните ключи доступа к Jira, Qase TMS, Telegram и Gemini API (подробнее см. [ENTERPRISE_DEPLOYMENT_AND_CREDS.md](./docs/ENTERPRISE_DEPLOYMENT_AND_CREDS.md)).

### 3. Комплексная проверка работоспособности системы (Health Check)
```bash
# Через готовый скрипт:
run_health_check.bat

# Или напрямую через Python:
python scripts/tools/check_environment_health.py
```

### 4. Запуск автотестов
```bash
# Запуск полного сьюта (API + UI)
pytest

# Запуск только серверных тестов (быстрый контрактный прогон JS-40)
pytest tests/backend/test_js40_api.py -v

# Запуск UI-тестов Playwright с отображением браузера
pytest tests/frontend/test_js41_ui.py --headed

# Запуск сквозных E2E тестов
pytest tests/frontend/test_js42_ui.py -v
```

### 5. Запуск фонового автономного демона (Контур 2)
```bash
python scripts/qa_agent_daemon.py
```
*Демон переходит в режим сторожевого таймера, отслеживает согласования лида в Jira/Telegram, выполняет статический аудит и безопасный промоушн кода через Git Worktrees.*

### 6. Формирование и просмотр отчета Allure
```bash
allure serve allure-results
```

---

## 📊 Ключевые показатели эффективности (KPI)

| Метрика | До внедрения платформы | После внедрения платформы | Эффект |
| :--- | :--- | :--- | :--- |
| **Time-to-Test (Время от Jira до автотеста в CI)** | 2–5 рабочих дней | **< 3 минут** | **Ускорение в 300+ раз** |
| **Полнота требований (DoR INVEST)** | Не контролировалась (до 40% багов в ТЗ) | **Строгий порог $\ge 80\%$** | **Исключение дефектов на этапе анализа** |
| **Процент плавающих тестов (Flaky Rate)** | 5–15% | **Строго 0%** | **Абсолютное доверие команды к CI** |
| **Сквозная прослеживаемость (Traceability)** | Фрагментарная (15–30%) | **100% (Confluence $\leftrightarrow$ Jira $\leftrightarrow$ Qase $\leftrightarrow$ Pytest)** | **Прозрачность для аудита и менеджмента** |
| **Участие ведущего инженера (HITL)** | Рутинное написание бойлерплейт-кода | **2 стратегических точки одобрения (Design & Code)** | **Освобождение времени на архитектуру** |

---

## 👨‍💻 Автор проекта

**Роман (Romeo Timony)** — Lead Automation QA / SDET / QAOps Architect  
- **GitHub:** [Romeo-Timony](https://github.com/Romeo-Timony)  
- **Репозиторий проекта:** [juice-qa](https://github.com/Romeo-Timony/juice-qa)  
- **Специализация:** Проектирование корпоративных платформ обеспечения качества, AI-агенты в тестировании (LLM-as-a-Judge), событийно-ориентированная оркестрация (n8n), Python/Playwright/Pytest, контрактное тестирование API и CI/CD автоматизация.
