# 🏢 Руководство по корпоративному развертыванию и настройке учетных данных (Enterprise Deployment Guide)

Данный документ описывает процесс переноса и запуска платформы **Autonomous QAOps & Self-Healing Testing Agent** на инфраструктуре любой компании или предприятия без привязки к конкретному аккаунту (Zero Vendor Lock-in).

---

## 🏗️ 1. Архитектурные компоненты платформы

Платформа состоит из 4 ключевых слабосвязанных слоев:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. ВНЕШНИЕ СЕРВИСЫ УПРАВЛЕНИЯ & ТЕЛЕМЕТРИИ                                 │
│    Jira Cloud / Qase TMS / Telegram / Confluence / GitHub Actions / Sentry  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Webhooks & REST API
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 2. ОРКЕСТРАЦИЯ И ГРАФ СОБЫТИЙ (n8n Self-Hosted)                            │
│    - 9 функциональных блоков с подробными стикерами-инструкциями            │
│    - Global Error Handler (перехват сбоев нод в Telegram)                   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Execution Resumption & Event Store
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 3. АВТОНОМНЫЙ QA АГЕНТ-ДЕМОН (Python 3.12 Engine)                          │
│    - scripts/qa_agent_daemon.py: управление жизненным циклом и гейтами     │
│    - scripts/scheduled_events_worker.py: очередь задач и бэкофф-повторы     │
│    - core_utils/crash_monitor.py: глобальный перехват падений (sys.hook)   │
│    - prompts/registry.py: движок версионирования промптов (PromptOps)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Dual-Engine Persistence
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 4. ХРАНИЛИЩЕ ДАННЫХ И ШЛЮЗ ТЕСТИРОВАНИЯ                                     │
│    - Event Sourcing Store: SQLite WAL (локально) / PostgreSQL 16 (прод)     │
│    - WireMock Standalone: изоляция внешних API и Fault Injection            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 2. Пошаговая инициализация для нового предприятия

### Шаг 1: Клонирование и виртуальное окружение
```bash
git clone https://github.com/your-org/qa-automation.git
cd qa-automation
python -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Шаг 2: Настройка учетных данных (.env)
Скопируйте шаблон `.env.example` в `.env`:
```bash
cp .env.example .env
```
Заполните обязательные переменные:
1. **Jira Cloud:** `ATLASSIAN_BASE_URL`, `ATLASSIAN_USER_EMAIL`, `ATLASSIAN_API_TOKEN`, `JIRA_PROJECT_KEY`.
2. **Telegram Bot:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
3. **Qase TMS:** `QASE_API_TOKEN`, `QASE_PROJECT_CODE`.
4. **LLM Provider:** `GEMINI_API_KEY` (или `OPENAI_API_KEY`).
5. **n8n Orchestrator:** `N8N_URL`, `N8N_API_KEY`.
6. **GitHub Actions:** `GITHUB_TOKEN`, `GITHUB_REPOSITORY`.

### Шаг 3: Импорт воркфлоу в инстанс n8n предприятия
1. В интерфейсе n8n перейдите в **Workflows** -> **Import from File**.
2. Выберите файл [`n8n/current_main_workflow.json`](file:///d:/Desktop/Juice_shop/qa-automation/n8n/current_main_workflow.json).
3. В нодах с учетными записями выберите сохраненные Credentials вашего инстанса (Jira Account, Gemini Account, Telegram Bot).
4. Активируйте глобальный обработчик ошибок:
   ```bash
   python scripts/tools/setup_n8n_error_workflow.py
   ```

### Шаг 4: Настройка Jira Cloud Webhook
В Jira перейдите в **Settings -> System -> WebHooks -> Create a Webhook**:
- **URL:** `https://your-domain/webhook/jira-webhook`
- **Events:**
  - Issue: `updated`, `created`
  - Issue related: `comment_created`
- **JQL Filter:** `project = "ВАШ_ПРОЕКТ"`

---

## 🗄️ 3. База данных: SQLite WAL vs PostgreSQL 16

| Критерий | SQLite WAL (По умолчанию) | PostgreSQL 16 (Enterprise Cluster) |
| :--- | :--- | :--- |
| **Применение** | Локальная разработка, PoC, Demo, Staging | Корпоративный production, High Availability |
| **Настройка** | Нулевая (автоматически создается в `data/qa_pipeline.db`) | Накатить [`qaops/sql/schema_postgres.sql`](file:///d:/Desktop/Juice_shop/qa-automation/qaops/sql/schema_postgres.sql) |
| **Конфигурация** | По умолчанию | В `.env`: `DATABASE_URL=postgresql://...` |
| **Режим блокировок**| WAL (Write-Ahead-Logging), безопасен для тредов | Row-level MVCC, распределенные транзакции |

---

## 🔄 4. Управление версиями промптов (PromptOps)

Любой домен промптов (DoR, аудит тест-дизайна, код-ревью, дельта-требования) версионируется в папке [`prompts/`](file:///d:/Desktop/Juice_shop/qa-automation/prompts/):
- Для отката на базовую версию укажите в `.env`:
  ```bash
  PROMPT_VERSION_DOR_EVALUATION=v1.0_baseline
  ```
- Для создания кастомного промпта предприятия создайте файл `prompts/dor_evaluation/v2.1_mycompany.md` и переключите переменную окружения.

---

## 🚀 5. Запуск сервисов и проверка работоспособности

### 1. Проверка здоровья окружения
```bash
python scripts/tools/check_environment_health.py
```

### 2. Запуск фонового демона агента
```bash
python scripts/qa_agent_daemon.py
```

### 3. Запуск воркера очереди запланированных событий
```bash
python scripts/scheduled_events_worker.py --interval 15
```

### 4. Запуск сквозного прогона автотестов
```bash
pytest tests/unit tests/qaops -v
```
Все 55+ тестов выполняются в изолированном режиме с поддержкой WireMock без необходимости обращения к живым сторонним сервисам.
