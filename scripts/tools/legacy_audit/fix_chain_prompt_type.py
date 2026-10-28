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
        n['parameters'] = {
            "promptType": "define",
            "text": f"={dor_prompt}"
        }
        print("Updated DoR Judge with promptType: define")
    elif n['name'] == 'LLM Judge: Аудит тест-дизайна (Design Gate)':
        n['parameters'] = {
            "promptType": "define",
            "text": f"={design_prompt}"
        }
        print("Updated Design Gate Judge with promptType: define")

wf_update = {
    'name': wf['name'],
    'nodes': nodes,
    'connections': wf['connections'],
    'settings': wf.get('settings', {})
}

up_r = requests.put(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', json=wf_update, headers=headers)
print('Workflow update status:', up_r.status_code)
