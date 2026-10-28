import os
import sys
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

token = os.getenv("QASE_API_TOKEN")
headers = {"Token": token, "Content-Type": "application/json"}

s_res = requests.get("https://api.qase.io/v1/suite/JS?limit=100", headers=headers)
existing_suites = s_res.json().get("result", {}).get("entities", [])
suite_id = None
for s in existing_suites:
    if "JS-40" in s.get("title", "").upper():
        suite_id = s["id"]
        print(f"Found existing suite #{suite_id}: {s.get('title')}")
        break

if not suite_id:
    r_create = requests.post("https://api.qase.io/v1/suite/JS", headers=headers, json={"title": "JS-40: API Registration", "description": "Backend API test cases for JS-40 (POST /api/Users)"})
    suite_id = r_create.json().get("result", {}).get("id")
    print(f"Created suite #{suite_id}: JS-40: API Registration")

cases = [
    {
        "title": "[API][Parametrized] Создание учетной записи пользователя через POST /api/Users/",
        "description": "Given valid email and password, When client sends POST /api/Users/, Then returns 201 Created with user id and role customer (AC-API-01)",
        "preconditions": "Сервер Juice Shop запущен на http://localhost:3000",
        "suite_id": suite_id,
        "automation": 1,
        "priority": 1,
        "tags": ["smoke", "regress", "to-be-automated"],
        "steps": [
            {"action": "Подготовить валидный email и пароль", "expected_result": "Данные сформированы"},
            {"action": "Отправить POST /api/Users/", "expected_result": "Статус ответа 201 Created"},
            {"action": "Валидировать Pydantic схему UserRegistrationResponse", "expected_result": "Схема валидна, role=customer"}
        ]
    },
    {
        "title": "[API] Возврат ошибки 400 Bad Request при попытке создания дубликата Email в POST /api/Users/",
        "description": "Given existing user in DB, When client registers again with same email, Then server returns HTTP 400 Bad Request email must be unique (AC-API-02)",
        "preconditions": "Пользователь с email уже зарегистрирован в системе",
        "suite_id": suite_id,
        "automation": 1,
        "priority": 2,
        "tags": ["regress", "to-be-automated"],
        "steps": [
            {"action": "Отправить повторный POST /api/Users/ с существующим email", "expected_result": "HTTP 400 Bad Request"},
            {"action": "Проверить текст ошибки в ответе", "expected_result": "Сообщение содержит email must be unique"}
        ]
    },
    {
        "title": "[API][Parametrized] Валидация обязательных полей (пустой email/password) в POST /api/Users/",
        "description": "Given empty email or password, When client sends POST /api/Users/, Then server returns 400 Bad Request (AC-API-03)",
        "preconditions": "Сервер Juice Shop доступен",
        "suite_id": suite_id,
        "automation": 1,
        "priority": 2,
        "tags": ["regress", "to-be-automated"],
        "steps": [
            {"action": "Отправить POST /api/Users/ с пустым email или паролем", "expected_result": "HTTP 400 Bad Request"},
            {"action": "Проверить валидацию обязательных полей", "expected_result": "Пользователь не создан в БД"}
        ]
    },
    {
        "title": "[API] Санитизация пробелов в начале и конце email перед сохранением в БД",
        "description": "Given email with leading and trailing spaces, When client sends POST /api/Users/, Then server trims spaces (AC-API-04)",
        "preconditions": "Сервер Juice Shop доступен",
        "suite_id": suite_id,
        "automation": 1,
        "priority": 2,
        "tags": ["regress", "to-be-automated"],
        "steps": [
            {"action": "Отправить POST /api/Users/ с email с пробелами", "expected_result": "HTTP 201 Created"},
            {"action": "Проверить email созданной записи в ответе", "expected_result": "Email очищен от пробелов"}
        ]
    },
    {
        "title": "[API] Привязка контрольного вопроса и ответа через POST /api/SecurityAnswers/",
        "description": "Given created user and security question id, When client sends POST /api/SecurityAnswers/, Then returns 201 Created (AC-API-05)",
        "preconditions": "Пользователь зарегистрирован, справочник вопросов доступен",
        "suite_id": suite_id,
        "automation": 1,
        "priority": 2,
        "tags": ["regress", "to-be-automated"],
        "steps": [
            {"action": "Отправить POST /api/SecurityAnswers/ с UserId и SecurityQuestionId", "expected_result": "HTTP 201 Created"},
            {"action": "Проверить сохранение ответа в БД", "expected_result": "Секретный ответ сохранен в хэшированном виде"}
        ]
    },
    {
        "title": "[API] Получение справочника из 14 контрольных вопросов через GET /api/SecurityQuestions/",
        "description": "When client sends GET /api/SecurityQuestions/, Then server returns HTTP 200 OK and array of 14 questions (AC-API-06)",
        "preconditions": "Сервер Juice Shop запущен",
        "suite_id": suite_id,
        "automation": 1,
        "priority": 1,
        "tags": ["smoke", "regress", "to-be-automated"],
        "steps": [
            {"action": "Отправить GET /api/SecurityQuestions/", "expected_result": "HTTP 200 OK"},
            {"action": "Проверить структуру ответа и количество вопросов", "expected_result": "Массив содержит 14 объектов с id и question"}
        ]
    }
]

cur_cases = requests.get(f"https://api.qase.io/v1/case/JS?suite_id={suite_id}&limit=100", headers=headers).json().get("result", {}).get("entities", [])
cur_titles = {c["title"]: c["id"] for c in cur_cases}
for c in cases:
    if c["title"] not in cur_titles:
        r = requests.post("https://api.qase.io/v1/case/JS", headers=headers, json=c)
        cid = r.json().get("result", {}).get("id")
        print(f"Created case #{cid}: {c['title'][:50]}")
    else:
        print(f"Case exists #{cur_titles[c['title']]}: {c['title'][:50]}")
