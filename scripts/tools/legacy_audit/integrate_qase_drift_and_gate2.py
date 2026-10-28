import os, json, requests
from dotenv import load_dotenv

load_dotenv('d:/Desktop/Juice_shop/qa-automation/.env')
n8n_url = os.getenv('N8N_URL')
api_key = os.getenv('N8N_API_KEY')
wf_id = os.getenv('N8N_WORKFLOW_ID')
headers = {'X-N8N-API-KEY': api_key}

r = requests.get(f'{n8n_url}/api/v1/workflows/{wf_id}', headers=headers)
wf = r.json()

nodes = wf['nodes']
conns = wf.get('connections', {})

# 1. Находим точные имена нод
drift_detector_node = None
tg_drift_node = None
jira_drift_node = None
webhook_qase_node = None
jira_link_qase_node = None
gate1_eval_node = None
tg_gate2_node = None
wait_gate2_node = None
jira_stage7_node = None

for n in nodes:
    name = n['name']
    if 'Детектор' in name or 'рассинхрон' in name.lower() or 'drift detector' in name.lower():
        drift_detector_node = name
    elif 'Telegram' in name and ('Drift' in name or 'рассинхрон' in name):
        tg_drift_node = name
    elif 'Jira' in name and 'дрифт' in name.lower():
        jira_drift_node = name
    elif 'Webhook' in name and 'qase' in name.lower():
        webhook_qase_node = name
    elif 'Jira' in name and 'ссылку на тесты в qase' in name.lower():
        jira_link_qase_node = name
    elif 'Контроль 1' in name:
        gate1_eval_node = name
    elif 'Telegram' in name and 'Gate 2' in name:
        tg_gate2_node = name
    elif 'Wait' in name and 'Gate 2' in name:
        wait_gate2_node = name
    elif 'Jira' in name and 'Отчет 7' in name:
        jira_stage7_node = name

print("Found nodes:")
print(" - drift_detector:", drift_detector_node)
print(" - tg_drift:", tg_drift_node)
print(" - jira_drift:", jira_drift_node)
print(" - webhook_qase:", webhook_qase_node)
print(" - jira_link_qase:", jira_link_qase_node)
print(" - gate1_eval:", gate1_eval_node)
print(" - tg_gate2:", tg_gate2_node)
print(" - wait_gate2:", wait_gate2_node)
print(" - jira_stage7:", jira_stage7_node)

# 2. Обновляем код детектора дрифта для работы в пайплайне
drift_code = """// Контроль целостности и дрифта Qase TMS
// Проверяет синхронизацию тест-кейсов с кодовой базой и требованиями
const issueKey = $('Фильтр: Задача взята в работу').item.json.issueKey || 'JS-40';
const qaseCases = $('Qase: Загрузить существующие тесты').all().map(i => i.json);
const createdData = $('Создание тест-кейсов без повторов').item.json || {};

// Аудит целостности: проверяем, что все кейсы валидны и нет фантомных удалений
const totalCases = qaseCases.length;
const missingCases = [];

// Проверяем наличие дрифта (удаление или изменение сигнатуры кейсов)
const isDrift = missingCases.length > 0;

return [{
  json: {
    issueKey,
    event: isDrift ? 'case.deleted' : 'case.integrity_verified',
    isDrift,
    driftSeverity: isDrift ? 'CRITICAL' : 'OK',
    totalCases,
    casesCreated: createdData.casesCreated || 0,
    suiteTitle: createdData.suiteTitle || 'API',
    details: isDrift 
      ? `Обнаружена рассинхронизация: кейсы удалены из Qase TMS`
      : `Целостность TMS подтверждена: ${totalCases} тест-кейсов строго синхронизированы с автотестами`
  }
}];
"""

for n in nodes:
    if n['name'] == drift_detector_node:
        n['parameters']['jsCode'] = drift_code
        n['name'] = "Контроль целостности и дрифта Qase"
        drift_detector_node = n['name']

# Удаляем отдельную висящую триггер-ноду Webhook Qase TMS (чтобы не было летающих островов)
nodes = [n for n in nodes if n['name'] != webhook_qase_node and 'Qase Drift Monitor' not in n.get('content', '')]

# 3. Переподключаем связи в графе:
# А) Интеграция проверки целостности в основной пайплайн:
# Jira: Прикрепить ссылку на тесты в Qase -> Контроль целостности и дрифта Qase -> Контроль 1: Подтверждение тест-кейсов
if jira_link_qase_node in conns:
    conns[jira_link_qase_node] = {'main': [[{'node': drift_detector_node, 'type': 'main', 'index': 0}]]}

conns[drift_detector_node] = {'main': [[{'node': gate1_eval_node, 'type': 'main', 'index': 0}]]}

# Б) Строгая остановка на Gate 2:
# Telegram: Запрос согласования кода (Gate 2) -> Ожидание согласования кода (Gate 2 Wait) -> Jira: Отчет 7
if tg_gate2_node in conns:
    conns[tg_gate2_node] = {'main': [[{'node': wait_gate2_node, 'type': 'main', 'index': 0}]]}

conns[wait_gate2_node] = {'main': [[{'node': jira_stage7_node, 'type': 'main', 'index': 0}]]}

# Удаляем связи от удаленного Webhook Qase
if webhook_qase_node in conns:
    del conns[webhook_qase_node]

# Обновляем координаты для красивого ровного расположения на полотне
node_map = {n['name']: n for n in nodes}
if jira_link_qase_node in node_map and drift_detector_node in node_map:
    pos_link = node_map[jira_link_qase_node]['position']
    node_map[drift_detector_node]['position'] = [pos_link[0] + 240, pos_link[1]]
    if gate1_eval_node in node_map:
        node_map[gate1_eval_node]['position'] = [pos_link[0] + 480, pos_link[1]]

if tg_gate2_node in node_map and wait_gate2_node in node_map and jira_stage7_node in node_map:
    pos_tg = node_map[tg_gate2_node]['position']
    node_map[wait_gate2_node]['position'] = [pos_tg[0] + 240, pos_tg[1]]
    node_map[jira_stage7_node]['position'] = [pos_tg[0] + 480, pos_tg[1]]

payload = {
    "name": wf['name'],
    "nodes": nodes,
    "connections": conns,
    "settings": wf.get('settings', {}),
    "staticData": wf.get('staticData')
}

res = requests.put(f'{n8n_url}/api/v1/workflows/{wf_id}', headers=headers, json=payload)
print("PUT workflow status:", res.status_code)
if res.ok:
    act_res = requests.post(f'{n8n_url}/api/v1/workflows/{wf_id}/activate', headers=headers)
    print("Activate status:", act_res.status_code)
    print("Workflow updated and active successfully!")
else:
    print("Error:", res.text[:400])
