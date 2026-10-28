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

# Find if GitHub node already exists
gh_node = next((n for n in nodes if 'GitHub' in n['name'] and n['type'] == 'n8n-nodes-base.github'), None)

if not gh_node:
    gh_node = {
        "parameters": {
            "authentication": "accessToken",
            "resource": "workflow",
            "operation": "dispatch",
            "owner": "Romeo-Timony",
            "repository": "juice-qa",
            "workflowId": "qa_tests.yml",
            "ref": "main"
        },
        "credentials": {
            "githubApi": {
                "id": "Vmo2I72RKP3SWreX",
                "name": "GitHub API (Romeo-Timony)"
            }
        },
        "id": "gh-dispatch-workflow",
        "name": "GitHub: Запуск автотестов в CI/CD",
        "type": "n8n-nodes-base.github",
        "typeVersion": 1,
        "position": [4650, 192],
        "notes": "🚀 Запускает рабочий процесс qa_tests.yml в GitHub Actions репозитория Romeo-Timony/juice-qa при согласовании тест-кейсов."
    }
    nodes.append(gh_node)
    print("Added GitHub node!")

# Add Telegram Start CI/CD node if not exists
tg_start_node = next((n for n in nodes if n['name'] == 'Telegram: Оповещение о старте CI/CD'), None)
if not tg_start_node:
    tg_start_node = {
        "parameters": {
            "chatId": "1434200911",
            "text": "🚀 <b>[CI/CD: Запуск прогона автотестов]</b>\n\n📌 <b>Задача:</b> {{ $('Подготовка данных для тест-кейсов').item.json.issueKey || 'JS' }}\n⚙️ <b>Репозиторий:</b> Romeo-Timony/juice-qa\n🌿 <b>Ветка / Workflow:</b> qa_tests.yml (main)\n\n🔄 Автотесты запущены в GitHub Actions. Ожидаем формирования отчета Allure...",
            "additionalFields": {
                "parse_mode": "HTML"
            }
        },
        "credentials": {
            "telegramApi": {
                "id": "dUppB4c1jJrLuGqq",
                "name": "QA Telegram Bot"
            }
        },
        "id": "tg-cicd-started-native",
        "name": "Telegram: Оповещение о старте CI/CD",
        "type": "n8n-nodes-base.telegram",
        "typeVersion": 1.2,
        "position": [4880, 192],
        "notes": "📢 Оповещает команду в Telegram о старте пайплайна в GitHub Actions."
    }
    nodes.append(tg_start_node)
    print("Added Telegram Start CI/CD node!")

# Wire: Telegram DoR Approved -> GitHub Dispatch -> Telegram Start CI/CD
# In connections:
# 'Telegram: Оповещение об успешном DoR' -> 'GitHub: Запуск автотестов в CI/CD'
connections['Telegram: Оповещение об успешном DoR'] = {
    'main': [[{'node': 'GitHub: Запуск автотестов в CI/CD', 'type': 'main', 'index': 0}]]
}
connections['GitHub: Запуск автотестов в CI/CD'] = {
    'main': [[{'node': 'Telegram: Оповещение о старте CI/CD', 'type': 'main', 'index': 0}]]
}

# Update positions of Allure nodes for clean visual alignment:
# Webhook: Прием отчетов GitHub Actions -> [5150, 480]
# Парсинг отчета Allure -> [5400, 480]
# Jira: Опубликовать отчет Allure -> [5650, 480]
# Telegram: Отчет Allure из CI/CD -> [5900, 480]
for n in nodes:
    if n['name'] == 'Webhook: Прием отчетов GitHub Actions':
        n['position'] = [5150, 480]
    elif n['name'] == 'Парсинг отчета Allure':
        n['position'] = [5400, 480]
    elif n['name'] == 'Jira: Опубликовать отчет Allure':
        n['position'] = [5650, 480]
    elif n['name'] == 'Telegram: Отчет Allure из CI/CD':
        n['position'] = [5900, 480]

# Update workflow in n8n
wf_update = {
    'name': wf['name'],
    'nodes': nodes,
    'connections': connections,
    'settings': wf.get('settings', {})
}

up_r = requests.put(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', json=wf_update, headers=headers)
print('Workflow update status:', up_r.status_code)
if up_r.status_code == 200:
    print('Workflow successfully updated in n8n!')
else:
    print('Error updating workflow:', up_r.text[:500])
