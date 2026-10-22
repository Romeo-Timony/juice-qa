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
| **DEC-007** | **Стандарт структуры репозитория и генеральная уборка**: чистый корень, каталоги `pipeline/`, `tools/`, `specs/`, `backups/`. | Clean Code | **High / Low** (профессиональный порядок в репозитории SDET) | **Реализовать** | `[✅ DONE]` | [`qa-automation/`](file:///d:/Desktop/Juice_shop/qa-automation/) |
| **DEC-008** | **Готовность к следующей задаче спринта (JS-41: Frontend UI)**: разработка Playwright UI тестов регистрации. | Automation | **High / Medium** (завершение эпика JS-39) | **В работе** | `[🚀 NOW]` | Jira: `JS-41` |

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
