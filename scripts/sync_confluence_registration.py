import os
import requests
import dotenv

dotenv.load_dotenv('.env')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
base_url = os.getenv('CONFLUENCE_BASE_URL', 'https://romeo-timony.atlassian.net/wiki').rstrip('/')
auth = (email, token)
space_key = os.getenv('CONFLUENCE_SPACE_KEY', 'JS')
parent_id = '163985'  # JS-3 page

title = "JS-100: Регистрация нового пользователя (User Registration)"

# Read markdown spec or build rich storage format HTML
html_content = """
<h2>1. Паспорт функционального модуля</h2>
<table>
  <tbody>
    <tr><th>Параметр</th><th>Значение</th></tr>
    <tr><td><strong>Задача в Jira</strong></td><td>JS-100: Регистрация нового покупателя через Email и пароль</td></tr>
    <tr><td><strong>Родительский Эпик</strong></td><td>JS-1: Разработка ключевых функциональных модулей</td></tr>
    <tr><td><strong>Родительский модуль</strong></td><td>JS-3: Модуль аутентификации, авторизации и управления профилем клиента</td></tr>
    <tr><td><strong>Статус аналитики</strong></td><td>Ready for Dev &amp; QA</td></tr>
    <tr><td><strong>Команда</strong></td><td>Cross-functional Team (Frontend, Backend, QA)</td></tr>
  </tbody>
</table>

<h2>2. Бизнес-контекст и User Story</h2>
<p><strong>User Story:</strong> Как новый покупатель интернет-магазина Juice Shop, Я хочу создать персональный аккаунт, указав адрес электронной почты, надежный пароль и секретный контрольный вопрос, Чтобы безопасно авторизовываться в магазине, сохранять историю покупок и оформлять доставку товаров.</p>

<h3>Бизнес-правила (Business Rules):</h3>
<ul>
  <li><strong>BR-AUTH-01 (Уникальность):</strong> Email пользователя должен быть уникальным в системе (case-insensitive). Попытка регистрации дубликата возвращает HTTP 400 Bad Request.</li>
  <li><strong>BR-AUTH-02 (Длина пароля):</strong> Пароль должен содержать от 5 до 40 символов. Клиентская форма отображает интерактивный индикатор стойкости пароля.</li>
  <li><strong>BR-AUTH-03 (Контрольный вопрос):</strong> Обязательный выбор из справочника (14 контрольных вопросов) и ввод ответа. Не подлежит изменению после регистрации.</li>
  <li><strong>BR-AUTH-04 (Санитизация ввода):</strong> На сервере применяется автоматический тримминг пробелов для email и паролей.</li>
  <li><strong>BR-AUTH-05 (Валидация пустых полей):</strong> Пустые строки блокируются валидатором с возвратом HTTP 400 'Invalid email/password cannot be empty'.</li>
</ul>

<h2>3. Системный анализ и архитектурные решения</h2>
<h3>3.1. Frontend компоненты (Angular 21):</h3>
<ul>
  <li><code>RegisterComponent</code> (роут <code>/#/register</code>) — форма регистрации с реактивной валидацией полей (Email, Password, Repeat Password, Security Question select, Security Answer).</li>
  <li><code>UserService.save(user)</code> — клиентский сервис отправки регистрационных данных.</li>
  <li><code>SecurityAnswerService.save(answer)</code> — сохранение контрольного ответа для связки с созданным пользователем.</li>
</ul>

<h3>3.2. REST API эндпоинты:</h3>
<table>
  <thead>
    <tr><th>Метод</th><th>Эндпоинт</th><th>Описание</th><th>Тело запроса / Ответа</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/SecurityQuestions/</code></td>
      <td>Получение списка 14 контрольных вопросов</td>
      <td>200 OK &rarr; <code>{ status: 'success', data: [...] }</code></td>
    </tr>
    <tr>
      <td><code>POST</code></td>
      <td><code>/api/Users/</code></td>
      <td>Создание учетной записи пользователя</td>
      <td><code>{ email, password, passwordRepeat, securityQuestion, securityAnswer }</code> &rarr; 201 Created</td>
    </tr>
    <tr>
      <td><code>POST</code></td>
      <td><code>/api/SecurityAnswers/</code></td>
      <td>Сохранение секретного ответа пользователя</td>
      <td><code>{ UserId, SecurityQuestionId, answer }</code> &rarr; 201 Created</td>
    </tr>
  </tbody>
</table>

<h2>4. Варианты создания пользователя (Спецификация разработчиков OWASP Juice Shop)</h2>
<ul>
  <li><strong>Стандартный покупатель (Customer):</strong> роль по умолчанию <code>customer</code>, базовый аватар <code>/assets/public/images/uploads/default.svg</code>.</li>
  <li><strong>Административная учетная запись (Admin Registration):</strong> поддержка присвоения роли <code>admin</code> при передаче параметра <code>role</code> (соответствует вызову челленджа <code>registerAdminChallenge</code>), системный аватар <code>defaultAdmin.png</code>.</li>
  <li><strong>Граничные условия безопасности:</strong> проверка устойчивости к несовпадению паролей при прямом API вызове (челлендж <code>passwordRepeatChallenge</code>) и проверка пустой регистрации (челлендж <code>emptyUserRegistration</code>).</li>
</ul>

<h2>5. Критерии приемки (Acceptance Criteria / Gherkin)</h2>
<pre><code>Scenario: Успешная регистрация нового покупателя через форму
  Given гость открывает страницу "/#/register"
  And закрывает модальное окно приветствия и cookie-баннер
  When заполняет email уникальным значением "new_buyer@juice-sh.op"
  And вводит пароль "Secret123!" и подтверждение "Secret123!"
  And выбирает секретный вопрос и указывает ответ "Alexander"
  And нажимает кнопку "Register"
  Then система отображает подтверждение успешной регистрации
  And пользователь перенаправляется на форму входа "/#/login"

Scenario: Блокировка кнопки Register при невалидных данных
  Given открыта страница регистрации
  When поле Email заполнено значением "invalid-email"
  Or пароль содержит менее 5 символов
  Or подтверждение пароля не совпадает с паролем
  Then под соответствующими полями отображаются сообщения об ошибках
  And кнопка "Register" находится в заблокированном состоянии (disabled)</code></pre>
"""

# Check if page already exists
check_r = requests.get(f"{base_url}/rest/api/content?spaceKey={space_key}&title={requests.utils.quote(title)}", auth=auth)
existing = check_r.json().get('results', [])

if existing:
    page_id = existing[0]['id']
    version = existing[0]['version']['number'] + 1
    print(f"Updating existing Confluence page {page_id} to version {version}...")
    update_payload = {
        "version": {"number": version},
        "title": title,
        "type": "page",
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage"
            }
        }
    }
    r = requests.put(f"{base_url}/rest/api/content/{page_id}", json=update_payload, auth=auth)
    print(f"Update status: {r.status_code}")
else:
    print(f"Creating new Confluence page '{title}' under parent {parent_id}...")
    create_payload = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "ancestors": [{"id": parent_id}],
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage"
            }
        }
    }
    r = requests.post(f"{base_url}/rest/api/content", json=create_payload, auth=auth)
    print(f"Create status: {r.status_code}")
    if r.ok:
        new_page = r.json()
        print(f"Created page ID: {new_page.get('id')}, URL: {base_url}/pages/viewpage.action?pageId={new_page.get('id')}")
    else:
        print(r.text)
