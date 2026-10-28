"""Updates n8n main workflow with comprehensive enterprise sticky notes and uploads via API."""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKFLOW_FILE = BASE_DIR / "n8n" / "current_main_workflow.json"

STICKY_CONFIGS = [
    {
        "name": "Стикер: Приём задач",
        "position": [-380, -60],
        "width": 520,
        "height": 720,
        "color": 6,
        "content": (
            "## 📥 Блок 1: Приём задач и Webhook Gateway\n\n"
            "**📌 Ноды в блоке:**\n"
            "• `Jira: Перехват обновления задачи` (Webhook)\n"
            "• `Execute Workflow Trigger` (Прямой вызов)\n"
            "• `Фильтр: Задача взята в работу` (Code)\n\n"
            "**⚙️ Что здесь происходит:**\n"
            "Мгновенный перехват webhook-событий Jira Cloud при переходе задачи в статус «В работе» (10046) "
            "или добавлении комментариев. Выделяет ключ задачи (issue_key) и correlation_id.\n\n"
            "**🔌 Контракты и источники:**\n"
            "• Jira Webhook: `/webhook/jira-webhook` через ngrok-туннель\n"
            "• Payload: `issue.key`, `issue.fields.summary`, `changelog.items[]`\n\n"
            "**💾 База данных и события:**\n"
            "• Таблица: `qa_pipeline_events` (событие `PIPELINE_STARTED`)\n"
            "• Таблица: `qaops_idempotency` (дедупликация повторных событий)\n"
            "• Таблица: `qa_pipeline_state` (проекция: stage=1 `DoR Gate`)\n\n"
            "**🔍 Логи и диагностика:**\n"
            "• Файл логов: `qa-automation/logs/qa_agent.log`\n"
            "• n8n Executions: `http://201.34.147.33:5678/executions`\n\n"
            "**💡 Инструкция для команды:**\n"
            "Для старта пайплайна переведите тикет в Jira в статус **«В работе»**."
        ),
    },
    {
        "name": "Стикер: Проверка готовности (DoR)",
        "position": [160, 40],
        "width": 1820,
        "height": 550,
        "color": 4,
        "content": (
            "## 📋 Блок 2: DoR Gate & AI Анализ Требований [Этап 1]\n\n"
            "**📌 Ноды в блоке:**\n"
            "• `Jira: Загрузить данные задачи` & `Jira: Загрузить ссылки задачи` (HTTP Request)\n"
            "• `Правила проверки готовности задачи` & `Подготовка задачи к проверке` (Code)\n"
            "• `LLM Judge: Оценка готовности (DoR Gate)` & `Gemini Model: DoR Judge` (LangChain)\n"
            "• `Проверка задачи на готовность` & `Условие: Требования задачи понятны?` (Code / If)\n"
            "• `Jira: Отчет 1 — Задача готова к работе (DoR Gate)` (HTTP Request)\n"
            "• `Langfuse: Фиксация трейса и метрик` (HTTP Request)\n\n"
            "**⚙️ Что здесь происходит:**\n"
            "Загрузка тикета и Confluence-спецификации. Многофакторный AI-аудит требований по INVEST "
            "(Independent, Negotiable, Valuable, Estimable, Small, Testable) и проверка контрактов API (C06 - поведение при ошибках). "
            "При успехе публикуется Отчет №1 в Jira и фиксируется трейс.\n\n"
            "**🔌 Контракты и источники:**\n"
            "• Jira REST API: `GET /rest/api/2/issue/{key}`, Confluence: `GET /wiki/rest/api/content`\n"
            "• Prompt: `prompts/dor_evaluation/v2.0_enterprise.md`\n\n"
            "**💾 База данных и события:**\n"
            "• `qa_pipeline_events`: `DOR_EVALUATED` (score, blockers, summary)\n"
            "• `qaops_metrics`: `INVEST_Compliance` (порог >= 80%)\n"
            "• `qaops_spans`: распределенный трейс `llm.gemini.dor`\n\n"
            "**🔍 Логи и трейсинг:**\n"
            "• Langfuse: `https://cloud.langfuse.com` (фильтр по `issue_key`)\n"
            "• Результат: балл >= 80% -> переход к Блоку 4; < 80% -> переход к Блоку 3 (Возврат)."
        ),
    },
    {
        "name": "Стикер: Возврат задачи",
        "position": [660, 650],
        "width": 1180,
        "height": 620,
        "color": 3,
        "content": (
            "## ❌ Блок 3: Эскалация и возврат задачи при DoR Fail\n\n"
            "**📌 Ноды в блоке:**\n"
            "• `Jira: Отправить замечания к задаче` (HTTP Request)\n"
            "• `Условие: Пауза из-за контракта или возврат?` (If)\n"
            "• `Jira: Поставить метку qa-paused` & `Jira: Вернуть задачу на доработку` (HTTP Request)\n"
            "• `Jira: Поставить метку Требует доработки` (HTTP Request)\n"
            "• `Telegram: Алерт об отклонении DoR` (Telegram)\n\n"
            "**⚙️ Что здесь происходит:**\n"
            "Если критерии приемки размыты или отсутствует контракт ошибок — задача блокируется. "
            "В Jira публикуется детальный список замечаний, тикет переводится в статус «К выполнению» (ID: 11) "
            "с меткой `qa-paused`, а в Telegram уходит алерт с баллами и списком блокеров.\n\n"
            "**🔌 Контракты и интеграции:**\n"
            "• Jira API: `POST /rest/api/2/issue/{key}/transitions`, `POST /rest/api/2/issue/{key}/comment`\n"
            "• Telegram Bot API: канал оповещения команды QA\n\n"
            "**💾 База данных и состояние:**\n"
            "• `qa_pipeline_events`: `DOR_REJECTED`\n"
            "• `qa_pipeline_state`: `hitl_gate1_status = 'REJECTED'`\n\n"
            "**💡 Инструкция по разблокировке (Human Override):**\n"
            "Аналитик дополняет задачу, ЛИБО QA Lead переопределяет решение: "
            "отправляет комментарий **`ОК`** (строго большими буквами) в задачу в Jira. "
            "Демон `qa_agent_daemon.py` выполнит DoR Override и возобновит пайплайн."
        ),
    },
    {
        "name": "Стикер: Интеллект-карта проверок",
        "position": [2030, -50],
        "width": 900,
        "height": 450,
        "color": 4,
        "content": (
            "## 🧠 Блок 4: Интеллект-карта проверок [Этап 2]\n\n"
            "**📌 Ноды в блоке:**\n"
            "• `Подготовка данных для чек-листа` & `Создание карты проверок` (Code)\n"
            "• `Whimsical: Генерация MindMap` (Code)\n"
            "• `Jira: Отчет 2 — Интеллект-карта проверок` (HTTP Request)\n\n"
            "**⚙️ Что здесь происходит:**\n"
            "Системная декомпозиция требований на слои тест-дизайна: Happy Path, негативные сценарии, "
            "граничные значения, роли безопасности (Admin, Customer, Guest) и проверка API-контрактов. "
            "Формирует интерактивную ментальную карту проверок и публикует Отчет №2 в Jira.\n\n"
            "**🔌 Контракты и модели:**\n"
            "• Контракты Pydantic: `schemas/contracts.py`, `schemas/models.py`\n"
            "• OpenAPI 3.0 спецификация Juice Shop: `/api-docs/swagger-ui-init.js`\n\n"
            "**💾 База данных и телеметрия:**\n"
            "• `qa_pipeline_events`: `MINDMAP_GENERATED`\n"
            "• `qaops_spans`: span `design.mindmap`\n\n"
            "**💡 Инструкция для команды:**\n"
            "Проверьте Отчет №2 в тикете перед переходом к согласованию тест-кейсов."
        ),
    },
    {
        "name": "Стикер: Тест-кейсы и RTM",
        "position": [2050, 520],
        "width": 1600,
        "height": 780,
        "color": 5,
        "content": (
            "## 🧪 Блок 5: Qase TMS Синхронизация & BDD Тест-дизайн [Этапы 3 и 4]\n\n"
            "**📌 Ноды в блоке:**\n"
            "• `Подготовка данных для тест-кейсов` & `Создание тест-кейсов без повторов` (Code)\n"
            "• `Qase: Загрузить список папок` & `Qase: Загрузить существующие тесты` (HTTP Request)\n"
            "• `LLM Judge: Аудит тест-дизайна (Design Gate)` & `Gemini Model: Design Gate Judge` (LangChain)\n"
            "• `Условие: Есть новые тесты для добавления?` & `Qase: Создать новые тесты в базе` (If / HTTP)\n"
            "• `Jira: Отчет 3 — Реестр тест-кейсов (BDD)` & `Jira: Отчет 4 — Матрица RTM` (HTTP Request)\n"
            "• `Jira: Прикрепить ссылку на тесты в Qase` (HTTP Request)\n\n"
            "**⚙️ Что здесь происходит:**\n"
            "1. Загрузка тест-кейсов из Qase TMS (проект `JS`).\n"
            "2. Семантическая дедупликация (исключает создание тестов-дубликатов).\n"
            "3. Экспорт новых BDD-кейсов в Qase TMS.\n"
            "4. AI-аудит качества тест-дизайна (Test Design Integrity >= 90%).\n"
            "5. Формирование матрицы прослеживаемости требований (RTM) и публикация Отчетов №3 и №4 в Jira.\n\n"
            "**🔌 Контракты и источники:**\n"
            "• Qase REST API: `https://api.qase.io/v1/case/{project}`, `suite/{project}`\n"
            "• Prompt: `prompts/test_design_audit/v2.0_enterprise.md`\n\n"
            "**💾 База данных и метрики:**\n"
            "• `qa_pipeline_events`: `TEST_CASES_SYNCED`\n"
            "• `qaops_metrics`: `Test_Design_Integrity` (порог >= 90%)\n\n"
            "**🔍 Где смотреть результат:**\n"
            "• Qase TMS Suite: `https://app.qase.io/project/JS`\n"
            "• Jira: Отчет 3 (список тест-кейсов) и Отчет 4 (матрица RTM: AC <-> QASE_ID)."
        ),
    },
    {
        "name": "Стикер: Контроль 1",
        "position": [3860, 40],
        "width": 710,
        "height": 500,
        "color": 7,
        "content": (
            "## 🛡️ Блок 6: Quality Gate 1 (Human-in-the-Loop Согласование) [Этап 5]\n\n"
            "**📌 Ноды в блоке:**\n"
            "• `Контроль 1: Подтверждение тест-кейсов` (Code)\n"
            "• `Jira: Карточка подтверждения тестов (Gate 1)` (HTTP Request)\n"
            "• `Telegram: Оповещение об успешном DoR` (Telegram)\n"
            "• `Ожидание согласования тест-дизайна (Gate 1 Wait)` (Wait Node)\n\n"
            "**⚙️ Что здесь происходит:**\n"
            "Публикация официальной карточки согласования Gate 1 в Jira со статусом `⏳ ОЖИДАЕТ СОГЛАСОВАНИЯ QA LEAD`. "
            "Отправка алерта в Telegram с количеством тестов и ссылкой на задачу. "
            "Воркфлоу n8n ставится на управляемую паузу (`Wait node`).\n\n"
            "**💾 База данных и состояние:**\n"
            "• `qa_pipeline_events`: `GATE1_WAITING`\n"
            "• `qa_pipeline_state`: `hitl_gate1_status = 'WAITING'`\n\n"
            "**💡 Действие для согласования (Инструкция QA Lead):**\n"
            "1. Ознакомьтесь с отчетами 1–4 в тикете Jira.\n"
            "2. Для согласования отправьте в комментарии тикета: **`ОК`** (строго верхний регистр).\n"
            "3. Демон `qa_agent_daemon.py` перехватит `ОК`, обновит карточку на `(/) ОДОБРЕНО`, "
            "разбудит execution в n8n и запустит разработку автотестов."
        ),
    },
    {
        "name": "Стикер: Gate 2 и Внедрение",
        "position": [4340, 40],
        "width": 970,
        "height": 550,
        "color": 2,
        "content": (
            "## ⚙️ Блок 7: Генерация кода, Ruff Gate & Quality Gate 2 [Этапы 6 и 7]\n\n"
            "**📌 Ноды в блоке:**\n"
            "• `Jira: Карточка проверки кода (Gate 2)` (HTTP Request)\n"
            "• `Telegram: Запрос согласования кода (Gate 2)` (Telegram)\n"
            "• `Ожидание согласования кода (Gate 2 Wait)` (Wait Node)\n"
            "• `Jira: Отчет 7 — Внедрение автотестов в проект` (HTTP Request)\n\n"
            "**⚙️ Что здесь происходит:**\n"
            "1. Демон генерирует код автотестов (`scaffold_dynamic.py`) в staging-папку `tests/review/`.\n"
            "2. Seam 3 Code Gate: AST-парсинг, линтер `ruff check --select E9,F63,F7,F82`, сухой сбор `pytest --collect-only`.\n"
            "3. AI-аудит чистоты и безопасности кода (`prompts/code_review_audit/v2.0_enterprise.md`).\n"
            "4. Публикуется карточка Gate 2 с Evidence Pack в Jira и уходит запрос согласования в Telegram.\n"
            "5. Пауза до подтверждения QA Lead.\n\n"
            "**💾 База данных и контроль:**\n"
            "• `qa_pipeline_events`: `GATE2_WAITING`, `GATE2_APPROVED`\n"
            "• `qa_pipeline_state`: `hitl_gate2_status = 'APPROVED'`\n"
            "• `qaops_idempotency`: хеш файлов для защиты от повторного push\n\n"
            "**💡 Инструкция QA Lead:**\n"
            "Отправьте комментарий **`ОК`** в Jira. Демон перенесет файлы в боевой каталог (`tests/backend` / `tests/frontend`), "
            "запушит ветку `qa/js-XX` в репозиторий, опубликует Отчет №7 и запустит CI/CD."
        ),
    },
    {
        "name": "Стикер: GitHub Actions Trigger",
        "position": [5250, 40],
        "width": 400,
        "height": 500,
        "color": 1,
        "content": (
            "## 🐙 Блок 8: GitHub Actions CI/CD Trigger\n\n"
            "**📌 Ноды в блоке:**\n"
            "• `GitHub: Запуск автотестов в CI/CD` (GitHub API)\n"
            "• `Telegram: Оповещение о старте CI/CD` (Telegram)\n\n"
            "**⚙️ Что здесь происходит:**\n"
            "Нативный вызов GitHub Actions REST API (`workflow_dispatch`) репозитория `Romeo-Timony/juice-qa`. "
            "Запускает workflow `autotests.yml` для целевой ветки задачи и уведомляет команду в Telegram.\n\n"
            "**🔌 Контракты и аутентификация:**\n"
            "• GitHub API: `POST /repos/Romeo-Timony/juice-qa/actions/workflows/autotests.yml/dispatches`\n"
            "• Параметры: `ref: main`, `inputs.issue_key: JS-XX`\n"
            "• GitHub Personal Access Token с правами `repo` и `workflow`\n\n"
            "**💾 База данных и аудит:**\n"
            "• `qa_pipeline_events`: `CI_PIPELINE_DISPATCHED`\n"
            "• `qa_scheduled_events`: задание контроля таймаута раннера\n\n"
            "**🔍 Мониторинг CI:**\n"
            "• `https://github.com/Romeo-Timony/juice-qa/actions`"
        ),
    },
    {
        "name": "Стикер: GitHub Actions Результаты",
        "position": [5650, 40],
        "width": 1000,
        "height": 550,
        "color": 6,
        "content": (
            "## 📊 Блок 9: Результаты CI/CD & Allure Отчетность [Этап 8]\n\n"
            "**📌 Ноды в блоке:**\n"
            "• `Webhook: Прием отчетов GitHub Actions` (Webhook)\n"
            "• `Ожидание завершения CI/CD и отчета Allure` (Wait Node)\n"
            "• `Парсинг отчета Allure` (Set)\n"
            "• `Jira: Опубликовать отчет Allure` (HTTP Request)\n"
            "• `Telegram: Отчет Allure из CI/CD` (Telegram)\n\n"
            "**⚙️ Что здесь происходит:**\n"
            "1. Прием webhook с результатами тестирования от GitHub Actions runner.\n"
            "2. Парсинг метрик Allure (Passed, Failed, Broken, Skipped, Execution Time).\n"
            "3. Расчет Release Quality Index (RQI) и формирование решения Go/No-Go.\n"
            "4. Публикация финального Отчета №8 в Jira и перевод задачи в «Автотесты пройдены» (10048).\n"
            "5. Отправка итогового отчета Allure со ссылками в Telegram-канал команды.\n\n"
            "**🔌 Контракты и вебхуки:**\n"
            "• Webhook: `/webhook/github-actions-report`\n"
            "• Allure Parser: `qaops/observability.py:parse_allure_summary`\n\n"
            "**💾 База данных и Go/No-Go:**\n"
            "• `qa_pipeline_events`: `PIPELINE_COMPLETED`\n"
            "• `qa_pipeline_state`: `stage = 6 (Completed)`, `rqi_score`\n"
            "• `qaops_metrics`: решение Go / No-Go (порог RQI >= 80%)\n\n"
            "**🎉 Результат:** Полный сквозной цикл тестирования задачи завершен!"
        ),
    },
]


def update_workflow():
    if not WORKFLOW_FILE.exists():
        raise FileNotFoundError(f"{WORKFLOW_FILE} does not exist")

    with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])

    # Remove existing sticky notes
    non_sticky_nodes = [n for n in nodes if n.get("type") != "n8n-nodes-base.stickyNote"]

    # Build new sticky notes
    import uuid
    new_stickies = []
    for cfg in STICKY_CONFIGS:
        sticky_node = {
            "parameters": {
                "content": cfg["content"],
                "height": cfg["height"],
                "width": cfg["width"],
                "color": cfg.get("color", 4),
            },
            "id": uuid.uuid4().hex[:16],
            "name": cfg["name"],
            "type": "n8n-nodes-base.stickyNote",
            "typeVersion": 1,
            "position": cfg["position"],
        }
        new_stickies.append(sticky_node)

    data["nodes"] = non_sticky_nodes + new_stickies

    # Save locally
    with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Updated local workflow: {len(data['nodes'])} total nodes ({len(new_stickies)} sticky notes)")

    # Upload to n8n API
    url = (os.getenv("N8N_URL") or os.getenv("N8N_SERVER_URL") or "http://201.34.147.33:5678").rstrip("/")
    key = os.getenv("N8N_API_KEY")

    workflow_id = "Dv1WydaTMC1lxR0E"
    put_payload = {
        "name": data.get("name", "Juice Shop"),
        "nodes": data["nodes"],
        "connections": data.get("connections", {}),
        "settings": data.get("settings", {}),
    }

    res = requests.put(
        f"{url}/api/v1/workflows/{workflow_id}",
        headers={"X-N8N-API-KEY": key, "Content-Type": "application/json"},
        json=put_payload,
        timeout=30,
    )

    if res.status_code == 200:
        print(f"✅ Successfully updated and published n8n workflow {workflow_id} on {url}!")
    else:
        print(f"❌ Failed to upload workflow: {res.status_code} - {res.text[:500]}")


if __name__ == "__main__":
    update_workflow()
