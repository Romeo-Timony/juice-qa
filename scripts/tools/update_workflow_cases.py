import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv('.env')

N8N_URL = os.getenv('N8N_BASE_URL', 'http://201.34.147.33:5678').rstrip('/')
N8N_KEY = os.getenv('N8N_API_KEY')
WORKFLOW_ID = 'Dv1WydaTMC1lxR0E'

NEW_BACKEND_CASES_JS = '''const defaultBackendCases = [
  {
    id: 'TC-BE-01',
    title: '[API][Parametrized] Успешная регистрация пользователя через POST /api/Users/ с валидным payload',
    description: 'Интеграционный API тест создания пользователя с валидными данными, хешированием пароля и связью с SecurityQuestion (AC-API-01). 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: User Registration")
@allure.severity("critical")
@fast-regression
@full-regression
Scenario Outline: Успешное создание пользователя через REST API
  Given API клиент отправляет POST-запрос на эндпоинт "/api/Users/"
  When тело запроса содержит валидный JSON с email "<email>", password "<password>", securityQuestionId <q_id>, answer "<answer>"
  Then сервер возвращает HTTP статус 201 Created
  And тело ответа содержит статус "success" и сгенерированный ID пользователя
  And в объекте ответа пароль пользователя отсутствует или замаскирован
  And в базе данных SQLite создана запись со значением хеша пароля

  Examples:
    | email                         | password        | q_id | answer       |
    | api.user1@juice-sh.op         | SecurePass123!  | 1    | SecretOne    |
    | api.service.user@juice-sh.op  | ComplexPass888# | 2    | SecretTwo    |
    | api.partner.test@juice-sh.op  | P@ssword2026$   | 3    | SecretThree  |`,
    covers: ['AC-API-01', 'BE-01', 'API-01'],
    type: 'smoke',
    severity: 'critical',
    priority: 'high',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'backend', 'supertest', 'smoke', 'parametrized', 'fast-regression', 'full-regression'],
    preconditions: 'Сервер Juice Shop запущен, SQLite БД инициализирована.',
    steps: [
      { action: '[Given] Сформировать HTTP POST запрос на /api/Users/', data: 'Endpoint: POST /api/Users/', expected_result: 'Запрос готов к отправке' },
      { action: '[When] Отправить валидный JSON payload', data: 'email: <email>, pass: <password>, qId: <q_id>, ans: <answer>', expected_result: 'Сервер возвращает HTTP 201 Created' },
      { action: '[Then] Проверить структуру ответа', data: 'Assertion: res.body.status === "success"', expected_result: 'res.body.data.id определен, password не передается в открытом виде' }
    ],
    postconditions: 'Запись пользователя добавлена в таблицу Users.'
  },
  {
    id: 'TC-BE-02',
    title: '[API] Возврат ошибки 409 Conflict при попытке создания дубликата Email в POST /api/Users/',
    description: 'Проверка уникального индекса email на уровне базы данных SQLite и ответа 409 Conflict при попытке повторной регистрации (AC-API-02). 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: User Creation Constraints")
@allure.severity("critical")
@full-regression
Scenario: Отказ в регистрации при существующем Email
  Given в базе данных уже существует запись с email "admin@juice-sh.op"
  When клиент отправляет POST-запрос на "/api/Users/" с email "admin@juice-sh.op"
  Then сервер возвращает HTTP статус 409 Conflict или 400 Bad Request
  And тело ответа содержит ошибку "Email must be unique."
  And количество записей в таблице Users не увеличивается`,
    covers: ['AC-API-02', 'BE-01', 'DB-01'],
    type: 'functional',
    severity: 'critical',
    priority: 'high',
    layer: 'api',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'backend', 'db-constraint', 'full-regression'],
    preconditions: 'Пользователь admin@juice-sh.op существует в базе.',
    steps: [
      { action: '[Given] Подготовить payload с существующим email', data: 'email: "admin@juice-sh.op"', expected_result: 'Payload готов' },
      { action: '[When] Выполнить POST /api/Users/', data: 'Supertest POST request', expected_result: 'HTTP 409 Conflict или 400 Bad Request' },
      { action: '[Then] Проверить сообщение об ошибке валидации', data: 'res.body.error', expected_result: 'Содержит сообщение об уникальности email' }
    ],
    postconditions: 'Целостность базы данных не нарушена.'
  },
  {
    id: 'TC-BE-03',
    title: '[API][Parametrized] Валидация схемы payload и минимальной длины пароля в POST /api/Users/',
    description: 'Data-driven проверка схемы JSON и валидаторов модели Sequelize: длина пароля от 5 символов (AC-API-03). 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: User Validation")
@allure.severity("major")
@full-regression
Scenario Outline: Валидация невалидных параметров регистрации на бэкенде
  Given API клиент отправляет POST-запрос на "/api/Users/"
  When тело запроса содержит email "<email>" и пароль "<password>"
  Then сервер возвращает HTTP статус-код <expected_status>
  And тело ответа содержит описание ошибки валидации

  Examples:
    | email                 | password | expected_status |
    | invalid-email-format  | Pass1234 | 400             |
    | valid@juice-sh.op     | 1234     | 400             |
    |                       | Pass1234 | 400             |`,
    covers: ['AC-API-03', 'BE-01', 'API-01'],
    type: 'functional',
    severity: 'major',
    priority: 'high',
    layer: 'api',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'validation', 'parametrized', 'full-regression'],
    preconditions: 'API сервер доступен.',
    steps: [
      { action: '[When] Отправить некорректный payload', data: 'email: <email>, pass: <password>', expected_result: 'HTTP статус <expected_status>' },
      { action: '[Then] Проверить статус и отсутствие записи в БД', data: 'Assertion HTTP 400', expected_result: 'Ошибка валидации схемы' }
    ],
    postconditions: 'БД не изменена.'
  },
  {
    id: 'TC-BE-04',
    title: '[API] Санитизация и нормализация email: удаление начальных и конечных пробелов trim',
    description: 'Проверка санитизации email: пробелы в начале и конце автоматически удаляются перед сохранением в SQLite (AC-API-04). 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: Email Sanitization")
@allure.severity("major")
@fast-regression
Scenario: Нормализация email с пробелами
  Given клиент отправляет POST на "/api/Users/" с email "  trimmed.user@juice-sh.op  "
  When сервер обрабатывает запрос регистрации
  Then email санитизируется и сохраняется как "trimmed.user@juice-sh.op"
  And HTTP статус равен 201 Created`,
    covers: ['AC-API-04', 'BE-01'],
    type: 'functional',
    severity: 'major',
    priority: 'medium',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'sanitization', 'fast-regression'],
    preconditions: 'API сервер доступен.',
    steps: [
      { action: '[When] Отправить POST /api/Users/ с пробелами в email', data: 'email: "  trimmed.user@juice-sh.op  "', expected_result: 'HTTP 201 Created' },
      { action: '[Then] Проверить сохраненный email в БД', data: 'SELECT email FROM Users', expected_result: 'email сохранен без пробелов' }
    ],
    postconditions: 'Пользователь сохранен с нормализованным email.'
  },
  {
    id: 'TC-BE-05',
    title: '[API] Привязка контрольного вопроса и ответа при регистрации пользователя (SecurityAnswer)',
    description: 'Проверка создания записи в таблице SecurityAnswers и привязки к UserId при регистрации (AC-API-05). 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: Security Question Binding")
@allure.severity("critical")
@fast-regression
Scenario: Привязка контрольного вопроса к пользователю
  Given клиент отправляет POST /api/SecurityAnswers/ с валидным UserId и SecurityQuestionId
  When запрос обрабатывается сервером
  Then сервер возвращает HTTP статус 201 Created
  And запись успешно связывается с аккаунтом пользователя`,
    covers: ['AC-API-05', 'BE-01', 'SEC-01'],
    type: 'smoke',
    severity: 'critical',
    priority: 'high',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'security-question', 'smoke', 'fast-regression'],
    preconditions: 'Пользователь зарегистрирован в системе.',
    steps: [
      { action: '[When] Отправить POST /api/SecurityAnswers/', data: 'UserId, SecurityQuestionId, answer', expected_result: 'HTTP 201 Created' },
      { action: '[Then] Проверить ответ сервера', data: 'res.body.status === "success"', expected_result: 'Контрольный вопрос успешно привязан' }
    ],
    postconditions: 'Связка SecurityAnswer создана.'
  },
  {
    id: 'TC-BE-06',
    title: '[API] Получение справочника доступных контрольных вопросов GET /api/SecurityQuestions',
    description: 'Проверка эндпоинта получения справочника контрольных вопросов для формы регистрации (AC-API-06). 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: Security Questions Directory")
@allure.severity("normal")
@fast-regression
Scenario: Получение списка контрольных вопросов
  Given API клиент отправляет GET-запрос на "/api/SecurityQuestions"
  When сервер возвращает ответ
  Then HTTP статус равен 200 OK
  And тело ответа содержит непустой массив вопросов безопасности с полями id и question`,
    covers: ['AC-API-06', 'BE-01'],
    type: 'smoke',
    severity: 'normal',
    priority: 'medium',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'directory', 'smoke', 'fast-regression'],
    preconditions: 'Таблица SecurityQuestions заполнена фикстурами.',
    steps: [
      { action: '[When] Отправить GET /api/SecurityQuestions', data: 'GET request', expected_result: 'HTTP 200 OK' },
      { action: '[Then] Проверить структуру элементов', data: 'Array of {id, question}', expected_result: 'Массив содержит > 0 элементов' }
    ],
    postconditions: 'Справочник доступен клиенту.'
  },
  {
    id: 'TC-BE-07',
    title: '[API] Проверка хеширования пароля в SQLite БД — пароль не хранится в открытом виде',
    description: 'Проверка безопасности хранения учетных данных: пароль хешируется (MD5/bcrypt) перед записью в SQLite (AC-API-07). 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend Security")
@allure.story("${ctx.issueKey}: Password Hashing Security")
@allure.severity("blocker")
@full-regression
Scenario: Верификация хеширования пароля в базе данных
  Given новый пользователь зарегистрирован с паролем "RawSecretPass999!"
  When выполняется прямой запрос в SQLite таблицу Users
  Then поле password содержит криптографический хеш
  And исходный открытый пароль "RawSecretPass999!" нигде не сохраняется в открытом виде`,
    covers: ['AC-API-07', 'BE-01', 'SEC-02'],
    type: 'security',
    severity: 'blocker',
    priority: 'high',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'security', 'hashing', 'owasp', 'full-regression'],
    preconditions: 'Пользователь зарегистрирован через API.',
    steps: [
      { action: '[When] Зарегистрировать пользователя через POST /api/Users/', data: 'Raw password', expected_result: 'HTTP 201' },
      { action: '[Then] Проверить значение пароля в таблице Users', data: 'SELECT password FROM Users', expected_result: 'Значение является хешем, не равно исходному паролю' }
    ],
    postconditions: 'Пароль надежно захеширован.'
  },
  {
    id: 'TC-BE-08',
    title: '[API] Проверка хеширования ответа на контрольный вопрос (SecurityAnswer) в базе данных',
    description: 'Проверка безопасности ответа на контрольный вопрос: значение answer хешируется перед сохранением в SQLite (AC-API-05, AC-API-07). 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend Security")
@allure.story("${ctx.issueKey}: Security Answer Hashing")
@allure.severity("critical")
@full-regression
Scenario: Хеширование ответа на контрольный вопрос
  Given пользователь сохраняет ответ на контрольный вопрос "SecretMomMaiden"
  When запись добавляется в таблицу SecurityAnswers
  Then поле answer в базе данных содержит хеш
  And ответ в открытом виде не доступен в БД`,
    covers: ['AC-API-05', 'AC-API-07', 'SEC-02'],
    type: 'security',
    severity: 'critical',
    priority: 'high',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'security', 'hashing', 'full-regression'],
    preconditions: 'SecurityAnswer сохранен для пользователя.',
    steps: [
      { action: '[When] Проверить запись в таблице SecurityAnswers', data: 'SELECT answer FROM SecurityAnswers', expected_result: 'answer является хешем' },
      { action: '[Then] Убедиться в отсутствии открытого текста', data: 'answer != "SecretMomMaiden"', expected_result: 'Хеширование подтверждено' }
    ],
    postconditions: 'Контрольный ответ защищен хешированием.'
  },
  {
    id: 'TC-BE-09',
    title: '[API] Отказ в регистрации при передаче несуществующего SecurityQuestionId',
    description: 'Проверка целостности внешних ключей: возврат ошибки при попытке указать несуществующий SecurityQuestionId (AC-API-05). 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: Foreign Key Integrity")
@allure.severity("major")
@full-regression
Scenario: Регистрация с несуществующим вопросом безопасности
  Given клиент отправляет запрос с securityQuestionId 999999
  When запрос обрабатывается бэкендом
  Then сервер возвращает HTTP статус 400 Bad Request или 404 Not Found
  And запись с некорректным внешним ключом не создается`,
    covers: ['AC-API-05', 'BE-01'],
    type: 'functional',
    severity: 'major',
    priority: 'medium',
    layer: 'api',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'validation', 'negative', 'full-regression'],
    preconditions: 'Вопрос с ID 999999 отсутствует в справочнике.',
    steps: [
      { action: '[When] Отправить POST /api/SecurityAnswers/ с questionId=999999', data: 'Invalid foreign key', expected_result: 'HTTP 400 или 404' },
      { action: '[Then] Проверить целостность БД', data: 'Запись не добавлена', expected_result: 'Целостность связей сохранена' }
    ],
    postconditions: 'Некорректная запись отклонена.'
  },
  {
    id: 'TC-BE-10',
    title: '[API] Валидация пустых обязательных полей (email, password) при регистрации в POST /api/Users/',
    description: 'Проверка валидации обязательных полей: отклонение пустых строк в email или password с кодом 400 (AC-API-03). 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: Required Fields Validation")
@allure.severity("critical")
@full-regression
Scenario: Отклонение регистрации с пустыми обязательными полями
  Given API клиент отправляет POST на "/api/Users/" с пустым email "" или пустым password ""
  When сервер проверяет входной payload
  Then сервер возвращает HTTP статус 400 Bad Request
  And запись пользователя не создается в базе данных`,
    covers: ['AC-API-03', 'BE-01'],
    type: 'functional',
    severity: 'critical',
    priority: 'high',
    layer: 'api',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'validation', 'negative', 'full-regression'],
    preconditions: 'API сервер запущен.',
    steps: [
      { action: '[When] Отправить POST /api/Users/ с email: "", password: ""', data: 'Empty strings', expected_result: 'HTTP 400 Bad Request' },
      { action: '[Then] Проверить сообщение валидации', data: 'res.body.error', expected_result: 'Содержит описание незаполненных полей' }
    ],
    postconditions: 'Пустые записи не попадают в БД.'
  },
  {
    id: 'TC-BE-11',
    title: '[API] Валидация некорректного формата Email адреса при регистрации в POST /api/Users/',
    description: 'Проверка регулярных выражений валидации email: отклонение адресов без домена или @ с кодом 400 (AC-API-03). 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: Email Format Validation")
@allure.severity("major")
@full-regression
Scenario: Отклонение некорректного формата Email
  Given клиент отправляет POST на "/api/Users/" с email "not-an-email-address"
  When Sequelize валидирует email формат
  Then сервер возвращает HTTP статус 400 Bad Request
  And сообщение об ошибке указывает на некорректный формат email`,
    covers: ['AC-API-03', 'BE-01'],
    type: 'functional',
    severity: 'major',
    priority: 'high',
    layer: 'api',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'validation', 'email', 'full-regression'],
    preconditions: 'API сервер запущен.',
    steps: [
      { action: '[When] Отправить POST /api/Users/ с невалидным email', data: 'email: "not-an-email-address"', expected_result: 'HTTP 400 Bad Request' },
      { action: '[Then] Проверить статус ответа', data: 'res.status === 400', expected_result: 'Ошибка валидации email' }
    ],
    postconditions: 'Невалидный email отклонен.'
  },
  {
    id: 'TC-BE-12',
    title: '[API] Проверка маскирования пароля в теле ответа после успешной регистрации',
    description: 'Проверка защиты от утечки чувствительных данных: поле password отсутствует или не возвращается в ответе POST /api/Users/ (AC-API-01, AC-API-07). 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend Security")
@allure.story("${ctx.issueKey}: Sensitive Data Exposure")
@allure.severity("critical")
@fast-regression
Scenario: Защита от утечки пароля в теле HTTP ответа
  Given клиент успешно зарегистрировал пользователя через POST /api/Users/
  When клиент анализирует JSON тело ответа сервера
  Then свойство res.body.data.password не определено или замаскировано
  And хеш или открытый пароль не передаются клиенту в ответе`,
    covers: ['AC-API-01', 'AC-API-07', 'SEC-01'],
    type: 'security',
    severity: 'critical',
    priority: 'high',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'security', 'masking', 'fast-regression'],
    preconditions: 'Регистрация выполнена успешно.',
    steps: [
      { action: '[When] Отправить валидный запрос регистрации POST /api/Users/', data: 'Valid credentials', expected_result: 'HTTP 201 Created' },
      { action: '[Then] Проверить тело ответа на отсутствие поля password', data: 'res.body.data.password === undefined', expected_result: 'Пароль отсутствует в ответе' }
    ],
    postconditions: 'Чувствительные данные защищены от утечки.'
  }
]'''

NEW_RTM_ROWS_JS = '''  if (isBackend) {
    lines.push('|*AC-API-01*|Эндпоинт POST /api/Users/: регистрация пользователя, валидация входных данных, хеширование пароля (MD5/Bcrypt), HTTP 201 Created|[TC-BE-01]|Успешная регистрация пользователя через POST /api/Users/ с валидным payload|API / Smoke|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-API-01*|Защита от утечки учетных данных: пароль отсутствует в теле HTTP ответа после регистрации|[TC-BE-12]|Проверка маскирования пароля в теле ответа после успешной регистрации|Security / Masking|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-API-02*|Контроль уникальности: запрет создания дубликатов email в таблице Users SQLite, возврат HTTP 409 Conflict|[TC-BE-02]|Возврат ошибки 409 Conflict при попытке создания дубликата Email в POST /api/Users/|API / Negative|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-API-03*|Валидация схемы payload: отклонение паролей менее 5 символов, возврат HTTP 400 Bad Request|[TC-BE-03]|Валидация схемы payload и минимальной длины пароля в POST /api/Users/|API / Validation|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-API-03*|Валидация обязательных полей: отклонение пустых строк email/password с кодом 400|[TC-BE-10]|Валидация пустых обязательных полей (email, password) при регистрации в POST /api/Users/|API / Validation|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-API-03*|Валидация некорректного формата email адреса при регистрации в POST /api/Users/|[TC-BE-11]|Валидация некорректного формата Email адреса при регистрации в POST /api/Users/|API / Validation|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-API-04*|Санитизация и нормализация email: автоматическое удаление начальных и конечных пробелов trim|[TC-BE-04]|Санитизация и нормализация email: удаление начальных и конечных пробелов trim|API / Sanitization|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-API-05*|Эндпоинт POST /api/SecurityAnswers/: сохранение и привязка контрольного ответа к UserId|[TC-BE-05]|Привязка контрольного вопроса и ответа при регистрации пользователя (SecurityAnswer)|API / Smoke|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-API-05*|Контроль внешних ключей: отказ в регистрации с несуществующим SecurityQuestionId|[TC-BE-09]|Отказ в регистрации при передаче несуществующего SecurityQuestionId|API / Negative|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-API-06*|Эндпоинт GET /api/SecurityQuestions: получение справочника доступных вопросов безопасности, HTTP 200 OK|[TC-BE-06]|Получение справочника доступных контрольных вопросов GET /api/SecurityQuestions|API / Directory|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-API-07*|Хеширование пароля в SQLite БД: пароль сохраняется в виде криптографического хеша (MD5/bcrypt)|[TC-BE-07]|Проверка хеширования пароля в SQLite БД — пароль не хранится в открытом виде|Security / Hashing|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-API-07*|Хеширование ответа на контрольный вопрос: поле answer в таблице SecurityAnswers защищено хешированием|[TC-BE-08]|Проверка хеширования ответа на контрольный вопрос (SecurityAnswer) в базе данных|Security / Hashing|API (Supertest)|(/) Покрыто (100%)|')
  }'''

print("1. Fetching active workflow from n8n API...")
req = urllib.request.Request(f"{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}", headers={"X-N8N-API-KEY": N8N_KEY})
with urllib.request.urlopen(req) as res:
    wf = json.loads(res.read().decode('utf-8'))

# Update node 'Создание тест-кейсов без повторов'
target_node = None
for node in wf.get('nodes', []):
    if node.get('name') == 'Создание тест-кейсов без повторов' or 'Создание тест-кейсов' in node.get('name', ''):
        target_node = node
        break

if not target_node:
    for node in wf.get('nodes', []):
        code = node.get('parameters', {}).get('jsCode', '')
        if 'defaultBackendCases' in code:
            target_node = node
            break

assert target_node, "Target node 'Создание тест-кейсов без повторов' not found!"
print(f"   Found target node: {target_node['name']}")

code = target_node['parameters']['jsCode']

# Replace defaultBackendCases
start_marker = "const defaultBackendCases = ["
end_marker = "const defaultStoryCases = ["
s_idx = code.find(start_marker)
e_idx = code.find(end_marker)
assert s_idx != -1 and e_idx != -1, f"Markers not found in code: {s_idx}, {e_idx}"

new_code = code[:s_idx] + NEW_BACKEND_CASES_JS + "\n\n" + code[e_idx:]

# Replace RTM table rows
rtm_start = "if (isBackend) {"
rtm_end = "} else if (isStory) {"
rs_idx = new_code.find(rtm_start)
re_idx = new_code.find(rtm_end)
assert rs_idx != -1 and re_idx != -1, f"RTM markers not found: {rs_idx}, {re_idx}"

final_code = new_code[:rs_idx] + NEW_RTM_ROWS_JS + new_code[re_idx + 1:]

target_node['parameters']['jsCode'] = final_code
print("   Updated jsCode in node definition successfully.")

# Push back to n8n
print("2. Pushing updated workflow to n8n Cloud API...")
update_payload = {
    "name": wf.get("name", "Juice Shop Enterprise QA Pipeline"),
    "nodes": wf.get("nodes", []),
    "connections": wf.get("connections", {}),
    "settings": wf.get("settings", {}),
}

req_put = urllib.request.Request(
    f"{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}",
    data=json.dumps(update_payload).encode('utf-8'),
    headers={"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"},
    method="PUT"
)

with urllib.request.urlopen(req_put) as res:
    resp_data = json.loads(res.read().decode('utf-8'))
    print(f"   ✅ n8n API response: status={res.status}, active={resp_data.get('active')}, nodes={len(resp_data.get('nodes', []))}")

# Also update local backup
with open('n8n/backups/n8n_backup_Dv1WydaTMC1lxR0E.json', 'w', encoding='utf-8') as f:
    json.dump(resp_data, f, ensure_ascii=False, indent=2)
print("   Saved backup to n8n/backups/n8n_backup_Dv1WydaTMC1lxR0E.json")
