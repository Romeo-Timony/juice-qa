import os
import sys
import json
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')

qase_token = os.getenv('QASE_API_TOKEN')
qase_url = os.getenv('QASE_API_URL', 'https://api.qase.io/v1')
headers = {'Token': qase_token, 'Content-Type': 'application/json'}
code = 'JS'

print("=== 1. Очистка старых/некорректных сьютов в Qase ===")
r_suites = requests.get(f"{qase_url}/suite/{code}", headers=headers)
existing_suites = r_suites.json().get('result', {}).get('entities', []) if r_suites.ok else []

# Delete old test cases first
r_cases = requests.get(f"{qase_url}/case/{code}?limit=100", headers=headers)
if r_cases.ok:
    for c in r_cases.json().get('result', {}).get('entities', []):
        requests.delete(f"{qase_url}/case/{code}/{c['id']}", headers=headers)
        print(f"Удален некорректный кейс {c['id']}")

# Delete old child suites under Frontend (like 76, 77)
for s in existing_suites:
    if s.get('parent_id') is not None or s['title'] in ['Frontend', 'Backend']:
        requests.delete(f"{qase_url}/suite/{code}/{s['id']}", headers=headers)
        print(f"Удален старый сьют {s['id']}: {s['title']}")

print("\n=== 2. Создание правильной иерархии папок (API, UI, E2E) ===")
def get_or_create_suite(title, parent_id=None):
    payload = {"title": title}
    if parent_id:
        payload["parent_id"] = parent_id
    res = requests.post(f"{qase_url}/suite/{code}", headers=headers, json=payload)
    if res.ok:
        sid = res.json()['result']['id']
        print(f"Создан сьют '{title}' -> ID: {sid} (parent: {parent_id})")
        return sid
    else:
        print(f"Ошибка создания '{title}':", res.text)
        return None

# Корневые папки слоев пирамиды
api_root_id = get_or_create_suite("API")
ui_root_id = get_or_create_suite("UI")
e2e_root_id = get_or_create_suite("E2E")

# Дочерние папки под конкретные инженерные задачи
js40_suite_id = get_or_create_suite("JS-40: [API] Реализация серверной логики и контрактов регистрации (POST /api/Users)", parent_id=api_root_id)
js41_suite_id = get_or_create_suite("JS-41: [UI] Разработка клиентской формы регистрации и валидации полей (/#/register)", parent_id=ui_root_id)
js42_suite_id = get_or_create_suite("JS-42: [E2E] Сквозная интеграция, приемочные сценарии и онбординг нового покупателя", parent_id=e2e_root_id)

print("\n=== 3. Создание профессиональных тест-кейсов для JS-40 (API) ===")
# Названия тест-кейсов по лучшим практикам тест-дизайна, коррелирующие с автотестами Pytest
js40_cases = [
    {
        "title": "[API][POST /api/Users] Регистрация нового покупателя с валидными параметрами (201 Created)",
        "suite_id": js40_suite_id,
        "severity": 1, # Blocker
        "priority": 1, # High
        "type": 1, # Functional
        "behavior": 1, # Positive
        "automation": 2, # To be automated
        "description": "Проверка создания учетной записи пользователя через REST API с уникальным email и паролем. Проверяется статус 201 Created и схема ответа UserRegistrationResponse.",
        "preconditions": "Сервер Juice Shop активен на http://localhost:3000",
        "steps": [
            {
                "action": "Отправить HTTP POST /api/Users/ с телом: email, password, passwordRepeat, securityQuestion, securityAnswer",
                "expected_result": "HTTP статус 201 Created, тело ответа содержит status='success' и данные пользователя с role='customer', isActive=true"
            }
        ]
    },
    {
        "title": "[API][GET /api/SecurityQuestions] Получение полного справочника контрольных вопросов (200 OK)",
        "suite_id": js40_suite_id,
        "severity": 2, # Critical
        "priority": 1, # High
        "type": 1, # Functional
        "behavior": 1, # Positive
        "automation": 2,
        "description": "Проверка доступности справочника секретных вопросов для формы регистрации.",
        "steps": [
            {
                "action": "Отправить HTTP GET /api/SecurityQuestions/",
                "expected_result": "HTTP статус 200 OK, в теле возвращается массив из 14 доступных секретных вопросов"
            }
        ]
    },
    {
        "title": "[API][POST /api/Users] Отказ в регистрации при дубликате Email (400 Bad Request)",
        "suite_id": js40_suite_id,
        "severity": 2, # Critical
        "priority": 1, # High
        "type": 2, # Negative
        "behavior": 2, # Negative
        "automation": 2,
        "description": "Проверка бизнес-правила BR-AUTH-01: запрет создания пользователей с одинаковым email (уникальность email в БД).",
        "preconditions": "Пользователь с указанным email уже существует в базе данных",
        "steps": [
            {
                "action": "Отправить HTTP POST /api/Users/ с уже зарегистрированным email",
                "expected_result": "HTTP статус 400 Bad Request, сообщение об ошибке содержит 'email must be unique'"
            }
        ]
    },
    {
        "title": "[API][POST /api/Users] Валидация запрета пустых значений Email и пароля (400 Bad Request)",
        "suite_id": js40_suite_id,
        "severity": 3, # Major
        "priority": 2, # Medium
        "type": 2, # Negative
        "behavior": 2, # Negative
        "automation": 2,
        "description": "Проверка бизнес-правила BR-AUTH-05: запрет отправки пустых строк в полях email или password.",
        "steps": [
            {
                "action": "Отправить HTTP POST /api/Users/ с email='' или password=''",
                "expected_result": "HTTP статус 400 Bad Request, тело ответа содержит 'Invalid email/password cannot be empty'"
            }
        ]
    },
    {
        "title": "[API][POST /api/SecurityAnswers] Сохранение ответа на контрольный вопрос пользователя (201 Created)",
        "suite_id": js40_suite_id,
        "severity": 2, # Critical
        "priority": 1, # High
        "type": 9, # Integration
        "behavior": 1, # Positive
        "automation": 2,
        "description": "Проверка создания связки UserId, SecurityQuestionId и ответа в таблице SecurityAnswers.",
        "steps": [
            {
                "action": "Отправить HTTP POST /api/SecurityAnswers/ с телом: UserId, SecurityQuestionId, answer",
                "expected_result": "HTTP статус 201 Created, ответ сохранен в БД в связке с UserId"
            }
        ]
    },
    {
        "title": "[API][Security][POST /api/Users] Назначение роли администратора через Mass Assignment (registerAdminChallenge)",
        "suite_id": js40_suite_id,
        "severity": 2, # Critical
        "priority": 1, # High
        "type": 4, # Security
        "behavior": 3, # Destructive
        "automation": 2,
        "description": "Верификация уязвимости Mass Assignment: передача параметра role='admin' при регистрации создает учетную запись администратора и решает челлендж registerAdminChallenge.",
        "steps": [
            {
                "action": "Отправить HTTP POST /api/Users/ с телом, содержащим role: 'admin'",
                "expected_result": "Пользователь создан с role='admin', назначен аватар defaultAdmin.png, челлендж решен"
            }
        ]
    }
]

for c in js40_cases:
    res = requests.post(f"{qase_url}/case/{code}", headers=headers, json=c)
    if res.ok:
        cid = res.json()['result']['id']
        print(f"  [+] Создан кейс {cid}: {c['title']}")
    else:
        print(f"  [-] Ошибка создания кейса '{c['title']}':", res.text)

print("\n=== 4. Отправка Telegram уведомления в бот ===")
from scripts.telegram_notifier import notify_pipeline_started, notify_gate1_waiting
notify_pipeline_started("JS-40", "[API] Реализация серверной логики и контрактов регистрации (POST /api/Users)")
notify_gate1_waiting("JS-40", bdd_count=len(js40_cases), rtm_count=len(js40_cases))
print("Уведомление в Telegram успешно отправлено!")
