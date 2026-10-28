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

test_wf = {
    'name': 'Test TG Expression Execution',
    'settings': {},
    'nodes': [
        {
            'parameters': {
                'httpMethod': 'POST',
                'path': 'test-tg-expr'
            },
            'id': 'wh1',
            'name': 'Webhook',
            'type': 'n8n-nodes-base.webhook',
            'typeVersion': 2,
            'position': [100, 100]
        },
        {
            'parameters': {
                'chatId': '1434200911',
                'text': '=✅ <b>[QA DoR Gate: Задача одобрена]</b>\n\n📌 <b>Задача:</b> {{ $json.body.issueKey || "JS-39" }} — {{ $json.body.summary || "Регистрация" }}\n🎯 <b>Оценка DoR:</b> 100%\n\n🔗 <a href="https://romeo-timony.atlassian.net/browse/{{ $json.body.issueKey || "JS-39" }}">Открыть задачу в Jira</a>',
                'additionalFields': {
                    'parse_mode': 'HTML'
                }
            },
            'credentials': {
                'telegramApi': {
                    'id': 'dUppB4c1jJrLuGqq',
                    'name': 'QA Telegram Bot'
                }
            },
            'id': 'tg1',
            'name': 'Telegram Test',
            'type': 'n8n-nodes-base.telegram',
            'typeVersion': 1.2,
            'position': [300, 100]
        }
    ],
    'connections': {
        'Webhook': {'main': [[{'node': 'Telegram Test', 'type': 'main', 'index': 0}]]}
    }
}

r = requests.post(f'{n8n_url}/api/v1/workflows', json=test_wf, headers=headers)
print('Create status:', r.status_code)
if r.status_code == 200:
    wid = r.json()['id']
    # Activate and test trigger
    requests.post(f'{n8n_url}/api/v1/workflows/{wid}/activate', headers=headers)
    t_r = requests.post(f'{n8n_url}/webhook/test-tg-expr', json={'issueKey': 'JS-39', 'summary': 'Регистрация пользователя'})
    print('Webhook trigger status:', t_r.status_code)
    requests.delete(f'{n8n_url}/api/v1/workflows/{wid}', headers=headers)
