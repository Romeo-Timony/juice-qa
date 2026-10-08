const https = require('https');

const email = 'roman.timoshenko@gmail.com';
const token = 'ATATT3xFfGF0fsfN5tTbmDMnKCM6GKKC3jeEDRBn31rScNDSMDI7LJhw7iihh_TMPq0ZhYcqd0t9CXMbS4zxcTzv44hzpt83RJw9Q6gzJ5VxGLnSVkqE4EaJ32dogjqQnkXX7iq6uCGc_KOlUGKeAnKjClPzKGMrGJSECkCK56TPvvXUfD4k4lI=2DFEDCC0';
const auth = Buffer.from(email + ':' + token).toString('base64');

const perfectedDescription = `h2. 1. Бизнес-контекст и цель задачи
*Бизнес-цель:* Реализовать клиентскую часть подсистемы учетных записей (регистрация, вход, сброс пароля, профиль пользователя) для интернет-магазина Juice Shop в соответствии с требованиями безопасности OWASP.
*Ценность для пользователя:* Возможность безопасно сохранять историю заказов, адреса доставки, управлять паролем и профилем без обращения в службу поддержки.

h2. 2. Границы скоупа (Scope)
* *Входит в скоуп (In-Scope):*
** Клиентские формы регистрации (/#/register), входа (/#/login) и сброса пароля (/#/forgot-password).
** Экран профиля пользователя (/#/profile) со сменой пароля и загрузкой аватара.
** Экран сохраненных адресов (/#/address/saved) и диалоговое окно добавления нового адреса.
** Реактивная валидация всех полей, обработка состояний загрузки, успеха и ошибок API.
* *Не входит в скоуп (Out-of-Scope):*
** Двухфакторная аутентификация (2FA TOTP) — выделена в отдельную задачу JS-40.
** Сторонняя авторизация через Google OAuth.

h2. 3. Архитектурный контекст и компоненты
* *Компоненты Angular (Frontend Architecture):*
** frontend/src/app/register/register.component.ts -> роут /#/register
** frontend/src/app/login/login.component.ts -> роут /#/login
** frontend/src/app/forgot-password/forgot-password.component.ts -> роут /#/forgot-password
** frontend/src/app/user-profile/user-profile.component.ts -> роут /#/profile
** frontend/src/app/address-create/address-create.component.ts -> диалог на /#/address/saved
* *Сервисы и хранилище:*
** UserService, SecurityQuestionService, AddressService
** Сохранение полученного Bearer JWT-токена в localStorage под ключом 'token', передача во все защищенные запросы через JwtInterceptor.
* *Связанная спецификация в Confluence:* https://romeo-timony.atlassian.net/wiki/spaces/JS/pages/163985
* *Родительская задача:* JS-15 (Реализация модуля аутентификации и профиля) в рамках Story JS-3.

h2. 4. Таблица полей и правила валидации (Validation Matrix)
||Поле||Тип||Обязательность||Ограничения и Regex||Текст ошибки при невалидности||
|Email|email|Да|RFC 5322, макс. 40 символов|'Please provide an email address.'|
|Password|password|Да|Мин. 5, макс. 40 символов|'Password must be 5 to 40 characters long.'|
|Repeat Password|password|Да|Полное совпадение со значением Password|'Passwords do not match.'|
|Security Question|select|Да|Выбор элемента из выпадающего списка|'Please select a security question.'|
|Security Answer|text|Да|Мин. 1, макс. 50 символов|'Please provide an answer to your security question.'|
|Country|text|Да|Мин. 2, макс. 60 символов, только буквы|'Please provide a country.'|
|Name|text|Да|Мин. 2, макс. 100 символов|'Please provide a name.'|
|Mobile Phone|tel|Да|^[0-9]{10,15}$ (10-15 цифр)|'Please provide a mobile number (10-15 digits).'|
|ZIP Code|text|Да|^[0-9A-Za-z -]{3,10}$|'Please provide a ZIP code.'|
|Address|text|Да|Мин. 5, макс. 160 символов|'Please provide an address.'|
|City|text|Да|Мин. 2, макс. 60 символов|'Please provide a city.'|
|Current Password|password|Да|Мин. 1 символ|'Please provide your current password.'|
|New Password|password|Да|Мин. 5, макс. 40 символов|'New password must be 5 to 40 characters long.'|
|Repeat New Password|password|Да|Полное совпадение со значением New Password|'New passwords do not match.'|
|Profile Avatar|file|Нет|Форматы .png, .jpg, .jpeg, макс. размер 2MB|'File size must not exceed 2MB. Allowed formats: PNG, JPEG.'|

h2. 5. Интеграция с REST API
* *POST /api/Users/* — Регистрация. Request Body: { email, password, passwordRepeat, securityQuestion: { id }, securityAnswer }. Ожидаемый ответ: 201 Created. Ошибки: 400 Bad Request ('Validation error'), 409 Conflict ('Email must be unique.').
* *POST /rest/user/login* — Аутентификация. Request Body: { email, password }. Ответ 200 OK: { authentication: { token, bid, umail } }. Ошибка 401 Unauthorized ('Invalid email or password.').
* *POST /rest/user/reset-password* — Сброс пароля. Request Body: { email, answer, newPassword, repeatNewPassword }. Ответ 200 OK. Ошибка 401 Unauthorized ('Wrong answer to security question.').
* *GET /api/SecurityQuestions/* — Получение списка вопросов. Ответ 200 OK: { status: 'success', data: [{ id: 1, question: 'Your eldest siblings middle name?' }] }.
* *GET /rest/user/security-question?email=:email* — Получение вопроса конкретного пользователя при сбросе пароля. Ответ 200 OK: { question: { id, question } }.
* *GET, POST /api/Addresss/* — Получение списка и добавление адресов доставки (согласно схеме REST API Juice Shop). Заголовок: Authorization: Bearer <token>. Ответ 200/201.
* *GET /rest/user/whoami* — Получение профиля текущего авторизованного пользователя. Заголовок: Authorization: Bearer <token>. Ответ 200 OK: { user: { id: 1, email: 'user@test.com', profileImage: '/assets/public/images/uploads/default.svg' } }.
* *POST /rest/user/change-password* — Безопасная смена пароля авторизованного пользователя в соответствии со стандартами OWASP. Request Body: { current: '...', new: '...', repeat: '...' }. Заголовок: Authorization: Bearer <token>. Ответ 200 OK: { user: { id: 1 } }. Ошибки: 401 Unauthorized ('Current password is not correct.'), 400 Bad Request ('New passwords do not match.').
* *POST /profile/image/file* — Загрузка файла аватара. Content-Type: multipart/form-data (поле file). Заголовок: Authorization: Bearer <token>. Ответ 200 OK: { status: 'success', data: { url: '/assets/public/images/uploads/user-avatar.png' } }. Ошибка 400 Bad Request ('Invalid file format or size exceeds 2MB.').

h2. 6. Состояния пользовательского интерфейса (UI States)
* *Default State:* Кнопки отправки формы деактивированы (disabled), пока форма не станет полностью валидной.
* *Loading State:* При отправке запроса на кнопке отображается MatProgressSpinner, повторные клики программно заблокированы.
* *Success State:* Закрытие формы/модального окна, отображение зеленого MatSnackBar ('Registration completed successfully. You can now log in.' / 'Address saved successfully.' / 'Your password was changed successfully.' / 'Profile image updated.').
* *Empty State:* При отсутствии адресов в таблице выводится плашка 'No saved addresses found. Please add a new delivery address.'.
* *Error State:* При ошибках сервера отображается красный MatSnackBar с текстом ошибки ответа API (например, 'Invalid email or password.' / 'Current password is not correct.').

h2. 7. Критерии приемки (Acceptance Criteria & BDD Scenarios)
h3. Чек-лист критериев приемки (Acceptance Criteria):
* [x] *AC-01:* Форма регистрации валидирует уникальность email и совпадение паролей. При успехе создает пользователя в БД (POST /api/Users/) и редиректит на /#/login с зеленым SnackBar.
* [x] *AC-02:* Попытка повторной регистрации существующего email возвращает HTTP 409 и выводит ошибку 'Email must be unique.'.
* [x] *AC-03:* Форма аутентификации проверяет пару email/пароль (POST /rest/user/login), сохраняет JWT в localStorage под ключом 'token' и перенаправляет в каталог.
* [x] *AC-04:* Неверный пароль или несуществующий email возвращает HTTP 401 и выводит 'Invalid email or password.' без сохранения токена.
* [x] *AC-05:* Сброс пароля требует верного ответа на контрольный вопрос (POST /rest/user/reset-password). При неверном ответе выводится 'Wrong answer to security question.'.
* [x] *AC-06:* Авторизованный пользователь может сменить пароль в профиле (POST /rest/user/change-password) с обязательной проверкой текущего пароля.
* [x] *AC-07:* Загрузка аватара в профиле принимает только PNG/JPEG до 2MB (POST /profile/image/file), возвращает новый url изображения и обновляет аватар на клиенте.
* [x] *AC-08:* Добавление адреса доставки проверяет корректность телефона (10-15 цифр) и обязательность всех полей адреса.

h3. Спецификация сценариев BDD (Gherkin):
{code:gherkin}
Scenario: Успешная регистрация нового клиента
  Given гость находится на странице "/#/register"
  When заполняет email "user@test.com", пароль "Pass123", подтверждение "Pass123"
  And выбирает вопрос "Your eldest siblings middle name?" и вводит ответ "Ivan"
  And нажимает активную кнопку "Register"
  Then отправляется запрос POST /api/Users/
  And отображается зеленый SnackBar "Registration completed successfully. You can now log in."
  And пользователь перенаправляется на роут "/#/login"

Scenario: Ошибка при попытке регистрации с занятым email
  Given гость вводит в форме регистрации уже существующий email "admin@juice-sh.op"
  When нажимает "Register"
  Then сервер возвращает HTTP 409 Conflict
  And отображается красный SnackBar "Email must be unique."
  And форма регистрации не очищается

Scenario: Ошибка аутентификации при неверном пароле
  Given пользователь находится на странице "/#/login"
  When вводит email "user@test.com" и неверный пароль "wrongpass"
  And нажимает кнопку "Log in"
  Then сервер возвращает HTTP 401 Unauthorized
  And отображается красный SnackBar "Invalid email or password."
  And токен авторизации не сохраняется в localStorage

Scenario: Успешная смена пароля авторизованным пользователем в профиле
  Given пользователь авторизован и находится на странице "/#/profile"
  When вводит текущий пароль "Pass123", новый пароль "NewPass456" и подтверждение "NewPass456"
  And нажимает кнопку "Change Password"
  Then отправляется запрос POST /rest/user/change-password с токеном Authorization: Bearer <token>
  And сервер возвращает HTTP 200 OK
  And отображается зеленый SnackBar "Your password was changed successfully."
  And поля смены пароля очищаются

Scenario: Успешная загрузка аватара в профиле пользователя
  Given пользователь авторизован и находится на странице "/#/profile"
  When выбирает изображение "avatar.png" размером менее 2MB
  And нажимает кнопку "Upload"
  Then отправляется multipart запрос POST /profile/image/file с токеном Authorization
  And сервер возвращает HTTP 200 OK с новым url в ответе "{ status: 'success', data: { url: '/assets/public/images/uploads/user-avatar.png' } }"
  And отображается зеленый SnackBar "Profile image updated."
  And изображение аватара на странице профиля обновляет src на полученный url
{code}

h2. 8. Нефункциональные требования, дизайн и адаптивность
* *Дизайн-макеты и компоненты:* Wireframes в Figma [OWASP Juice Shop UI/UX Design System|https://www.figma.com/design/owasp-juice-shop-auth-ui], библиотека Angular Material (MatCard, MatFormField, MatInput, MatSelect, MatButton, MatSnackBar).
* *Адаптивная сетка (Responsive Breakpoints):*
** Mobile (360px-767px): Вертикальный single-column flex-layout, поля ввода растягиваются на 100% ширины экрана.
** Tablet (768px-1199px): Двухколоночный grid-layout для парных полей (Country/City, Password/Repeat).
** Desktop (1200px+): Центрированная карточка формы фиксированной ширины 520px.
* *Доступность (Accessibility / a11y):* Соответствие стандарту WCAG 2.1 Level AA, атрибуты aria-label и aria-required для всех полей ввода, полная навигация с клавиатуры по клавише Tab.
* *Кроссбраузерность:* Chrome 120+, Firefox 120+, Edge 120+, Safari 17+.
* *Производительность:* Время начальной загрузки и рендеринга форм FCP < 1.0s, LCP < 2.0s, время отклика UI на действия пользователя < 50ms.
* *Логирование и мониторинг:* Все необработанные ошибки UI и сбои сетевых запросов (HTTP 4xx/5xx) логируются в консоль и передаются в клиентский логгер.
* *Интернационализация (i18n):* Поддержка мультиязычности через Angular i18n / ngx-translate; базовый язык интерфейса — английский (en), тексты сообщений вынесены в JSON-словари.
* *Тестовое окружение и данные:* Стенд Staging (http://localhost:3000), тестовые учетные записи: существующий пользователь admin@juice-sh.op, новый пользователь user@test.com / Pass123, секретный вопрос ID 1 ('Your eldest siblings middle name?'), тестовый ответ 'Ivan'.
* *Тестовое покрытие:* Покрытие бизнес-логики компонентов unit-тестами Vitest >= 80%.
`;

async function updateAndTransition() {
  // 1. Update issue
  await new Promise((resolve, reject) => {
    const req = https.request({
      hostname: 'romeo-timony.atlassian.net',
      path: '/rest/api/2/issue/JS-16',
      method: 'PUT',
      headers: {
        'Authorization': 'Basic ' + auth,
        'Content-Type': 'application/json'
      }
    }, res => {
      console.log('1. Updated JS-16 description and cleared labels -> Status:', res.statusCode);
      resolve();
    });
    req.write(JSON.stringify({ fields: { description: perfectedDescription, labels: [] } }));
    req.end();
  });

  // 2. Transition to In Progress (id 21)
  await new Promise((resolve) => {
    const req = https.request({
      hostname: 'romeo-timony.atlassian.net',
      path: '/rest/api/2/issue/JS-16/transitions',
      method: 'POST',
      headers: {
        'Authorization': 'Basic ' + auth,
        'Content-Type': 'application/json'
      }
    }, res => {
      console.log('2. Transitioned JS-16 to In Progress -> Status:', res.statusCode);
      resolve();
    });
    req.write(JSON.stringify({ transition: { id: '21' } }));
    req.end();
  });
}

updateAndTransition();
