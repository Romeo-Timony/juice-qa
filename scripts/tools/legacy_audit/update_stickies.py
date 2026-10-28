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
stickies = [n for n in nodes if n['type'] == 'n8n-nodes-base.stickyNote']

# Define clean, professional sticky configurations
sticky_configs = {
    "Стикер: Приём задач": {
        "pos": [-352, -50],
        "width": 430,
        "height": 700,
        "color": 6,
        "content": "## 📥 1. Приём задач и событий\n\n**Что здесь происходит:**\nВходящие вебхуки из Jira (обновление статуса тикета, комментарии) и Qase TMS (синхронизация тестов drift). Мгновенный перехват событий разработки."
    },
    "Стикер: Проверка готовности (DoR)": {
        "pos": [144, 100],
        "width": 1820,
        "height": 380,
        "color": 1,
        "content": "## 📋 2. Проверка готовности задачи (DoR Gate) [Этап 1]\n\n**Что здесь происходит:**\nЗагрузка тикета и Confluence-спецификации. Анализ качества критериев приемки (AC), валидация по чек-листу Definition of Ready и решение: пропустить или вернуть на доработку."
    },
    "Стикер: Возврат задачи": {
        "pos": [672, 650],
        "width": 1152,
        "height": 520,
        "color": 3,
        "content": "## ❌ 3. Возврат задачи при DoR Fail & Telegram Alert\n\n**Что здесь происходит:**\nЕсли требования неполные или контракты не согласованы — задача переводится в «qa-paused» либо возвращается в «К выполнению» с подробными замечаниями в Jira и алертом в Telegram."
    },
    "Стикер: Интеллект-карта проверок": {
        "pos": [2040, -30],
        "width": 680,
        "height": 320,
        "color": 4,
        "content": "## 🧠 4. Интеллект-карта проверок [Этап 2]\n\n**Что здесь происходит:**\nФормирование ментальной карты тест-дизайна (MindMap) по контрактам и пользовательским сценариям. Публикация Отчета 2 в Jira со структурой проверок."
    },
    "Стикер: Тест-кейсы и RTM": {
        "pos": [2080, 500],
        "width": 1580,
        "height": 520,
        "color": 5,
        "content": "## 🧪 5. Синхронизация с Qase TMS & Матрица RTM [Этапы 3 и 4]\n\n**Что здесь происходит:**\nГенерация BDD-тест-кейсов, дедупликация относительно существующей базы Qase TMS, сохранение новых тестов и публикация матрицы прослеживаемости требований (RTM) в Jira."
    },
    "Стикер: Контроль 1": {
        "pos": [3860, 50],
        "width": 680,
        "height": 340,
        "color": 7,
        "content": "## 🛡️ 6. Контроль 1 (Gate 1 Review) & Оповещение\n\n**Что здесь происходит:**\nПубликация интерактивной карточки согласования тестов в Jira (Gate 1). Отправка сводного уведомления в Telegram-канал команды QA."
    },
    "Стикер: GitHub Actions Trigger": {
        "pos": [4580, 50],
        "width": 480,
        "height": 340,
        "color": 2,
        "content": "## 🐙 7. GitHub Actions: Запуск CI/CD\n\n**Что здесь происходит:**\nНативный вызов GitHub API (workflow_dispatch) репозитория Romeo-Timony/juice-qa для запуска прогона автотестов. Оповещение команды в Telegram о старте пайплайна."
    },
    "Стикер: GitHub Actions Результаты": {
        "pos": [5100, 320],
        "width": 1050,
        "height": 380,
        "color": 6,
        "content": "## 📊 8. Результаты прогона в CI/CD (Allure Report) [Этап 8]\n\n**Что здесь происходит:**\nПрием вебхука с результатами от GitHub Actions runner, парсинг метрик Allure, публикация финального отчета в тикете Jira и закрытие задачи с итоговым отчетом в Telegram."
    }
}

# Apply updates to existing stickies and add new ones
existing_names = set(n['name'] for n in nodes)

for name, conf in sticky_configs.items():
    snode = next((n for n in nodes if n['name'] == name), None)
    if not snode:
        snode = {
            "parameters": {
                "content": conf["content"],
                "height": conf["height"],
                "width": conf["width"],
                "color": conf["color"]
            },
            "id": f"sticky-{abs(hash(name)) % 100000}",
            "name": name,
            "type": "n8n-nodes-base.stickyNote",
            "typeVersion": 1,
            "position": conf["pos"]
        }
        nodes.append(snode)
        print(f"Created sticky: {name}")
    else:
        snode["position"] = conf["pos"]
        snode["parameters"]["content"] = conf["content"]
        snode["parameters"]["width"] = conf["width"]
        snode["parameters"]["height"] = conf["height"]
        snode["parameters"]["color"] = conf["color"]
        print(f"Updated sticky: {name}")

wf_update = {
    'name': wf['name'],
    'nodes': nodes,
    'connections': wf['connections'],
    'settings': wf.get('settings', {})
}

up_r = requests.put(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', json=wf_update, headers=headers)
print('Workflow sticky update status:', up_r.status_code)
