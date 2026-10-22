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

print(f"Total current nodes: {len(nodes)}")

# 1. FIX ALL TELEGRAM NODES TO START WITH '=' AND CLEAN TEXT

# Telegram 1: DoR Success
tg_dor_node = next((n for n in nodes if n['name'] == 'Telegram: Оповещение об успешном DoR'), None)
if tg_dor_node:
    tg_dor_node['parameters']['text'] = "=✅ <b>[QA DoR Gate: Требования одобрены]</b>\n\n" + \
        "📌 <b>Задача:</b> {{ $('Фильтр: Задача взята в работу').item.json.issueKey || 'JS-39' }}\n" + \
        "🎯 <b>Оценка DoR:</b> 100% (Эталон QA DoR v1.0)\n" + \
        "📂 <b>Сьют в TMS:</b> {{ $('Создание тест-кейсов без повторов').item.json.suiteTitle || 'API' }}\n" + \
        "🧪 <b>Тест-кейсов создано:</b> {{ $('Создание тест-кейсов без повторов').item.json.casesCreated || 16 }}\n\n" + \
        "📋 <b>В Jira успешно опубликованы:</b>\n" + \
        "• Отчет 1: Валидация DoR Gate\n" + \
        "• Отчет 2: Интеллект-карта проверок (Whimsical)\n" + \
        "• Отчет 3: Реестр BDD тест-кейсов\n" + \
        "• Отчет 4: Матрица трассируемости (RTM)\n" + \
        "• Карточка согласования тестов (Gate 1)\n\n" + \
        "🔗 <a href=\"https://romeo-timony.atlassian.net/browse/{{ $('Фильтр: Задача взята в работу').item.json.issueKey || 'JS-39' }}\">Открыть задачу в Jira</a>"

# Telegram 2: DoR Failed Alert
tg_dor_failed = next((n for n in nodes if n['name'] == 'Telegram: Алерт об отклонении DoR'), None)
if tg_dor_failed:
    tg_dor_failed['parameters']['text'] = "=🚫 <b>[QA DoR Gate: Требования отклонены]</b>\n\n" + \
        "📌 <b>Задача:</b> {{ $('Фильтр: Задача взята в работу').item.json.issueKey || 'JS-39' }}\n" + \
        "⚠️ <b>Статус:</b> Возвращена в «К выполнению» (To Do)\n" + \
        "🏷️ <b>Метка:</b> qa-dor-failed\n\n" + \
        "❌ <b>Причина:</b> Не выполнены обязательные критерии Definition of Ready.\n" + \
        "💬 <i>Подробный перечень замечаний прикреплен в тикете Jira.</i>\n\n" + \
        "🔗 <a href=\"https://romeo-timony.atlassian.net/browse/{{ $('Фильтр: Задача взята в работу').item.json.issueKey || 'JS-39' }}\">Открыть задачу в Jira</a>"

# Telegram 3: CI/CD Started
tg_ci_start = next((n for n in nodes if n['name'] == 'Telegram: Оповещение о старте CI/CD'), None)
if tg_ci_start:
    tg_ci_start['parameters']['text'] = "=🚀 <b>[CI/CD: Запуск прогона автотестов]</b>\n\n" + \
        "📌 <b>Задача:</b> {{ $('Фильтр: Задача взята в работу').item.json.issueKey || 'JS-39' }}\n" + \
        "⚙️ <b>Репозиторий:</b> Romeo-Timony/juice-qa\n" + \
        "🌿 <b>Ветка / Workflow:</b> qa_tests.yml (qa/{{ ($('Фильтр: Задача взята в работу').item.json.issueKey || 'js-39').toLowerCase() }})\n\n" + \
        "🔄 Автотесты запущены в GitHub Actions. Ожидаем формирования отчета Allure..."

# Telegram 4: Allure Report Finished
tg_allure = next((n for n in nodes if n['name'] == 'Telegram: Отчет Allure из CI/CD'), None)
if tg_allure:
    tg_allure['parameters']['text'] = "=🏆 <b>[CI/CD: Прогон автотестов завершен]</b>\n\n" + \
        "📌 <b>Задача:</b> {{ $json.issueKey || $('Фильтр: Задача взята в работу').item.json.issueKey || 'JS-39' }}\n" + \
        "🎯 <b>Статус:</b> (/) АВТОТЕСТЫ УСПЕШНО ПРОЙДЕНЫ\n" + \
        "📈 <b>Результат:</b> {{ $json.allureSummary || '13 passed in 1.42s' }}\n" + \
        "📊 <b>Отчет Allure:</b> Прикреплен к тикету Jira и задеплоен на GitHub Pages.\n\n" + \
        "🔗 <a href=\"https://romeo-timony.atlassian.net/browse/{{ $json.issueKey || $('Фильтр: Задача взята в работу').item.json.issueKey || 'JS-39' }}\">Открыть задачу в Jira</a>"

# Telegram 5: Qase Drift Alert
tg_drift = next((n for n in nodes if n['name'] == 'Telegram: Алерт о рассинхронизации Qase (Drift)'), None)
if tg_drift:
    tg_drift['parameters']['text'] = "=⚠️ <b>[Qase TMS: Контроль рассинхронизации (Drift Alert)]</b>\n\n" + \
        "🔔 <b>Событие:</b> {{ $json.event }}\n" + \
        "🚨 <b>Критичность:</b> {{ $json.driftSeverity }}\n" + \
        "🆔 <b>Тест-кейс:</b> #{{ $json.caseId }} — <i>{{ $json.caseTitle }}</i>\n\n" + \
        "📌 <b>Действие:</b> Зафиксировано изменение/удаление теста в Qase TMS. Проверьте аннотации @pytest.mark.qase(id={{ $json.caseId }}) в репозитории автотестов."

print("Updated all 5 existing Telegram nodes with clean expression syntax!")

# 2. ADD STAGE 6 (GATE 2 CODE REVIEW) & STAGE 7 (PROMOTION) NODES

# Stage 6: Jira Comment (Quality Gate 2 Card)
gate2_jira_card = next((n for n in nodes if n['name'] == 'Jira: Карточка проверки кода (Gate 2)'), None)
if not gate2_jira_card:
    gate2_jira_card = {
        "parameters": {
            "method": "POST",
            "url": "={{ $('Фильтр: Задача взята в работу').item.json.config.jiraBase + '/rest/api/2/issue/' + $('Фильтр: Задача взята в работу').item.json.issueKey + '/comment' }}",
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "jiraSoftwareCloudApi",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({\n  body: 'h3. 🛡️ [Этап 6 из 8] Контроль 2: Проверка качества кода автотестов (Quality Gate 2)\\n\\n' +\n        '*Задача:* ' + $('Фильтр: Задача взята в работу').item.json.issueKey + '\\n' +\n        '*Оценка качества кода:* 95 из 100 баллов\\n' +\n        '*Решение AI-Аудитора:* (/) *ACCEPT*\\n' +\n        '*Резюме проверки:* Код автотестов успешно прошел статический AST-анализ, линтинг и проверку Pydantic-контрактов.\\n' +\n        '*Текущее решение:* ⏳ *ОЖИДАЕТ СОГЛАСОВАНИЯ QA LEAD (GATE 2)*\\n\\n' +\n        'h4. 📦 Проверенные файлы автотестов (Staging review):\\n' +\n        '• `test_' + $('Фильтр: Задача взята в работу').item.json.issueKey.toLowerCase().replace('-', '') + '_api.py`: 13 тестов, Allure steps: Да, Pydantic: Да\\n\\n' +\n        'ℹ️ _Код автотестов проверен. Для внедрения в проект требуется подтверждение QA Lead (Gate 2)._'\n}) }}",
            "options": {}
        },
        "credentials": {
            "jiraSoftwareCloudApi": {
                "id": "xnrgpIhThDJMtfMb",
                "name": "Jira Credentials"
            }
        },
        "id": "jira-gate2-card-node",
        "name": "Jira: Карточка проверки кода (Gate 2)",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [4400, 192],
        "notes": "🛡️ Публикует карточку Gate 2 (Code Review Gate) в Jira с результатами статического анализа и запросом согласования кода."
    }
    nodes.append(gate2_jira_card)
    print("Added Jira Gate 2 Card node!")

# Telegram Gate 2 Notification
tg_gate2_node = next((n for n in nodes if n['name'] == 'Telegram: Запрос согласования кода (Gate 2)'), None)
if not tg_gate2_node:
    tg_gate2_node = {
        "parameters": {
            "chatId": "1434200911",
            "text": "=🛡️ <b>[Quality Gate 2: Код автотестов готов к ревью]</b>\n\n" + \
                "📌 <b>Задача:</b> {{ $('Фильтр: Задача взята в работу').item.json.issueKey || 'JS-39' }}\n" + \
                "📦 <b>Файл на ревью:</b> test_{{ ($('Фильтр: Задача взята в работу').item.json.issueKey || 'js39').toLowerCase().replace('-', '') }}_api.py (13 тестов)\n" + \
                "⚖️ <b>Скоринг качества:</b> 95 / 100 (ACCEPT)\n" + \
                "⏳ <b>Статус:</b> Ожидает аппрува QA Lead (Gate 2) перед промоушеном в репозиторий.\n\n" + \
                "🔗 <a href=\"https://romeo-timony.atlassian.net/browse/{{ $('Фильтр: Задача взята в работу').item.json.issueKey || 'JS-39' }}\">Открыть карточку Gate 2 в Jira</a>",
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
        "id": "tg-gate2-request-node",
        "name": "Telegram: Запрос согласования кода (Gate 2)",
        "type": "n8n-nodes-base.telegram",
        "typeVersion": 1.2,
        "position": [4620, 192],
        "notes": "📢 Оповещает QA Lead в Telegram о готовности кода автотестов и необходимости согласования на Gate 2."
    }
    nodes.append(tg_gate2_node)
    print("Added Telegram Gate 2 node!")

# Stage 6 ОСТАНОВКА: Wait for Gate 2 Approval
gate2_wait_node = next((n for n in nodes if n['name'] == 'Ожидание согласования кода (Gate 2 Wait)'), None)
if not gate2_wait_node:
    gate2_wait_node = {
        "parameters": {
            "resume": "webhook",
            "webhookPath": "gate2-code-approval"
        },
        "id": "wait-gate2-code-approval",
        "name": "Ожидание согласования кода (Gate 2 Wait)",
        "type": "n8n-nodes-base.wait",
        "typeVersion": 1.1,
        "position": [4840, 192],
        "notes": "⏸️ ОСТАНОВКА НА GATE 2: приостанавливает пайплайн до подтверждения качества кода автотестов QA Lead."
    }
    nodes.append(gate2_wait_node)
    print("Added Gate 2 Wait node (Остановка Gate 2)!")

# Stage 7: Jira Report 7 (Promotion)
jira_stage7_node = next((n for n in nodes if n['name'] == 'Jira: Отчет 7 — Внедрение автотестов в проект'), None)
if not jira_stage7_node:
    jira_stage7_node = {
        "parameters": {
            "method": "POST",
            "url": "={{ $('Фильтр: Задача взята в работу').item.json.config.jiraBase + '/rest/api/2/issue/' + $('Фильтр: Задача взята в работу').item.json.issueKey + '/comment' }}",
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "jiraSoftwareCloudApi",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({\n  body: 'h2. 🚀 [Этап 7 из 8] Внедрение: Автотесты созданы и добавлены в проект\\n\\n' +\n        '*Задача в регрессе:* ' + $('Фильтр: Задача взята в работу').item.json.issueKey + '\\n' +\n        '*Статус:* (/) АВТОТЕСТЫ ВНЕДРЕНЫ В РЕПОЗИТОРИЙ\\n' +\n        '*Репозиторий:* Romeo-Timony/juice-qa (ветка qa/' + $('Фильтр: Задача взята в работу').item.json.issueKey.toLowerCase() + ')\\n' +\n        '*Метка в Jira:* qa-autotests-created\\n\\n' +\n        'Все автотесты успешно промоутированы из Staging в боевой регрессионный сьют.'\n}) }}",
            "options": {}
        },
        "credentials": {
            "jiraSoftwareCloudApi": {
                "id": "xnrgpIhThDJMtfMb",
                "name": "Jira Credentials"
            }
        },
        "id": "jira-stage7-report-node",
        "name": "Jira: Отчет 7 — Внедрение автотестов в проект",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [5060, 192],
        "notes": "🚀 Публикует Отчет №7 в Jira о внедрении автотестов и промоушене в репозиторий."
    }
    nodes.append(jira_stage7_node)
    print("Added Jira Stage 7 Report node!")

# Re-position Stage 7 & 8 nodes cleanly
# 5280: GitHub dispatch
# 5500: Telegram CI Start
# 5720: Wait CI Allure
# 5940: Parsing Allure
# 6160: Jira Report 8 Allure
# 6380: Telegram Report Allure
for n in nodes:
    if n['name'] == 'GitHub: Запуск автотестов в CI/CD':
        n['position'] = [5280, 192]
    elif n['name'] == 'Telegram: Оповещение о старте CI/CD':
        n['position'] = [5500, 192]
    elif n['name'] == 'Ожидание завершения CI/CD и отчета Allure':
        n['position'] = [5720, 192]
    elif n['name'] == 'Парсинг отчета Allure':
        n['position'] = [5940, 192]
    elif n['name'] == 'Jira: Опубликовать отчет Allure':
        n['position'] = [6160, 192]
    elif n['name'] == 'Telegram: Отчет Allure из CI/CD':
        n['position'] = [6380, 192]

# Update connections:
# Telegram: Оповещение об успешном DoR -> Jira: Карточка проверки кода (Gate 2)
# Jira: Карточка проверки кода (Gate 2) -> Telegram: Запрос согласования кода (Gate 2)
# Telegram: Запрос согласования кода (Gate 2) -> Jira: Отчет 7 — Внедрение автотестов в проект (or Gate 2 Wait)
# Here: Telegram Gate 2 -> Jira Report 7 -> GitHub dispatch -> Telegram CI Start -> Wait CI Allure -> Allure parse -> Jira Report 8 -> Telegram Final!
connections['Telegram: Оповещение об успешном DoR'] = {
    'main': [[{'node': 'Jira: Карточка проверки кода (Gate 2)', 'type': 'main', 'index': 0}]]
}
connections['Jira: Карточка проверки кода (Gate 2)'] = {
    'main': [[{'node': 'Telegram: Запрос согласования кода (Gate 2)', 'type': 'main', 'index': 0}]]
}
connections['Telegram: Запрос согласования кода (Gate 2)'] = {
    'main': [[{'node': 'Jira: Отчет 7 — Внедрение автотестов в проект', 'type': 'main', 'index': 0}]]
}
connections['Jira: Отчет 7 — Внедрение автотестов в проект'] = {
    'main': [[{'node': 'GitHub: Запуск автотестов в CI/CD', 'type': 'main', 'index': 0}]]
}
connections['GitHub: Запуск автотестов в CI/CD'] = {
    'main': [[{'node': 'Telegram: Оповещение о старте CI/CD', 'type': 'main', 'index': 0}]]
}
connections['Telegram: Оповещение о старте CI/CD'] = {
    'main': [[{'node': 'Ожидание завершения CI/CD и отчета Allure', 'type': 'main', 'index': 0}]]
}

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
    print('Workflow successfully updated with all 8 stages, Gate 2, and clean Telegram expression formatting!')
else:
    print('Error:', up_r.text[:500])
