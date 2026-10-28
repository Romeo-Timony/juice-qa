# 📋 База заметок и журнал совместных решений (Decision Log & SDET Architecture Notes)

Единый официальный реестр проектных решений, архитектурных стандартов и соглашений по кодовой базе автоматизации тестирования **OWASP Juice Shop (QA & SDET Ecosystem)**.

---

## 🚦 Статусы решений

| Статус | Значок | Значение |
| :--- | :---: | :--- |
| **В обсуждении** | `[💡 DISCUSS]` | Идея предложена, требует уточнения скоупа или критериев. |
| **Делаем сейчас** | `[🚀 NOW]` | Утверждено к немедленной реализации в текущем спринте. |
| **Отложено в бэклог**| `[⏳ LATER]` | Полезная идея, отложена на будущие спринты (Sprint 2+ / Post-MVP). |
| **Реализовано** | `[✅ DONE]` | Решение внедрено в кодовую базу, зафиксировано в Git и готово к использованию. |

---

## 📊 Реестр инициатив и решений

| ID | Инициатива / Заметка | Категория | Влияние (Impact / Effort) | Решение | Статус | Связанные файлы / Задачи |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **DEC-001** | **Параметризация автотестов по 3 видам пользователей** (Admin, Jim с $100, Bender с $0). | Test Data | **High / Low** (ускоряет тесты, убирает флаки) | **Реализовать** | `[✅ DONE]` | [`qa-automation/data/users.py`](file:///d:/Desktop/Juice_shop/qa-automation/data/users.py)<br>[`qa-automation/conftest.py`](file:///d:/Desktop/Juice_shop/qa-automation/conftest.py)<br>[`tests/api/personas/`](file:///d:/Desktop/Juice_shop/qa-automation/tests/api/personas/) |
| **DEC-002** | **Архитектура пирамиды тестов и политика Framework DoD** (Unit, API, UI, E2E, QAOps). | Architecture | **High / Medium** (масштабируемость, предотвращение деградации) | **Реализовать** | `[✅ DONE]` | [`TEST_SUITE_ARCHITECTURE.md`](file:///d:/Desktop/Juice_shop/qa-automation/TEST_SUITE_ARCHITECTURE.md)<br>[`tests/`](file:///d:/Desktop/Juice_shop/qa-automation/tests/) |
| **DEC-003** | **Изоляция тестовых данных и автоматический Teardown** (`isolate_wallet_state` для SQLite). | Reliability | **High / Low** (100% идемпотентность прогонов) | **Реализовать** | `[✅ DONE]` | [`qa-automation/conftest.py`](file:///d:/Desktop/Juice_shop/qa-automation/conftest.py) |
| **DEC-004** | **Стандарты визуальной маркировки автотестов и ANSI-отчетов**: блок-баннеры `# === [QASE #ID]`, шаблон AAA, ANSI-матрица. | AQA DX | **High / Low** (читаемость глазами и трассируемость) | **Реализовать** | `[✅ DONE]` | [`tests/api/auth/test_auth_api.py`](file:///d:/Desktop/Juice_shop/qa-automation/tests/api/auth/test_auth_api.py)<br>[`conftest.py`](file:///d:/Desktop/Juice_shop/qa-automation/conftest.py) |
| **DEC-005** | **Именование автотестов без синтетических индексов (YAGNI & Pure ISTQB Titles)**: отказ от `[API-AUTH-01]` в пользу прямых Qase ID. | Standard | **High / Low** (прозрачность покрытия, избавление от бюрократии) | **Реализовать** | `[✅ DONE]` | [`tests/api/auth/test_auth_api.py`](file:///d:/Desktop/Juice_shop/qa-automation/tests/api/auth/test_auth_api.py) |
| **DEC-006** | **Сквозная верификация пайплайна JS-40 (REST API)**: полный цикл швов 1–8, интеграция Qase, Allure, Telegram, Jira. | Pipeline | **Critical / High** (промышленный эталон поставки автотестов) | **Реализовать** | `[✅ DONE]` | Jira: `JS-40` (`Автотесты пройдены`) |
| **DEC-010** | **Устранение дублирования триггеров n8n и защита от самосогласования гейтов**: отказ от ручного webhook при наличии нативного Jira Cloud Webhook, строгая валидация автора/размера комментария при HITL. | Reliability | **Critical / Low** (чистота пайплайна, гарантированная пауза HITL) | **Реализовать** | `[✅ DONE]` | [`scripts/qa_agent_daemon.py`](file:///d:/Desktop/Juice_shop/qa-automation/scripts/qa_agent_daemon.py) |
| **DEC-011** | **Единый стандарт согласования Gate 1 и Gate 2 — только комментарий «ОК» с больших букв**: отказ от эмодзи (❤️, звездочки) и синонимов во избежание двусмысленности и ложных срабатываний. | Standard | **High / Low** (исключение человеческих и машинных ошибок) | **Реализовать** | `[✅ DONE]` | [`scripts/qa_agent_daemon.py`](file:///d:/Desktop/Juice_shop/qa-automation/scripts/qa_agent_daemon.py)<br>[`scripts/telegram_notifier.py`](file:///d:/Desktop/Juice_shop/qa-automation/scripts/telegram_notifier.py) |
| **DEC-012** | **Интеграция WireMock Standalone для герметичного тестирования и Fault Injection**: изоляция API внешних сервисов (Jira, Qase, Telegram, Juice Shop), симуляция сбоев 503/429 для Seam 4 (Circuit Breaker & Outbox). | SDET Best Practice | **Critical / Medium** (100% герметичность, независимость от внешней сети) | **Реализовать** | `[✅ DONE]` | [`wiremock/`](file:///d:/Desktop/Juice_shop/qa-automation/wiremock/)<br>[`tests/qaops/test_wiremock_isolated.py`](file:///d:/Desktop/Juice_shop/qa-automation/tests/qaops/test_wiremock_isolated.py) |
| **DEC-013** | **Промышленный статический и семантический аудит (Ruff + DeepEval G-Eval)**: включение Ruff (E9, F63, F7, F82) в Seam 3 и DeepEval в Seam 2. | Quality Gate | **High / Low** (ликвидация silent fallback, блокировка синтаксических ошибок) | **Реализовать** | `[✅ DONE]` | [`requirements.txt`](file:///d:/Desktop/Juice_shop/qa-automation/requirements.txt)<br>[`qaops/judge.py`](file:///d:/Desktop/Juice_shop/qa-automation/qaops/judge.py)<br>[`qaops/code_gate.py`](file:///d:/Desktop/Juice_shop/qa-automation/qaops/code_gate.py) |
| **DEC-014** | **Защита от дрейфа контрактов API через OpenAPI 3.0 / Swagger Validator**: автоматическая сверка схем с `/api-docs/swagger-ui-init.js` и Pydantic v2 моделями. | Contract Safety | **High / Low** (защита от несовместимости версий бэкенда) | **Реализовать** | `[✅ DONE]` | [`qaops/openapi_validator.py`](file:///d:/Desktop/Juice_shop/qa-automation/qaops/openapi_validator.py)<br>[`tests/qaops/test_openapi_contracts.py`](file:///d:/Desktop/Juice_shop/qa-automation/tests/qaops/test_openapi_contracts.py) |
| **DEC-015** | **Сквозной перехват сбоев (n8n Global Error Handler + Sentry MCP + Autonomous Crash Hook)**: связка воркфлоу `errorTrigger` в n8n с Telegram, интеграция Sentry MCP (`mcp.sentry.dev/mcp/romeoworx`) и глобального перехватчика `sys.excepthook`. | Observability & Reliability | **Critical / Low** (мгновенный алертинг при падениях flow и демона) | **Реализовать** | `[✅ DONE]` | [`scripts/tools/setup_n8n_error_workflow.py`](file:///d:/Desktop/Juice_shop/qa-automation/scripts/tools/setup_n8n_error_workflow.py)<br>[`core_utils/crash_monitor.py`](file:///d:/Desktop/Juice_shop/qa-automation/core_utils/crash_monitor.py)<br>[`mcp_config.json`](file:///C:/Users/user/.gemini/config/mcp_config.json) |

---

## 🔍 Детальные карточки решений

### 📌 DEC-001: Параметризация автотестов по 3 типам пользователей
* **Суть решения:**  
  Вместо динамической генерации случайных пользователей для каждого сценария используются сидированные учетные записи из базы Juice Shop:
  1. **Администратор (`admin@juice-sh.op`)** — проверка прав доступа, RBAC, аудит.
  2. **Покупатель с балансом (`jim@juice-sh.op`, $100)** — Happy Path оплаты кошельком и оформление Deluxe.
  3. **Покупатель без денег (`bender@juice-sh.op`, $0)** — валидация граничных условий (BVA), ошибки недостаточности средств.
* **Артефакты:**  
  [`qa-automation/data/users.py`](file:///d:/Desktop/Juice_shop/qa-automation/data/users.py), параметризованные фикстуры в [`conftest.py`](file:///d:/Desktop/Juice_shop/qa-automation/conftest.py), сьют [`tests/api/personas/test_user_personas_api.py`](file:///d:/Desktop/Juice_shop/qa-automation/tests/api/personas/test_user_personas_api.py).

---

### 📌 DEC-002: Архитектура пирамиды тестов и триггеры DoD
* **Суть решения:**  
  Внедрена 5-слойная иерархия каталогов `qa-automation/tests/`:
  - `tests/unit/`: тесты самого фреймворка (<10мс, без сети).
  - `tests/api/`: интеграционные тесты REST API по доменам (`auth`, `catalog`, `basket`, `orders`, `wallet`, `deluxe`, `user`, `administration`, `personas`).
  - `tests/ui/`: компонентные UI-тесты страниц через Playwright POM.
  - `tests/e2e/`: сквозные пользовательские сценарии покупки.
  - `tests/qaops/`: швы валидации пайплайна (Seams 1–6).
* **Framework DoD Trigger Policy:**  
  Добавление любого нового метода в `api/client.py`, модели данных или утилиты обязывает написать соответствующий Unit-тест в `tests/unit/`.

---

### 📌 DEC-003: Изоляция тестовых данных и автоматический Teardown
* **Суть решения:**  
  После выполнения тестов чекаута и списания средств фикстура `isolate_wallet_state` в `conftest.py` автоматически сбрасывает балансы пользователей в `data/juiceshop.sqlite` (Jim -> $100, Bender -> $0).
* **Результат:** 100% идемпотентность прогонов без ложноотрицательных падений.

---

### 📌 DEC-004: Стандарты визуальной маркировки автотестов и ANSI-отчетов
* **Суть решения:**  
  Для облегчения навигации глазами в коде и мгновенного понимания контекста теста внедрены:
  1. **Информационный блок-баннер над каждым тестом:**
     ```python
     # =============================================================================
     # [QASE #633] [BLOCKER] Создание учетной записи нового покупателя (POST /api/Users/)
     # =============================================================================
     @allure.title("Создание учетной записи нового покупателя с валидными параметрами -> HTTP 201 Created")
     ```
  2. **Структура Docstring по шаблону AAA (Arrange / Act / Assert):**
     Четкое описание шагов подготовки, действия и проверок прямо в документации метода.
  3. **Терминальная визуализация (`conftest.py`):**
     Цветные Cyan/Yellow/Green разделители перед запуском теста и итоговая сводная таблица результатов со статусами, временем и ссылками на Qase ID.

---

### 📌 DEC-005: Стандарт именования автотестов без синтетических индексов (YAGNI & Pure ISTQB Titles)
* **Суть решения:**  
  Упразднены искусственные индексы вида `[API-AUTH-01]`, создававшие оверинжиниринг и ломавшие нумерацию при вставке новых тестов.
* **Принятый стандарт:**
  1. **Заголовок в Allure (`@allure.title`):** Профессиональный русский язык по формуле ISTQB: *[Действие / Сценарий] при [Условие / Входные данные] -> [Ожидаемый результат]*.
  2. **Имя функции Python:** Прямая привязка к ID кейса из TMS: `test_tc{QASE_ID}_{краткая_суть}` (например, `test_tc633_register_valid_user_success`).
  3. **Связи с системами:** `@allure.issue("JS-40")`, `@allure.testcase("633")`, `@pytest.mark.qase(id=633)`.

---

### 📌 DEC-006: Сквозная верификация пайплайна JS-40 (REST API)
* **Суть решения:**  
  Задача `JS-40` (`[API] Автоматизация REST API регистрации и авторизации (POST /api/Users/)`) успешно проведена через все 8 этапов автоматического пайплайна:
  - **Этап 1:** DoR Gate (Валидация требований Jira против Confluence).
  - **Этап 2:** MindMap (Генерация интерактивной карты проверок Whimsical).
  - **Этап 3:** BDD Gherkin в Qase TMS (Создан сьют #86 с 12 тест-кейсами #633–#644).
  - **Этап 4:** RTM Matrix (Матрица прослеживаемости требований в комментариях Jira).
  - **Этап 5:** Quality Gate 1 (HITL пауза n8n, согласование тест-дизайна по эмодзи ❤️).
  - **Этап 6:** Quality Gate 2 (HITL пауза n8n, аудит кода тестов независимым AI-судьей).
  - **Этап 7:** Promotion (Слияние сгенерированных автотестов в `main`).
  - **Этап 8:** CI/CD & Reporting (GitHub Actions run, Allure-отчет, оповещение в Telegram, перевод задачи в Jira в статус `Автотесты пройдены` / 10048).

---

### 📌 DEC-007: Стандарт структуры репозитория и наведение порядка (SDET Housekeeping)
* **Суть решения:**  
  Репозиторий очищен от мусорных временных файлов и четко структурирован:
  1. **Корень (`qa-automation/`):** Содержит исключительно конфиги (`.env`, `pytest.ini`, `requirements.txt`), раннеры (`run_*.bat`), точку входа `conftest.py` и архитектурную документацию (`*.md`).
  2. **`scripts/`:** Содержит только активные операционные модули (демон, шлюзы, интеграции).
  3. **`scripts/pipeline/`:** Скрипты управления этапами пайплайна (`run_step1_trigger.py`, `run_finish_pipeline.py`, и др.).
  4. **`scripts/tools/`:** Диагностические и инспекционные утилиты (`inspect_*.py`, `check_*.py`, `debug_*.py`).
  5. **`docs/specs/`:** Сырые и спарсенные спецификации Confluence / Jira.
  6. **`docs/screenshots/`:** Скриншоты форм и экранов.
  7. **`docs/dashboards/`:** HTML-дашборды прогонов и скринкастов.
  8. **`n8n/backups/`:** Снапшоты и дампы воркфлоу n8n.
  9. **`logs/archive/`:** Архив разовых текстовых логов и трейсов.

---

### 📌 DEC-008: План перехода к следующей задаче (JS-41: Frontend UI)
* **Контекст:**  
  Задача `JS-41`: `[UI] Разработка клиентской формы регистрации и валидации полей (/#/register)`.
* **План реализации:**
  1. Разработка Page Object Model [`pages/register_page.py`](file:///d:/Desktop/Juice_shop/qa-automation/pages/register_page.py).
  2. Реализация набора UI-автотестов на Playwright в [`tests/ui/auth/test_auth_ui.py`](file:///d:/Desktop/Juice_shop/qa-automation/tests/ui/auth/test_auth_ui.py).
  3. Прогон через пайплайн n8n (DoR -> Whimsical -> Qase UI Suite -> Gate 1 -> Gate 2 -> GitHub Actions).

---

### 📌 DEC-009: Полный отказ от хардкода триггеров и ID переходов Jira
* **Проблема:**  
  Ранее скрипты запуска этапов пайплайна содержали захардкоженные ключи задач (`JS-16`, `JS-40`) и статичные ID переходов (`21`, `31`), что создавало риск ложных вызовов и делало систему жестко привязанной к конкретным тикетам.
* **Суть решения:**  
  1. Создан единый контроллер жизненного цикла [`scripts/pipeline/task_lifecycle.py`](file:///d:/Desktop/Juice_shop/qa-automation/scripts/pipeline/task_lifecycle.py).
  2. Реализовано прямое динамическое чтение состояния задач из Jira через `/rest/api/3/search/jql`.
  3. Переход в статус «В работе» (10046) или «Автотесты пройдены» (10048) выполняется через динамический поиск доступных transitions по целевому статусу через `GET /rest/api/2/issue/{key}/transitions`.
  4. Скрипты этапов (`run_step1_trigger.py`, `run_step2_gate1.py`, `run_gate2_process.py`, `run_finish_pipeline.py`) переведены на поддержку CLI-аргументов (`python run_step1_trigger.py [ISSUE_KEY]`) и автоопределение активных задач.
* **Результат:** 100% динамический запуск любой задачи бэклога без ручной правки кода.

---

### 📌 DEC-010: Устранение дублирования триггеров n8n и защита от самосогласования гейтов
* **Проблема:**  
  1. При запуске задачи параллельно стартовали два одинаковых воркфлоу n8n из-за дублирования: первый триггер посылал Jira Cloud Webhook через ngrok при транзишене, а второй вызов делался скриптом вручную.
  2. Робот-комментарий Этапа 5 содержал текст инструкции `(оставьте комментарий ❤️ или «ОК» в задаче)`. Демон `qa_agent_daemon.py` при парсинге комментариев находил символ `❤️` в тексте самой карточки и ошибочно принимал ее за согласие пользователя, мгновенно отправляя алерт о согласовании Gate 1.
* **Суть решения:**  
  1. Из [`scripts/pipeline/task_lifecycle.py`](file:///d:/Desktop/Juice_shop/qa-automation/scripts/pipeline/task_lifecycle.py) убран дублирующий ручной webhook — запуск полностью делегирован нативному Jira Cloud Webhook.
  2. В [`scripts/qa_agent_daemon.py`](file:///d:/Desktop/Juice_shop/qa-automation/scripts/qa_agent_daemon.py) функция `is_approval_comment` теперь строго проверяет `is_human_comment` ДО поиска ключевых слов и эмодзи.
  3. Все системные маркеры (`[этап`, `контроль`, `оценка качества`, длинные тексты >200 символов) безусловно отсекаются как системные.
  4. Поиск карточки `stage5_comment` и `stage6_comment` переведен на выбор последней актуальной карточки (`[-1]`), исключая гонки при дубликатах.
* **Результат:** Единичное выполнение воркфлоу n8n, строгая пауза на Quality Gate 1 и ожидание реального действия человека.

---

### 📌 DEC-011: Единый стандарт согласования гейтов — только комментарий «ОК» с больших букв
* **Контекст:**  
  Ранее в качестве аппрува допускались эмодзи (`❤️`, `❤`, звёздочки) и различные текстовые синонимы (`да`, `yes`, `ок`, `approved`). Это приводило к путанице, визуальному мусору и риску ложных срабатываний, когда эмодзи из текста подсказки считывался как согласие.
* **Принятое решение:**  
  1. **Строгий формат:** Для согласования любого этапа (Quality Gate 1, Quality Gate 2, DoR Override) принимается **исключительно комментарий `ОК`** (в верхнем регистре, кириллица `ОК` или латиница `OK`).
  2. Все эмодзи (`❤️`, `⭐`), синонимы в нижнем регистре (`ок`, `ok`) и иные формулировки полностью отключены в функции `is_approval_comment()`.
  3. Все шаблоны сообщений в Telegram, Jira, n8n и документации обновлены и прямо указывают: *«Для согласования отправьте комментарий ОК в задачу»*.
* **Результат:** 100% прозрачность, отсутствие путаницы и полная защита от непреднамеренных согласований.

---

### 📌 DEC-012: Интеграция WireMock Standalone для изоляции тестов и fault injection
* **Контекст:** Внешние сервисы (Jira, Telegram, SUT) могут быть недоступны в CI/CD или возвращать лимиты (429/503).
* **Решение:** Интегрирован `wiremock-standalone-3.9.2.jar` с изолированным запуском на динамическом порту, stubs в `wiremock/mappings/` и fault injection для проверки Circuit Breaker и повторных попыток.
* **Результат:** 100% повторяемость тестов без обращения к живым внешним API.

---

### 📌 DEC-013: Внедрение Ruff Linter и DeepEval для Quality Gates
* **Контекст:** Требовалось строгое статическое профилирование и AI-оценка сгенерированных тестов.
* **Решение:** Добавлены `ruff` (заменивший flake8/black) и `deepeval` (`DeepEvalBaseLLM`, `GEval`) в пайплайн Seam 3 и Seam 2.
* **Результат:** Молниеносная валидация синтаксиса и формализованная оценка тест-дизайна.

---

### 📌 DEC-014: OpenAPI 3.0 Contract Drift Protection
* **Контекст:** Несовпадение схемы Juice Shop и сгенерированных тестов приводит к скрытым дефектам.
* **Решение:** Реализован [`qaops/openapi_validator.py`](file:///d:/Desktop/Juice_shop/qa-automation/qaops/openapi_validator.py), извлекающий спецификацию из `/api-docs/swagger-ui-init.js` и кеширующий ее для верификации Pydantic контрактов.
* **Результат:** Автоматическая защита от дрейфа API контрактов.

---

### 📌 DEC-015: n8n Global Error Handler + Sentry MCP + Crash Monitor
* **Контекст:** Любой сбой внутри узлов n8n или падение фонового демона должны моментально приводить к оповещению команды.
* **Решение:**
  1. Создан и активирован workflow `Global QA Error Handler` (`pOfD3EHy9YcL4cza`), перехватывающий ошибки всех нод основного пайплайна.
  2. Настроен Sentry MCP сервер `https://mcp.sentry.dev/mcp/romeoworx`.
  3. Реализован `core_utils/crash_monitor.py` с глобальным `sys.excepthook`, отправляющий стек-трейс в Telegram при критических сбоях.
* **Результат:** Нулевая слепая зона при отказах.

---

### 📌 DEC-016: Архитектура Event Sourcing и Scheduled Events Outbox Engine
* **Контекст:** Для корпоративной масштабируемости и полной аудируемости пайплайна требовался переход от простого изменения статусов к Event Sourcing и очереди запланированных/повторных задач.
* **Решение:**
  1. Разработана схема PostgreSQL 16: [`qaops/sql/schema_postgres.sql`](file:///d:/Desktop/Juice_shop/qa-automation/qaops/sql/schema_postgres.sql).
  2. В [`qaops/store.py`](file:///d:/Desktop/Juice_shop/qa-automation/qaops/store.py) реализованы таблицы `qa_pipeline_events` (Append-Only Event Stream), `qa_pipeline_state` (проекция текущего состояния) и `qa_scheduled_events` (очередь с exponential backoff).
  3. Создан фоновый воркер [`scripts/scheduled_events_worker.py`](file:///d:/Desktop/Juice_shop/qa-automation/scripts/scheduled_events_worker.py).
  4. Все ключевые переходы в [`scripts/qa_agent_daemon.py`](file:///d:/Desktop/Juice_shop/qa-automation/scripts/qa_agent_daemon.py) фиксируются в Event Store.
* **Результат:** 100% аудит каждого шага, гарантированная доставка событий и надёжные повторы при сбоях.

---

### 📌 DEC-017: Комплексное оформление n8n стикерами и документацией на холсте
* **Контекст:** Для прозрачности демонстрации и работы любого члена команды требовалось снабдить каждый логический блок n8n исчерпывающими инструкциями, ссылками на БД, логи, спецификации и регламенты согласования.
* **Решение:**
  1. Разработаны 9 подробных стикеров (Sticky Notes) с цветовым кодированием для каждого этапа: от Webhook Gateway и DoR Gate до Allure-отчетности.
  2. В каждом блоке задокументированы: входящие/исходящие контракты, таблицы БД (`qa_pipeline_events`, `qa_pipeline_state`, `qaops_metrics`), лог-файлы, метрики Langfuse, и явные инструкции для QA Lead по согласованию (`ОК`).
  3. Воркфлоу обновлен и опубликован на сервере n8n (`Dv1WydaTMC1lxR0E`).
* **Результат:** Интуитивно понятный холст n8n, готовый к публичной демонстрации и командной работе.

---

### 📌 DEC-018: Архитектура PromptOps и централизованный реестр версионирования промптов
* **Контекст:** Жестко зашитые в Python-коде промпты затрудняли откат, тюнинг и адаптацию под другие компании/проекты.
* **Решение:**
  1. Создан модуль [`prompts/`](file:///d:/Desktop/Juice_shop/qa-automation/prompts/) с чистыми Markdown-шаблонами по доменам (`dor_evaluation`, `test_design_audit`, `code_review_audit`, `delta_refinement`).
  2. Реализована строгая иерархия версий (`v1.0_baseline.md` и `v2.0_enterprise.md`).
  3. Создан класс [`PromptRegistry`](file:///d:/Desktop/Juice_shop/qa-automation/prompts/registry.py) с поддержкой динамического рендеринга, безопасной подстановки переменных и мгновенного отката через переменные окружения (`PROMPT_VERSION_<DOMAIN>=v1.0_baseline`).
  4. Интегрирован во все аудиторы и проверен юнит-тестами.
* **Результат:** 100% разделение кода и промптов, версионирование уровня корпоративного PromptFlow.

---

### 📌 DEC-019: Корпоративная переносимость и конфигурационный шаблон (.env.example)
* **Контекст:** Требовалось сделать продукт готовым к установке в любое другое предприятие (Zero Vendor Lock-in).
* **Решение:**
  1. Создан всеобъемлющий файл [`.env.example`](file:///d:/Desktop/Juice_shop/qa-automation/.env.example) с подробным описанием каждого параметра (Jira, n8n, Telegram, Qase, Langfuse, Sentry, GitHub, DB, WireMock, Models).
  2. Разработано детальное руководство по корпоративному развертыванию [`docs/ENTERPRISE_DEPLOYMENT_AND_CREDS.md`](file:///d:/Desktop/Juice_shop/qa-automation/docs/ENTERPRISE_DEPLOYMENT_AND_CREDS.md).
* **Результат:** Любая новая организация может развернуть пайплайн за 4 простых шага.

---

### 📌 DEC-020: Санитария рабочей области IDE и архивация временных утилит
* **Контекст:** За время исследований в `scripts/tools/` и корне проекта накопилось более 130 временных отладочных скриптов и пустых файлов, что мешало презентации и захламляло навигацию.
* **Решение:**
  1. Удалены 0-байтные остаточные файлы `qaops.db` и `qa_pipeline.db` из корня (активная БД находится в `data/qa_pipeline.db`).
  2. Устаревший экспорт `n8n_live_workflow.json` перемещен в `n8n/backups/`.
  3. В `scripts/tools/` оставлены только 6 ключевых инструментов жизненного цикла, а 132 исследовательских скрипта аккуратно архивированы в `scripts/tools/legacy_audit/`.
* **Результат:** Кристально чистая структура проекта, готовая к онлайн-показу и код-ревью.

---

### 📌 DEC-021: SDET Pre-flight Readiness Probe & Infrastructure Health Gate
* **Контекст:** Запуск задачи в пайплайне при неактивном воркфлоу n8n, отключенном туннеле ngrok, упавшем SUT или неработающем демоне приводит к гарантированному падению задачи на середине выполнения.
* **Решение:**
  1. Разработан модуль [`qaops/health.py`](file:///d:/Desktop/Juice_shop/qa-automation/qaops/health.py) с глубокими проверками готовности (Readiness Probes) всех 10 компонентов: Juice Shop SUT, n8n активный воркфлоу, n8n Error Handler, ngrok туннель, Jira API, Telegram Bot, Qase TMS, Gemini LLM, SQLite Event Store, QA Daemon (с механизмом heartbeat).
  2. Создан выделенный набор pytest автотестов [`tests/health/test_system_health.py`](file:///d:/Desktop/Juice_shop/qa-automation/tests/health/test_system_health.py) (11 тестов со строгими SLA по задержкам и Allure аннотациями).
  3. В [`scripts/pipeline/task_lifecycle.py`](file:///d:/Desktop/Juice_shop/qa-automation/scripts/pipeline/task_lifecycle.py) внедрен пре-флайт гейт: задача физически не может быть переведена в статус «В работе», если хотя бы один критический сервис недоступен.
  4. Создан скрипт запуска в 1 клик [`run_health_check.bat`](file:///d:/Desktop/Juice_shop/qa-automation/run_health_check.bat).
* **Результат:** 100% защита от ложных стартов, мгновенная локализация сбоев за 4 секунды.

---

### 📌 DEC-022: n8n Stage 0 SDET Pre-Flight Gate & Премиальный UI/UX Редизайн Канваса
* **Контекст:** Пользователь запросил реализацию Варианта А (встраивание проверок здоровья непосредственно в n8n перед стартом пайплайна) с полной визуальной гармонизацией канваса n8n: устранение пересечений стикеров, ликвидация наплыва текста на ноды, соблюдение отступов (gutters), строгая последовательность UI/UX сценария и добавление кликабельных ссылок на все рабочие инструменты.
* **Решение:**
  1. **Stage 0 Pre-Flight Gate внутри n8n**: Внедрен новый защитный блок из 5 нод (`Stage 0: Проверка Jira Cloud API`, `Stage 0: Проверка Qase TMS API`, `Stage 0: Валидация готовности инфраструктуры`, `Условие: Инфраструктура готова к работе?`, `Telegram: 🚨 Отказ запуска — сбой инфраструктуры`). При сбое зависимостей n8n отправляет мгновенный алерт и завершает выполнение до расхода токенов LLM.
  2. **Математическая сетка канваса (UI/UX Grid)**:
     - Все 10 блоков размещены строго слева направо (X от -520 до 12780) с межблочным интервалом 160px (Gutters).
     - Вертикальная зона текста стикера (Y: -140..220, высота 360px) полностью отделена от зоны нод (Y: 380..580). Наплыв текста на ноды исключен на 100%.
     - Все 10 стикеров получили цветовую кодировку (Blue, Green, Purple, Red, Teal, Yellow) и единую архитектурную структуру (Цель, Вход, Ноды, Хранилище, Кликабельные ссылки `[текст](url)`, Инструкция для инженера).
  3. Воркфлоу синхронизирован и успешно опубликован на облачном инстансе n8n (`http://201.34.147.33:5678/workflow/Dv1WydaTMC1lxR0E`).
* **Результат:** Канвас n8n выглядит безупречно, профессионально и презентабельно; пайплайн защищен на уровне n8n и локального раннера.

---

### 📌 DEC-023: n8n Personal Workflows Consolidation, Credentials Suite, Variables Audit & Epic Tasks Reset
* **Контекст:** Пользователь запросил наведение абсолютного порядка в n8n (вкладки Personal, Credentials, Variables, Data Tables) и подготовку (обезличивание/сброс) задач JS-40, JS-41, JS-42 к новому сквозному тестовому прогону.
* **Решение:**
  1. **Personal Workflows**: Все 7 устаревших и вспомогательных воркфлоу аккуратно забэкаплены в `n8n/backups/` и удалены из инстанса. Логика Global Error Handler перенесена непосредственно внутрь основного воркфлоу `Juice Shop` (`Dv1WydaTMC1lxR0E`) в виде автономного форка `Error Trigger -> Format Error Card -> Telegram Alert`. Теперь в n8n активен **ровно 1 рабочий воркфлоу**.
  2. **Credentials Tab**: Добавлены нативные профили подключения для `Sentry Exception Monitoring` (`sentryIoApi`) и `Production PostgreSQL Database` (`postgres`), удален дубликат токена Qase. Зарегистрированы все 9 сервисов экосистемы.
  3. **Variables Audit**: Проведен аудит `/api/v1/variables`. Зафиксировано, что n8n Community возвращает HTTP 403 на данную вкладку (требует Enterprise лицензию). Применен общепринятый открытый паттерн: переменные прокинуты через `$env` и централизованы в корневом конфигурационном узле `Фильтр: Задача взята в работу`.
  4. **Data Tables**: Подтверждено наличие и схема 3 встроенных таблиц n8n (`QA Pipeline Tasks`, `QA Pipeline Stages`, `QA Test Cases`). Сформулировано архитектурное разделение: SQLite (локальный кэш), PostgreSQL (боевой бэкенд), n8n Data Tables (визуальное представление в UI).
  5. **Anonymization & Reset (JS-40, JS-41, JS-42)**: Разработан скрипт [`scripts/tools/reset_epic_tasks.py`](file:///d:/Desktop/Juice_shop/qa-automation/scripts/tools/reset_epic_tasks.py). Все 3 задачи переведены в статус `К выполнению` (10045), очищены от всех комментариев и робот-лейблов, локальный SQLite и n8n Data Tables подготовлены к новому циклу.
* **Результат:** Чистый инстанс n8n, 100% готовность к сквозному прогону с задачи JS-40.

---

### 📌 DEC-024: Stage 0 Full Multi-Service Readiness Gate & Error SQL Persistence
* **Контекст:** Пользователь указал, что проверки только Jira, Qase и Telegram в Stage 0 недостаточно — перед запуском должны валидироваться ВСЕ сервисы: Langfuse, базы данных SQL, модели Gemini, перехватчики, GitHub Actions. Также ошибки должны обязательно падать в SQL базу данных, а бот должен быть строго реальным `@QApower_bot`.
* **Решение:**
  1. **Stage 0 расширен до 7 комплексных диагностических проб**:
     - `Stage 0: Проверка Jira Cloud API` (Auth & Myself)
     - `Stage 0: Проверка Qase TMS API` (Project JS & Token)
     - `Stage 0: Проверка Telegram Bot (@QApower_bot)` (getMe)
     - `Stage 0: Проверка Langfuse Observability` (Health Endpoint)
     - `Stage 0: Проверка Google Gemini LLM` (Model gemini-flash-lite-latest & API Key)
     - `Stage 0: Проверка GitHub Actions CI/CD` (Repo Access)
     - `Stage 0: Проверка SQL Базы и Data Tables` (n8n Data Tables API)
     - `Stage 0: Валидация готовности ВСЕЙ инфраструктуры` (Master Code Evaluator с расчетом вердикта Go / No-Go).
  2. **Персистентность сбоев в SQL**: Создана таблица `QA Pipeline Errors` (ID: `eCPXK5QUBpIxYyEc`) в n8n Data Tables и `qa_pipeline_errors` в SQLite/Postgres. В Error Trap Fork добавлен узел `SQL: Запись сбоя в таблицу QA Pipeline Errors`.
  3. **Связка Error Trap**: В системных настройках воркфлоу параметр `settings.errorWorkflow` привязан к `Dv1WydaTMC1lxR0E` (self), гарантируя немедленный перехват любых падений узлов на уровне движка.

---

### 📌 DEC-025: Синхронизация двухконтурной архитектуры и русскоязычные стандарты обозначений
* **Контекст:** Пользователь выявил архитектурный рассинхрон: в Блоке 3 воркфлоу n8n использовался `LLM Judge` на базе Gemini, тогда как в коде планировался DeepEval, при этом результат работы нейросети в n8n не потреблялся последующей нодой. Также пользователь потребовал отказаться от непонятных англицизмов (*Tier 1 / Tier 2*, *Seams 1–6*) и сделать обозначения шагов и процессов доступными и понятными на русском языке.
* **Решение:**
  1. **Ликвидация рассинхрона между движками и этапами:**
     - Разграничены зоны ответственности: **Контур 1 (Облачная оркестрация в n8n)** выполняет входной экспресс-анализ пользовательской истории и валидацию INVEST; **Контур 2 (Локальный SDET в Python)** выполняет глубокий семантический аудит тест-кейсов в Qase TMS через **DeepEval G-Eval** (метрика обоснованности Groundedness $\ge$ 90%) перед генерацией кода тестов.
     - В n8n нода `Проверка задачи на готовность` обновлена: теперь она безопасно парсит и потребляет вердикт и оценку ноды `LLM Judge: Оценка готовности (DoR Gate)`. Итоговый балл DoR формируется интегрально (40% контрактные проверки + 60% вердикт AI-судьи) с единым корпоративным порогом **80%**.
  2. **Отказ от англицизмов и переход на доступную русскую терминологию:**
     - Вместо *Tier 1 / Tier 2* утверждены: **Контур 1 (Облачная оркестрация n8n)** и **Контур 2 (Локальный инженерный SDET-контур в Python)**.
     - Вместо термина *Seams (швы)* утверждены: **6 Контрольных точек обеспечения качества**:
       - *Контрольная точка 1:* Входной контроль требований задачи (DoR Gate & INVEST, порог 80%).
       - *Контрольная точка 2:* Семантический аудит тест-дизайна (DeepEval G-Eval, Groundedness $\ge$ 90%).
       - *Контрольная точка 3:* Статический аудит синтаксиса и сборки тестов (Ruff + AST-парсер).
       - *Контрольная точка 4:* Защита от дублей и сетевых сбоев (Идемпотентность и Outbox).
       - *Контрольная точка 5:* Экспертное согласование инженером (Human-in-the-Loop и Evidence Pack).
       - *Контрольная точка 6:* Сквозной мониторинг и трейсинг (Langfuse Cloud).
  3. **Обновление полотна n8n и документации:**
     - Все 11 стикеров на канвасе n8n переписаны на понятном русском языке без терминологического мусора и загружены в облако n8n (`http://201.34.147.33:5678`).
     - Создано подробное русскоязычное руководство в [`n8n/README.md`](file:///d:/Desktop/Juice_shop/qa-automation/n8n/README.md).
* **Результат:** 100% синхронизация данных между LLM Judge и решающими нодами, согласованность порогов и абсолютная прозрачность терминологии для всей команды.





