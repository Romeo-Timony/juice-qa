import sys
sys.path.insert(0, '.')
from qaops.design_gate import run_design_gate, deterministic_review
from qaops.judge import judge_coverage

# Define the 12 registration cases
cases = [
    {
        "id": 1,
        "title": "[API][Parametrized] Успешная регистрация пользователя через POST /api/Users/ с валидным payload",
        "description": "Проверка создания пользователя в POST /api/Users с email, паролем и контрольным вопросом.",
        "automation": 1,
        "priority": 1,
        "severity": 1,
        "tags": [{"title": "smoke"}, {"title": "bdd"}, {"title": "allure"}, {"title": "api"}],
        "steps": [
            {"action": "POST /api/Users/", "data": '{"email": "valid@juice-sh.op", "password": "ValidPassword123"}', "expected_result": "HTTP 201 Created, status: success"}
        ]
    },
    {
        "id": 2,
        "title": "[API] Возврат ошибки 409 Conflict при попытке создания дубликата Email в POST /api/Users/",
        "description": "Проверка уникальности email в БД: повторная регистрация возвращает 409 Conflict.",
        "automation": 1,
        "priority": 1,
        "severity": 1,
        "tags": [{"title": "negative"}, {"title": "regression"}, {"title": "api"}],
        "steps": [
            {"action": "POST /api/Users/ с существующим email", "data": "admin@juice-sh.op", "expected_result": "HTTP 409 Conflict или 400 Bad Request, email must be unique"}
        ]
    },
    {
        "id": 3,
        "title": "[API][Parametrized] Валидация схемы payload и минимальной длины пароля в POST /api/Users/",
        "description": "Проверка обязательности полей и длины пароля не менее 5 символов.",
        "automation": 1,
        "priority": 1,
        "severity": 2,
        "tags": [{"title": "validation"}, {"title": "regression"}, {"title": "api"}],
        "steps": [
            {"action": "POST /api/Users/ с коротким паролем '1234'", "data": "pass: 1234", "expected_result": "HTTP 400 Bad Request"}
        ]
    },
    {
        "id": 4,
        "title": "[API] Санитизация и нормализация email: удаление начальных и конечных пробелов trim",
        "description": "Проверка санитизации email: пробелы удаляются перед сохранением в БД.",
        "automation": 1,
        "priority": 2,
        "severity": 2,
        "tags": [{"title": "regression"}, {"title": "api"}],
        "steps": [
            {"action": "POST /api/Users/ с email '  user@juice-sh.op  '", "data": "trimmed email", "expected_result": "HTTP 201, в БД сохранен 'user@juice-sh.op'"}
        ]
    },
    {
        "id": 5,
        "title": "[API] Привязка контрольного вопроса и ответа при регистрации пользователя (SecurityAnswer)",
        "description": "Проверка связи пользователя с контрольным вопросом через POST /api/SecurityAnswers/.",
        "automation": 1,
        "priority": 1,
        "severity": 1,
        "tags": [{"title": "smoke"}, {"title": "api"}],
        "steps": [
            {"action": "POST /api/SecurityAnswers/", "data": "UserId, SecurityQuestionId, answer", "expected_result": "HTTP 201 Created, контрольный ответ сохранен"}
        ]
    },
    {
        "id": 6,
        "title": "[API] Получение справочника доступных контрольных вопросов GET /api/SecurityQuestions",
        "description": "Проверка эндпоинта получения справочника вопросов безопасности.",
        "automation": 1,
        "priority": 2,
        "severity": 2,
        "tags": [{"title": "smoke"}, {"title": "api"}],
        "steps": [
            {"action": "GET /api/SecurityQuestions", "data": "empty query", "expected_result": "HTTP 200 OK, массив доступных вопросов"}
        ]
    },
    {
        "id": 7,
        "title": "[API] Проверка хеширования пароля в SQLite БД — пароль не хранится в открытом виде",
        "description": "Верификация того, что пароль хешируется (bcrypt/md5) и не сохраняется plain-text в БД.",
        "automation": 1,
        "priority": 1,
        "severity": 1,
        "tags": [{"title": "security"}, {"title": "regression"}, {"title": "api"}],
        "steps": [
            {"action": "Проверка записи в таблице Users после регистрации", "data": "SQL SELECT password", "expected_result": "Хеш пароля вместо открытого текста"}
        ]
    },
    {
        "id": 8,
        "title": "[API] Проверка хеширования ответа на контрольный вопрос (SecurityAnswer) в базе данных",
        "description": "Проверка криптографического хеширования секретного ответа пользователя.",
        "automation": 1,
        "priority": 2,
        "severity": 2,
        "tags": [{"title": "security"}, {"title": "regression"}, {"title": "api"}],
        "steps": [
            {"action": "Проверка записи в таблице SecurityAnswers", "data": "SQL SELECT answer", "expected_result": "Хеш ответа вместо открытого текста"}
        ]
    },
    {
        "id": 9,
        "title": "[API] Отказ в регистрации при передаче несуществующего SecurityQuestionId",
        "description": "Проверка внешнего ключа и валидации ID контрольного вопроса.",
        "automation": 1,
        "priority": 2,
        "severity": 2,
        "tags": [{"title": "negative"}, {"title": "regression"}, {"title": "api"}],
        "steps": [
            {"action": "POST /api/SecurityAnswers/ с SecurityQuestionId=99999", "data": "Invalid ID", "expected_result": "HTTP 400 или 404"}
        ]
    },
    {
        "id": 10,
        "title": "[API] Валидация пустых обязательных полей (email, password) при регистрации в POST /api/Users/",
        "description": "Проверка отклонения регистрации с пустыми строками в полях email или password (AC-API-03).",
        "automation": 1,
        "priority": 1,
        "severity": 1,
        "tags": [{"title": "validation"}, {"title": "regression"}, {"title": "api"}],
        "steps": [
            {"action": "POST /api/Users/ с пустыми строками email: '', password: ''", "data": "Empty fields", "expected_result": "HTTP 400 Bad Request, сообщение об ошибке валидации"}
        ]
    },
    {
        "id": 11,
        "title": "[API] Валидация некорректного формата Email адреса при регистрации в POST /api/Users/",
        "description": "Проверка валидации формата email (RFC 5322).",
        "automation": 1,
        "priority": 2,
        "severity": 2,
        "tags": [{"title": "negative"}, {"title": "regression"}, {"title": "api"}],
        "steps": [
            {"action": "POST /api/Users/ с email 'invalid_email_format'", "data": "invalid email", "expected_result": "HTTP 400 Bad Request, сообщение о невалидном email"}
        ]
    },
    {
        "id": 12,
        "title": "[API] Проверка маскирования пароля в теле ответа после успешной регистрации",
        "description": "Проверка утечки учетных данных: пароль отсутствует в теле ответа сервера.",
        "automation": 1,
        "priority": 1,
        "severity": 1,
        "tags": [{"title": "security"}, {"title": "smoke"}, {"title": "api"}],
        "steps": [
            {"action": "POST /api/Users/", "data": "Valid registration", "expected_result": "res.data.id определен, res.data.password не возвращается"}
        ]
    }
]

print("1. Deterministic check on 12 cases:")
for c in cases:
    r = deterministic_review(c)
    assert r.deterministic_ok, f"Case {c['id']} failed deterministic: {r.reasons}"
print("   All 12 cases passed deterministic review!")

print("2. Running full run_design_gate with LLM-as-a-Judge...")
res = run_design_gate("JS-40", cases, use_llm=True)
print(f"   Integrity: {res.integrity:.1%}, Passed count: {res.passed_count}/{res.total}, Gate passed: {res.gate_passed}")
if res.coverage:
    print(f"   Coverage: {res.coverage.get('score')}, Reason: {res.coverage.get('reason')}")
for r in res.reviews:
    if not r.passed:
        print(f"   FAILED: #{r.id} {r.title} - {r.reasons}")
