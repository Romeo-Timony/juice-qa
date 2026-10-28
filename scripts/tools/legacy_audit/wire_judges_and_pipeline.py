import os
import requests
import json
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')
n8n_url = os.getenv('N8N_URL')
api_key = os.getenv('N8N_API_KEY')
headers = {'X-N8N-API-KEY': api_key}

r = requests.get(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', headers=headers)
wf = r.json()

nodes = wf['nodes']
connections = wf['connections']

# 1. Update Gemini Model parameters to user's verified model
for n in nodes:
    if 'Gemini Model' in n['name']:
        n['parameters'] = {
            "modelName": "models/gemini-flash-latest",
            "options": {
                "temperature": 0.2
            }
        }
        print(f"Verified & updated {n['name']} modelName to models/gemini-flash-latest")

# 2. Configure Prompts for LLM Judges
dor_prompt = """Ты — ведущий QA-архитектор (SDET Lead) проекта OWASP Juice Shop.
Проведи строгий независимый аудит Definition of Ready (DoR Gate) для пользовательской истории.

Входные данные задачи:
- Ключ: {{ $('Подготовка задачи к проверке').item.json.issueKey }}
- Название: {{ $('Подготовка задачи к проверке').item.json.summary }}
- Описание: {{ $('Подготовка задачи к проверке').item.json.description }}
- Критерии приемки (AC): {{ $('Подготовка задачи к проверке').item.json.ac || 'Не указаны явно' }}
- Спецификация Confluence: {{ $('Подготовка задачи к проверке').item.json.confluenceSpec || 'Не прикреплена' }}

Проверь требования по 4 критериям DoR:
1. Наличие и однозначность критериев приемки (Acceptance Criteria).
2. Тестопригодность (Testability) — понятен ли способ проверки на уровне API или UI.
3. Описание контракта данных (DTO, эндпоинты, параметры, статус-коды).
4. Отсутствие двусмысленностей и блокирующих внешних зависимостей.

Верни строго JSON объект следующей структуры:
{
  "verdict": "APPROVED" или "REJECTED",
  "score": <число от 0 до 100>,
  "dorPassed": true или false,
  "summary": "<краткий вердикт на русском языке>",
  "missingCriteria": ["<список пунктов, которых не хватает для взятия в работу>"],
  "actionItems": ["<конкретные шаги для аналитика по доработке>"]
}"""

design_prompt = """Ты — Staff SDET проекта OWASP Juice Shop.
Проведи технический аудит тест-дизайна (Design Gate) перед загрузкой в Qase TMS.

Сгенерированные тест-кейсы:
{{ JSON.stringify($('Создание тест-кейсов без повторов').item.json.qaseCases || $('Создание тест-кейсов без повторов').item.json) }}

Критерии Design Gate:
1. Покрытие: позитивные (Happy Path), негативные сценарии и граничные значения для всех AC.
2. BDD структура: строгий формат Given-When-Then с проверяемыми ожидаемыми результатами.
3. Отсутствие галлюцинаций: проверка реальных эндпоинтов REST API или компонентов Angular UI.
4. Атомарность: каждый тест изолирован и проверяет ровно одно утверждение.

Верни строго JSON объект:
{
  "verdict": "PASS" или "FAIL",
  "coverageScore": <число от 0 до 100>,
  "feedback": "<детальный отзыв по качеству тест-дизайна>",
  "approvedCount": <количество одобренных тестов>
}"""

for n in nodes:
    if n['name'] == 'LLM Judge: Оценка готовности (DoR Gate)':
        n['parameters'] = {"prompt": f"={dor_prompt}"}
        n['position'] = [1344, 272]
        print("Configured DoR Judge Prompt and Position!")
    elif n['name'] == 'Gemini Model: DoR Judge':
        n['position'] = [1344, 460]
    elif n['name'] == 'LLM Judge: Аудит тест-дизайна (Design Gate)':
        n['parameters'] = {"prompt": f"={design_prompt}"}
        n['position'] = [2880, 816]
        print("Configured Design Gate Judge Prompt and Position!")
    elif n['name'] == 'Gemini Model: Design Gate Judge':
        n['position'] = [2880, 1020]

# 3. Add Wait node between Stage 7 and Stage 8
wait_node = next((n for n in nodes if n['name'] == 'Ожидание завершения CI/CD и отчета Allure'), None)
if not wait_node:
    wait_node = {
        "parameters": {
            "resume": "webhook",
            "webhookPath": "ci-report-wait"
        },
        "id": "wait-for-allure-report",
        "name": "Ожидание завершения CI/CD и отчета Allure",
        "type": "n8n-nodes-base.wait",
        "typeVersion": 1.1,
        "position": [5100, 192],
        "notes": "⏳ Приостанавливает выполнение воркфлоу до получения вебхука от GitHub Actions runner с результатами Allure (сквозная связь Этапа 7 и 8)."
    }
    nodes.append(wait_node)
    print("Added Wait node linking Stage 7 to Stage 8!")

# 4. Add Jira notification node for Qase Drift to 'friend' it with the project
qase_drift_jira = next((n for n in nodes if n['name'] == 'Jira: Регистрация дрифта в задаче'), None)
if not qase_drift_jira:
    qase_drift_jira = {
        "parameters": {
            "method": "POST",
            "url": "https://romeo-timony.atlassian.net/rest/api/2/issue/JS-40/comment",
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "jiraSoftwareCloudApi",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({\n  body: 'h3. ⚠️ Внимание: Зафиксирован дрифт в Qase TMS\\n\\n' +\n        '*Событие:* ' + $json.event + '\\n' +\n        '*Тест-кейс:* #' + $json.caseId + ' — ' + $json.caseTitle + '\\n' +\n        '*Критичность:* ' + $json.driftSeverity + '\\n\\n' +\n        '{color:red}Репозиторий автотестов требует синхронизации маркерного покрытия.{color}'\n}) }}",
            "options": {}
        },
        "credentials": {
            "jiraSoftwareCloudApi": {
                "id": "xnrgpIhThDJMtfMb",
                "name": "Jira Credentials"
            }
        },
        "id": "jira-qase-drift-log",
        "name": "Jira: Регистрация дрифта в задаче",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [1080, -220],
        "notes": "📝 Публикует предупреждение о рассинхронизации тестов в активный тикет Jira при удалении кейса в Qase TMS."
    }
    nodes.append(qase_drift_jira)
    print("Added Jira Qase Drift registration node!")

# 5. Wire connections cleanly
# Main flow:
# Подготовка задачи к проверке -> LLM Judge: Оценка готовности (DoR Gate) -> Проверка задачи на готовность -> Условие: Требования задачи понятны?
connections['Подготовка задачи к проверке'] = {
    'main': [[{'node': 'LLM Judge: Оценка готовности (DoR Gate)', 'type': 'main', 'index': 0}]]
}
connections['LLM Judge: Оценка готовности (DoR Gate)'] = {
    'main': [[{'node': 'Проверка задачи на готовность', 'type': 'main', 'index': 0}]]
}
connections['Gemini Model: DoR Judge'] = {
    'ai_languageModel': [[{'node': 'LLM Judge: Оценка готовности (DoR Gate)', 'type': 'ai_languageModel', 'index': 0}]]
}

# Design Gate:
# Создание тест-кейсов без повторов -> LLM Judge: Аудит тест-дизайна (Design Gate) -> Jira: Отчет 3 — Реестр тест-кейсов (BDD)
connections['Создание тест-кейсов без повторов'] = {
    'main': [[{'node': 'LLM Judge: Аудит тест-дизайна (Design Gate)', 'type': 'main', 'index': 0}]]
}
connections['LLM Judge: Аудит тест-дизайна (Design Gate)'] = {
    'main': [[{'node': 'Jira: Отчет 3 — Реестр тест-кейсов (BDD)', 'type': 'main', 'index': 0}]]
}
connections['Gemini Model: Design Gate Judge'] = {
    'ai_languageModel': [[{'node': 'LLM Judge: Аудит тест-дизайна (Design Gate)', 'type': 'ai_languageModel', 'index': 0}]]
}

# Stage 7 to Stage 8 linkage:
# Telegram: Оповещение о старте CI/CD -> Ожидание завершения CI/CD и отчета Allure -> Парсинг отчета Allure
connections['Telegram: Оповещение о старте CI/CD'] = {
    'main': [[{'node': 'Ожидание завершения CI/CD и отчета Allure', 'type': 'main', 'index': 0}]]
}
connections['Ожидание завершения CI/CD и отчета Allure'] = {
    'main': [[{'node': 'Парсинг отчета Allure', 'type': 'main', 'index': 0}]]
}

# Qase Drift linkage:
# Webhook: События Qase TMS -> Анализ рассинхрона Qase (Drift Detector) -> Telegram: Алерт о рассинхронизации Qase (Drift) -> Jira: Регистрация дрифта в задаче
connections['Telegram: Алерт о рассинхронизации Qase (Drift)'] = {
    'main': [[{'node': 'Jira: Регистрация дрифта в задаче', 'type': 'main', 'index': 0}]]
}

# Update positions of Stage 8 nodes for visual alignment with Wait node:
for n in nodes:
    if n['name'] == 'Парсинг отчета Allure':
        n['position'] = [5350, 192]
    elif n['name'] == 'Jira: Опубликовать отчет Allure':
        n['position'] = [5600, 192]
    elif n['name'] == 'Telegram: Отчет Allure из CI/CD':
        n['position'] = [5850, 192]

# Save updated workflow to n8n
wf_update = {
    'name': wf['name'],
    'nodes': nodes,
    'connections': connections,
    'settings': wf.get('settings', {})
}

up_r = requests.put(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', json=wf_update, headers=headers)
print('Workflow update status:', up_r.status_code)
if up_r.status_code == 200:
    print('All connections, prompts, and linkages successfully wired in n8n!')
else:
    print('Error updating workflow:', up_r.text[:500])
