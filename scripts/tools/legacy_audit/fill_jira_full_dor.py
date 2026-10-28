import os
import sys
import json
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')

u = os.getenv('ATLASSIAN_BASE_URL').rstrip('/')
a = (os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))

def set_description(issue_key, text):
    payload = {
        "fields": {
            "description": text
        }
    }
    r = requests.put(f"{u}/rest/api/2/issue/{issue_key}", auth=a, json=payload)
    if r.ok:
        print(f"Successfully updated description for {issue_key}")
    else:
        print(f"Error updating {issue_key}: {r.status_code}")
        print(r.text)

# Full rich DoR description for JS-40 [API]
api_dor = """h2. 1. Бизнес-контекст и цель задачи
*Бизнес-цель:* Реализовать серверную часть подсистемы регистрации пользователей (POST /api/Users/ и POST /api/SecurityAnswers/) интернет-магазина Juice Shop в соответствии с требованиями безопасности OWASP.
*Ценность для пользователя:* Надежное сохранение учетных записей клиентов, хэширование паролей и привязка контрольных секретных вопросов.

h2. 2. Границы скоупа (Scope)
* *Входит в скоуп (In-Scope):*
** REST эндпоинт POST /api/Users/ (создание пользователя, валидация уникальности email, санитизация пробелов).
** REST эндпоинт POST /api/SecurityAnswers/ (сохранение ответа на секретный вопрос со связкой UserId и SecurityQuestionId).
** REST эндпоинт GET /api/SecurityQuestions/ (справочник из 14 контрольных вопросов).
** Обработка ошибок бэкенда: 400 Bad Request при дубликатах email и пустых полях.
** Поддержка создания администратора при наличии флага role: 'admin' (соответствие registerAdminChallenge).
* *Не входит в скоуп (Out-of-Scope):*
** Клиентская форма Angular (роут /#/register) — выделена в задачу JS-41.
** Выпуск JWT-токенов и логин (POST /rest/user/login).

h2. 3. Архитектурный контекст и контракты REST API
* *Эндпоинты бэкенда:*
** POST /api/Users/ — Регистрация. Request: { email, password, passwordRepeat, securityQuestion: { id, question }, securityAnswer }. Response 201 Created: { status: 'success', data: { id, email, role: 'customer', isActive: true } }.
** POST /api/SecurityAnswers/ — Сохранение ответа. Request: { UserId, SecurityQuestionId, answer }. Response 201 Created.
** GET /api/SecurityQuestions/ — Справочник вопросов. Response 200 OK: { status: 'success', data: [{ id: 1..14, question }] }.
* *Связанная спецификация в Confluence:* https://romeo-timony.atlassian.net/wiki/pages/viewpage.action?pageId=3604481
* *Родительская история:* JS-39 (Регистрация нового покупателя через Email и пароль).

h2. 4. Бизнес-правила (Business Rules)
* *BR-AUTH-01 (Уникальность):* Email пользователя уникален в системе (case-insensitive). Дубликат возвращает HTTP 400 'email must be unique'.
* *BR-AUTH-02 (Длина пароля):* Хэширование пароля через bcrypt/HMAC на сервере.
* *BR-AUTH-03 (Контрольный вопрос):* Обязательная связка UserId с SecurityQuestionId в таблице SecurityAnswers.
* *BR-AUTH-04 (Санитизация):* Серверный trim() пробелов для email и паролей (server.ts).
* *BR-AUTH-05 (Валидация пустых строк):* Передача пустых email/password возвращает 400 'Invalid email/password cannot be empty'.

h2. 5. Критерии приемки (Acceptance Criteria / Gherkin)
{code:gherkin}
Scenario: Успешная регистрация пользователя через REST API
  When клиент отправляет POST /api/Users/ с уникальным email и паролем
  Then сервер возвращает HTTP 201 Created с объектом пользователя (role='customer', isActive=true)
  And связка ответа на секретный вопрос успешно сохраняется в POST /api/SecurityAnswers/

Scenario: Попытка регистрации дубликата email
  Given в БД уже есть пользователь с email "client@juice-sh.op"
  When клиент отправляет POST /api/Users/ с этим же email
  Then сервер возвращает HTTP 400 Bad Request с ошибкой "email must be unique"
{code}

h2. 6. Definition of Ready (DoR) Checklist
* [x] Бизнес-цель и границы задачи зафиксированы.
* [x] REST API контракты и схемы данных специфицированы.
* [x] Описаны коды ответов (201, 400) и бизнес-правила BR-AUTH-01 – BR-AUTH-05.
* [x] Страница Confluence привязана к задаче.
"""

# Full rich DoR description for JS-41 [UI]
ui_dor = """h2. 1. Бизнес-контекст и цель задачи
*Бизнес-цель:* Разработать клиентскую форму регистрации пользователей (/#/register) на Angular 21 для интернет-магазина Juice Shop.
*Ценность для пользователя:* Удобный интерфейс с мгновенной реактивной валидацией полей, подсказками стойкости пароля и защитой от некорректного ввода.

h2. 2. Границы скоупа (Scope)
* *Входит в скоуп (In-Scope):*
** Клиентская форма регистрации на роуте /#/register (компонент RegisterComponent).
** Поля ввода: Email, Password, Repeat Password, Security Question (dropdown select), Security Answer.
** Реактивная валидация Angular (Validators.required, Validators.email, Validators.minLength(5), matchValidator).
** Интерактивный переключатель советов по надежности пароля (Show password advice).
** Управление состоянием кнопки отправки (Register Button disabled до полной валидности формы).
** Навигация на форму входа (/login) по ссылке 'Already a customer?'.
** Обработка модальных окон (Welcome Banner, Cookie Consent).
* *Не входит в скоуп (Out-of-Scope):*
** Серверная обработка базы данных — выделена в задачу JS-40.
** Экран входа и сброса пароля.

h2. 3. Архитектурный контекст и UI-компоненты
* *Файлы компонентов:*
** frontend/src/app/register/register.component.ts -> роут /#/register
** frontend/src/app/register/register.component.html
** frontend/src/app/Services/user.service.ts -> вызов POST /api/Users/
** frontend/src/app/Services/security-question.service.ts -> вызов GET /api/SecurityQuestions/
** frontend/src/app/Services/security-answer.service.ts -> вызов POST /api/SecurityAnswers/
* *Связанная спецификация в Confluence:* https://romeo-timony.atlassian.net/wiki/pages/viewpage.action?pageId=3604481
* *Родительская история:* JS-39 (Регистрация нового покупателя через Email и пароль).

h2. 4. Таблица полей и правила валидации (Validation Matrix)
||Поле||Селектор||Обязательность||Ограничения||Текст ошибки на экране||
|Email|#emailControl|Да|RFC 5322 email|'Please provide an email address.' / 'Email address is not valid.'|
|Password|#passwordControl|Да|Мин. 5, макс. 40 символов|'Please provide a password.' / 'Password must be 5-40 characters long.'|
|Repeat Password|#repeatPasswordControl|Да|Совпадение с Password|'Please repeat your password.' / 'Passwords do not match'|
|Security Question|mat-select[name='securityQuestion']|Да|Выбор из 14 вариантов|'Please select a security question.' (Подсказка: 'This cannot be changed later!')|
|Security Answer|#securityAnswerControl|Да|Непустая строка|'Please provide an answer to your security question.'|
|Register Button|#registerButton|Да|Кнопка отправки формы|Заблокирована (disabled), пока все 5 контролов не станут valid|

h2. 5. Критерии приемки (Acceptance Criteria / Gherkin)
{code:gherkin}
Scenario: Успешная валидация и отправка формы регистрации
  Given пользователь открыл страницу "/#/register" и закрыл баннеры
  When он вводит валидный email, пароль от 5 символов, подтверждение пароля
  And выбирает секретный вопрос и заполняет секретный ответ
  Then кнопка "Register" становится активной
  When пользователь нажимает кнопку "Register"
  Then отображается нотификация успешной регистрации и происходит редирект на "/#/login"

Scenario: Блокировка кнопки Register при невалидных данных
  Given открыта форма регистрации
  When пользователь вводит некорректный email или короткий пароль (< 5 символов)
  Then отображаются соответствующие красные сообщения об ошибках
  And кнопка "Register" остается заблокированной (disabled)
{code}

h2. 6. Definition of Ready (DoR) Checklist
* [x] Описаны все элементы формы и селекторы.
* [x] Зафиксированы тексты сообщений об ошибках и валидаторы.
* [x] Специфицированы состояния кнопки Register.
* [x] Страница Confluence привязана к задаче.
"""

# Full rich DoR description for JS-42 [E2E]
e2e_dor = """h2. 1. Бизнес-контекст и цель задачи
*Бизнес-цель:* Реализовать сквозную интеграцию, приемочное тестирование и онбординг нового покупателя в интернет-магазине Juice Shop.
*Ценность для пользователя:* Бесшовный пользовательский опыт от момента регистрации учетной записи до входа в систему и добавления товаров в корзину.

h2. 2. Границы скоупа (Scope)
* *Входит в скоуп (In-Scope):*
** Сквозной сценарий онбординга (End-to-End Customer Journey): Регистрация на /#/register -> Переход на /#/login -> Авторизация -> Проверка профиля в меню Account -> Добавление товара в корзину.
** Проверка реакции UI на ошибку дубликата email (всплывающий красный баннер с сообщением сервера).
** Интеграция и верификация архитектурных челленджей Juice Shop (Admin Registration через mass assignment, passwordRepeat bypass, empty user registration).
** Проверка устойчивости к модальным окнам (Welcome Banner, Cookie Consent).
* *Не входит в скоуп (Out-of-Scope):*
** Оформление заказа и оплата (Checkout Flow) — отдельные сценарии магазина.

h2. 3. Архитектурный контекст и сценарии
* *Связанная спецификация в Confluence:* https://romeo-timony.atlassian.net/wiki/pages/viewpage.action?pageId=3604481
* *Родительская история:* JS-39 (Регистрация нового покупателя через Email и пароль).

h2. 4. Критерии приемки (Acceptance Criteria / Gherkin)
{code:gherkin}
Scenario: Полный сквозной путь нового покупателя (Onboarding Journey)
  Given новый пользователь открывает страницу "/#/register"
  When он проходит регистрацию с уникальным email
  And авторизуется на странице "/#/login" с созданными учетными данными
  Then в шапке сайта в меню "Account" отображается email пользователя
  When пользователь добавляет товар в корзину
  Then в корзине появляется добавленный товар под сессией нового пользователя

Scenario: Обработка дубликата email в интерфейсе
  Given пользователь пытается зарегистрироваться с уже существующим email
  When он нажимает "Register"
  Then в верхней части формы появляется красное сообщение об ошибке сервера
  And пользователь остается на странице регистрации, данные не теряются
{code}

h2. 5. Definition of Ready (DoR) Checklist
* [x] Описан сквозной пользовательский путь онбординга.
* [x] Зафиксированы интеграционные точки (Регистрация -> Логин -> Корзина).
* [x] Описаны граничные и негативные сценарии.
* [x] Страница Confluence привязана к задаче.
"""

# Story JS-39 description
story_dor = """h2. 1. Бизнес-контекст и цель пользовательской истории
*Бизнес-цель:* Предоставить новым покупателям веб-магазина Juice Shop возможность создания персональной учетной записи.
*User Story:* Как новый покупатель интернет-магазина Juice Shop, Я хочу создать персональный аккаунт с уникальным email, паролем и секретным вопросом, Чтобы безопасно входить в магазин, сохранять историю заказов и оформлять покупки.

h2. 2. Декомпозиция работ на инженерные задачи
* *JS-40:* [API] Реализация серверной логики и контрактов регистрации (POST /api/Users & /api/SecurityAnswers)
* *JS-41:* [UI] Разработка клиентской формы регистрации и валидации полей (/#/register)
* *JS-42:* [E2E] Сквозная интеграция, приемочные сценарии и онбординг нового покупателя

h2. 3. Связанная документация
* *Спецификация в Confluence:* https://romeo-timony.atlassian.net/wiki/pages/viewpage.action?pageId=3604481
* *Родительский Эпик:* JS-1 (Разработка ключевых функциональных модулей)
"""

set_description("JS-39", story_dor)
set_description("JS-40", api_dor)
set_description("JS-41", ui_dor)
set_description("JS-42", e2e_dor)

print("\nDone updating all issues with full DoR specifications!")
