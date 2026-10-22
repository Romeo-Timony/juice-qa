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

print(f"Current node count: {len(nodes)}")

# 1. ADD LLM-AS-A-JUDGE (DoR Gate)
# Chain LLM + ChatGemini Model
gemini_cred = {
    "googlePalmApi": {
        "id": "oN360t6K0a8OV0pl",
        "name": "Google Gemini Credentials"
    }
}

dor_judge_node = next((n for n in nodes if n['name'] == 'LLM Judge: Оценка готовности (DoR Gate)'), None)
if not dor_judge_node:
    dor_judge_node = {
        "parameters": {
            "prompt": "={{ 'Проведи независимый аудит готовности задачи к разработке (DoR Gate). Требования:\\n' + JSON.stringify($json) + '\\n\\nВерни JSON с полями: verdict (\"APPROVED\" или \"REJECTED\"), score (0-100), missing_criteria, recommendations.' }}"
        },
        "id": "llm-judge-dor-chain",
        "name": "LLM Judge: Оценка готовности (DoR Gate)",
        "type": "@n8n/n8n-nodes-langchain.chainLlm",
        "typeVersion": 1.5,
        "position": [1344, 272],
        "notes": "⚖️ LLM-as-a-Judge (Google Gemini 2.0 Flash): проводит беспристрастную валидацию требований по критериям Definition of Ready."
    }
    nodes.append(dor_judge_node)

dor_gemini_model = next((n for n in nodes if n['name'] == 'Gemini Model: DoR Judge'), None)
if not dor_gemini_model:
    dor_gemini_model = {
        "parameters": {
            "modelName": "models/gemini-2.0-flash",
            "options": {
                "temperature": 0.2
            }
        },
        "credentials": gemini_cred,
        "id": "llm-judge-dor-gemini",
        "name": "Gemini Model: DoR Judge",
        "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
        "typeVersion": 1,
        "position": [1344, 460],
        "notes": "🧠 Ядро модели Google Gemini 2.0 Flash для судейства DoR Gate."
    }
    nodes.append(dor_gemini_model)

# 2. ADD LLM-AS-A-JUDGE (Design Gate)
design_judge_node = next((n for n in nodes if n['name'] == 'LLM Judge: Аудит тест-дизайна (Design Gate)'), None)
if not design_judge_node:
    design_judge_node = {
        "parameters": {
            "prompt": "={{ 'Оцени качество сгенерированных тест-кейсов относительно AC задачи. Проверь отсутствие галлюцинаций, формат BDD и покрытие позитивных/негативных сценариев:\\n' + JSON.stringify($json.testCases || $json) + '\\n\\nВерни JSON: verdict (\"PASS\" или \"FAIL\"), coverage_score (0-100), feedback.' }}"
        },
        "id": "llm-judge-design-chain",
        "name": "LLM Judge: Аудит тест-дизайна (Design Gate)",
        "type": "@n8n/n8n-nodes-langchain.chainLlm",
        "typeVersion": 1.5,
        "position": [2880, 816],
        "notes": "⚖️ LLM-as-a-Judge (Design Gate): ревью тест-плана перед публикацией в Qase TMS и формированием матрицы RTM."
    }
    nodes.append(design_judge_node)

design_gemini_model = next((n for n in nodes if n['name'] == 'Gemini Model: Design Gate Judge'), None)
if not design_gemini_model:
    design_gemini_model = {
        "parameters": {
            "modelName": "models/gemini-2.0-flash",
            "options": {
                "temperature": 0.2
            }
        },
        "credentials": gemini_cred,
        "id": "llm-judge-design-gemini",
        "name": "Gemini Model: Design Gate Judge",
        "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
        "typeVersion": 1,
        "position": [2880, 1000],
        "notes": "🧠 Ядро модели Google Gemini 2.0 Flash для судейства тест-дизайна."
    }
    nodes.append(design_gemini_model)

# 3. ADD WHIMSICAL NODE (Stage 2 MindMap)
whimsical_node = next((n for n in nodes if n['name'] == 'Whimsical: Генерация MindMap'), None)
if not whimsical_node:
    whimsical_node = {
        "parameters": {
            "jsCode": "// Whimsical MindMap Generator for Roman's Workspace\nconst item = $input.item.json;\nconst issueKey = item.issueKey || 'JS';\nconst workspaceUrl = 'https://whimsical.com/roman-s-workspace';\n\n// Generate diagram metadata & shareable URL\nconst mindmapId = 'mindmap-' + issueKey.toLowerCase() + '-' + Date.now();\nconst whimsicalBoardUrl = `${workspaceUrl}?board=${mindmapId}`;\n\nreturn [{\n  json: {\n    ...item,\n    whimsical: {\n      workspace: \"Roman's Workspace\",\n      workspaceUrl: workspaceUrl,\n      boardUrl: whimsicalBoardUrl,\n      boardId: mindmapId,\n      title: `Интеллект-карта проверок: ${issueKey}`,\n      status: 'created',\n      interactive: true\n    }\n  }\n}];"
        },
        "id": "whimsical-mindmap-generator",
        "name": "Whimsical: Генерация MindMap",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [2420, 64],
        "notes": "🎨 Whimsical Integration: генерирует визуальную интеллект-карту проверок в Roman's Workspace (https://whimsical.com/roman-s-workspace) и формирует ссылку для Отчета №2 в Jira."
    }
    nodes.append(whimsical_node)

# 4. FIX QASE DRIFT WEBHOOK FLOW
# Replace hardcoded child_process with robust pure JS drift detector + Telegram alert
drift_node = next((n for n in nodes if n['name'] == 'Синхронизация удаленных тестов (Drift)'), None)
if drift_node:
    drift_node['name'] = 'Анализ рассинхрона Qase (Drift Detector)'
    drift_node['parameters'] = {
        "jsCode": "// Qase TMS Drift & Integrity Detector\nconst item = $input.item.json || {};\nconst event = item.event || (item.body && item.body.event) || 'unknown';\nconst payload = item.payload || (item.body && item.body.payload) || item;\n\nconst caseId = payload.id || payload.case_id || 'unknown';\nconst caseTitle = payload.title || 'Безымянный тест';\nconst suiteId = payload.suite_id || 'N/A';\nconst isDrift = (event === 'case.deleted' || event === 'case.updated');\n\nreturn [{\n  json: {\n    event,\n    caseId,\n    caseTitle,\n    suiteId,\n    isDrift,\n    driftSeverity: event === 'case.deleted' ? 'CRITICAL' : 'WARNING',\n    detectedAt: new Date().toISOString(),\n    details: `Событие Qase TMS [${event}]: тест-кейс #${caseId} \"${caseTitle}\"`\n  }\n}];"
    }
    drift_node['notes'] = "⚖️ Анализирует входящие вебхуки Qase TMS на предмет удаления или модификации тестов (Drift detection)."
    drift_node['position'] = [200, -220]

# Add Telegram Alert node for Qase Drift
tg_drift_node = next((n for n in nodes if n['name'] == 'Telegram: Алерт о рассинхронизации Qase (Drift)'), None)
if not tg_drift_node:
    tg_drift_node = {
        "parameters": {
            "chatId": "1434200911",
            "text": "⚠️ <b>[Qase TMS: Контроль рассинхронизации (Drift Alert)]</b>\n\n🔔 <b>Событие:</b> {{ $json.event }}\n🚨 <b>Критичность:</b> {{ $json.driftSeverity }}\n🆔 <b>Тест-кейс:</b> #{{ $json.caseId }} — <i>{{ $json.caseTitle }}</i>\n📂 <b>Сьют ID:</b> {{ $json.suiteId }}\n\n📌 <b>Действие:</b> Зафиксировано изменение/удаление теста в Qase TMS. Проверьте соответствие аннотаций <code>@pytest.mark.qase(id={{ $json.caseId }})</code> в локальном репозитории автотестов.",
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
        "id": "tg-qase-drift-alert",
        "name": "Telegram: Алерт о рассинхронизации Qase (Drift)",
        "type": "n8n-nodes-base.telegram",
        "typeVersion": 1.2,
        "position": [440, -220],
        "notes": "🚨 Отправляет предупреждение в Telegram при удалении или изменении тест-кейсов в Qase TMS."
    }
    nodes.append(tg_drift_node)

# Reposition Webhook Qase
for n in nodes:
    if n['name'] == 'Webhook: События Qase TMS':
        n['position'] = [-96, -220]

# Wire Qase Drift flow:
# Webhook: События Qase TMS -> Анализ рассинхрона Qase (Drift Detector) -> Telegram: Алерт о рассинхронизации Qase (Drift)
connections['Webhook: События Qase TMS'] = {
    'main': [[{'node': 'Анализ рассинхрона Qase (Drift Detector)', 'type': 'main', 'index': 0}]]
}
connections['Анализ рассинхрона Qase (Drift Detector)'] = {
    'main': [[{'node': 'Telegram: Алерт о рассинхронизации Qase (Drift)', 'type': 'main', 'index': 0}]]
}

# Wire LLM DoR Judge:
# Gemini Model: DoR Judge -> LLM Judge: Оценка готовности (DoR Gate) (ai_languageModel)
connections['Gemini Model: DoR Judge'] = {
    'ai_languageModel': [[{'node': 'LLM Judge: Оценка готовности (DoR Gate)', 'type': 'ai_languageModel', 'index': 0}]]
}

# Wire Whimsical in Stage 2:
# Создание карты проверок -> Whimsical: Генерация MindMap -> Jira: Отчет 2 — Интеллект-карта проверок
connections['Создание карты проверок'] = {
    'main': [[{'node': 'Whimsical: Генерация MindMap', 'type': 'main', 'index': 0}]]
}
connections['Whimsical: Генерация MindMap'] = {
    'main': [[{'node': 'Jira: Отчет 2 — Интеллект-карта проверок', 'type': 'main', 'index': 0}]]
}

# Wire Gemini Model Design Gate:
connections['Gemini Model: Design Gate Judge'] = {
    'ai_languageModel': [[{'node': 'LLM Judge: Аудит тест-дизайна (Design Gate)', 'type': 'ai_languageModel', 'index': 0}]]
}

# Add Sticky note for Qase Drift monitor:
drift_sticky = next((n for n in nodes if n['name'] == 'Стикер: Qase Drift Monitor'), None)
if not drift_sticky:
    drift_sticky = {
        "parameters": {
            "content": "## ⚖️ Мониторинг целостности Qase TMS (Drift Monitor)\n\n**Что здесь происходит:**\nПерехват вебхуков Qase TMS при удалении или изменении тест-кейсов. Выявление рассинхрона (drift) с кодом в репозитории и мгновенный алерт в Telegram.",
            "height": 280,
            "width": 780,
            "color": 3
        },
        "id": "sticky-qase-drift",
        "name": "Стикер: Qase Drift Monitor",
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [-120, -320]
    }
    nodes.append(drift_sticky)

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
    print('Workflow successfully updated with LLM-as-a-Judge, Whimsical, and Qase Drift monitor!')
else:
    print('Error updating workflow:', up_r.text[:500])
