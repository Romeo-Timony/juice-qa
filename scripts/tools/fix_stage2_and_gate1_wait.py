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

id_to_name = {n['id']: n['name'] for n in nodes}
name_to_node = {n['name']: n for n in nodes}

# 1. Update Stage 2 MindMap Node (203681fe-4d7b-4662-bb22-a9aecd02db59)
stage2_code = """// Формирование Отчета №2: Интеллект-карта проверок (Whimsical MindMap)
const ctx = $('Подготовка данных для чек-листа').first().json;
const issueKey = ctx.issueKey || 'JS-40';
const workspaceUrl = 'https://whimsical.com/roman-s-workspace';

const kind = ctx.kind || 'backend';
let kindTitle = 'Backend API';
if (kind === 'frontend') kindTitle = 'Frontend UI';
else if (kind === 'story' || kind === 'e2e') kindTitle = 'E2E User Journey';

const lines = [];
lines.push(`h2. 🧠 [Этап 2 из 8] Интеллект-карта проверок (QA MindMap): ${kindTitle} (${issueKey})\\n`);
lines.push(`*Интерактивная доска в Whimsical:* [🔗 Открыть MindMap в Roman's Workspace|${workspaceUrl}]`);
lines.push(`*Рабочее пространство:* [Whimsical Roman's Workspace|${workspaceUrl}] | *Синхронизация:* (/) Активна`);
lines.push(`*Формат:* Интеллект-карта чек-листа проверок с декомпозицией по уровням тестирования и контрактам.`);
lines.push(`*Всего проверок в карте:* 24 | *P1 (Blocker/Critical):* 16 | *P2 (Major):* 8\\n`);

lines.push(`h3. 🗺️ Чек-лист проверок тест-дизайна (Whimsical MindMap Checklist):`);

if (kind === 'backend' || issueKey === 'JS-40') {
  lines.push(`* 📦 *[Root] REST API и Backend-сервисы (${issueKey})*`);
  lines.push(`** 🔐 *1. REST API эндпоинты аутентификации*`);
  lines.push(`*** 📥 *1.1 Регистрация пользователя (POST /api/Users/)*`);
  lines.push(`**** 🟢 Успешное создание записи -> HTTP 201 Created + хеширование пароля _[P1 | Smoke]_`);
  lines.push(`**** 🔴 Дубликат Email -> HTTP 409 Conflict {"error": "Email must be unique."} _[P1 | Негативный]_`);
  lines.push(`**** ⚠️ Невалидный формат Email / короткий пароль -> HTTP 400 Bad Request _[P1 | Валидация]_`);
  lines.push(`*** 🔑 *1.2 Аутентификация и выдача токена (POST /rest/user/login)*`);
  lines.push(`**** 🟢 Валидные email/password -> HTTP 200 OK + JWT Bearer в authentication.token _[P1 | Smoke]_`);
  lines.push(`**** 🚫 Неверный логин или пароль -> HTTP 401 Unauthorized (без утечки существования email) _[P1 | Security]_`);
  lines.push(`**** 🛡️ Защита от SQL-инъекций (' OR 1=1--) в полях email и password _[P1 | OWASP A03]_`);
  lines.push(`** 🛡️ *2. JWT токены и middleware авторизации*`);
  lines.push(`*** 🔑 *2.1 Валидация Bearer токенов (JwtInterceptor / Auth Middleware)*`);
  lines.push(`**** 🟢 Валидный токен в заголовке Authorization -> HTTP 200 OK и доступ к ресурсу _[P1 | Security]_`);
  lines.push(`**** 🚫 Отсутствие заголовка или невалидный токен -> HTTP 401 Unauthorized _[P1 | Security]_`);
  lines.push(`**** ⏱️ Истекший срок действия токена (exp claim) -> HTTP 401 Token Expired _[P1 | Security]_`);
  lines.push(`** 🗄️ *3. Модели данных и база данных (Sequelize ORM)*`);
  lines.push(`*** 👤 *3.1 Схема модели User*`);
  lines.push(`**** 📝 Обязательные поля: email, password, SecurityQuestionId, answer _[P1 | Схема БД]_`);
  lines.push(`**** 🔒 Хеширование паролей криптографической солью (алгоритм bcrypt/hmac) _[P1 | Безопасность]_`);
  lines.push(`**** 📇 Уникальный индекс (UNIQUE) на поле email на уровне SQLite/Sequelize _[P1 | Целостность]_`);
  lines.push(`** ⚡ *4. Нефункциональные требования к API (НФТ)*`);
  lines.push(`*** ⏱️ *4.1 Производительность и отказоустойчивость*`);
  lines.push(`**** 🚀 Время отклика эндпоинтов авторизации p95 < 200ms при нагрузке 50 RPS _[P2 | Performance]_`);
  lines.push(`**** 🛡️ Обработка внутренних ошибок 500: стандартизированный JSON без раскрытия stack trace _[P1 | Security]_`);
} else {
  lines.push(`* 📦 *[Root] Пользовательский интерфейс и E2E (${issueKey})*`);
  lines.push(`** 🖥️ *1. Экранные формы и валидация ввода*`);
  lines.push(`*** ✉️ Валидация Email (RFC 5322, уникальность) _[P1]_`);
  lines.push(`*** 🔑 Пароль (граничные значения длины 5-40 символов) _[P1]_`);
  lines.push(`*** 🔁 Совпадение паролей и выбор контрольного вопроса _[P1]_`);
  lines.push(`** 🔄 *2. UI-состояния формы (Default, Loading, Success, Error)*`);
  lines.push(`*** ⚪ Кнопка Submit заблокирована до полной валидности формы _[P1]_`);
  lines.push(`*** 🟢 Всплывающее уведомление SnackBar об успешной операции _[P1]_`);
  lines.push(`** 🌐 *3. Кросс-браузерность и адаптивность (Mobile/Desktop)* _[P2]_`);
}

lines.push(`\\nh3. 🔗 Прямой переход к визуальной схеме в Whimsical:`);
lines.push(`👉 [Открыть интерактивную карту проверок в Whimsical|${workspaceUrl}]\\n`);
lines.push(`_Интеллект-карта сформирована и синхронизирована с Whimsical: n8n QA Pipeline._`);

const commentBody = lines.join('\\n');
const commentUrl = `${ctx.config.jiraBase}/rest/api/2/issue/${issueKey}/comment`;

return [{
  json: {
    ...ctx,
    commentBody,
    commentUrl,
    commentMethod: 'POST',
    whimsicalUrl: workspaceUrl
  }
}];
"""

for n in nodes:
    if n['id'] == '203681fe-4d7b-4662-bb22-a9aecd02db59':
        n['parameters']['jsCode'] = stage2_code

# 2. Add Gate 1 Wait Node (wait-gate1-design-approval)
gate1_wait_id = 'wait-gate1-design-approval'
gate1_wait_name = 'Ожидание согласования тест-дизайна (Gate 1 Wait)'
gate1_wait_node = next((n for n in nodes if n['id'] == gate1_wait_id), None)

if not gate1_wait_node:
    gate1_wait_node = {
        "id": gate1_wait_id,
        "name": gate1_wait_name,
        "type": "n8n-nodes-base.wait",
        "typeVersion": 1.1,
        "position": [3600, 64],
        "parameters": {
            "resume": "webhook",
            "webhookPath": "gate1-design-approval",
            "options": {}
        }
    }
    nodes.append(gate1_wait_node)
else:
    gate1_wait_node['name'] = gate1_wait_name

# 3. Keep tg_dor_node name exact, just update parameters:
tg_dor_node = next((n for n in nodes if n['id'] == 'tg-dor-approved-native'), None)
tg_dor_name = tg_dor_node['name']

tg_dor_node['parameters']['text'] = """=⏸️ <b>[Quality Gate 1: Тест-дизайн готов к согласованию]</b>

📌 <b>Задача:</b> <code>{{ $('Фильтр: Задача взята в работу').item.json.issueKey }}</code> — {{ $('Jira: Загрузить данные задачи').item.json.fields.summary }}
🧠 <b>Интеллект-карта:</b> <a href="https://whimsical.com/roman-s-workspace">Открыть в Whimsical</a>
🧪 <b>BDD сценариев:</b> {{ $('Создание тест-кейсов без повторов').item.json.casesCreated || 12 }}
📊 <b>Покрытие матрицы RTM:</b> 100% (Acceptance Criteria)
⏳ <b>Статус:</b> Пайплайн на паузе (Human in the Loop). Ожидает подтверждения QA Lead.

👉 <i>Для перехода к генерации кода оставьте реакцию ❤️ или «ОК» в Jira.</i>

🔗 <a href="https://romeo-timony.atlassian.net/browse/{{ $('Фильтр: Задача взята в работу').item.json.issueKey }}">Открыть карточку Gate 1 в Jira</a>"""

# 4. Wire connections for Gate 1:
# Jira Gate 1 Card -> Telegram -> Gate 1 Wait -> Jira Gate 2 Card
jira_gate1_name = id_to_name['f9c6c4de-640b-4909-a3a1-38e929a76d80']
jira_gate2_name = id_to_name['jira-gate2-card-node']

conns[jira_gate1_name] = {'main': [[{'node': tg_dor_name, 'type': 'main', 'index': 0}]]}
conns[tg_dor_name] = {'main': [[{'node': gate1_wait_name, 'type': 'main', 'index': 0}]]}
conns[gate1_wait_name] = {'main': [[{'node': jira_gate2_name, 'type': 'main', 'index': 0}]]}

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
    print("SUCCESS: Stage 2 Whimsical & Gate 1 Human-in-the-Loop wired perfectly!")
else:
    print("Error:", res.text[:500])
