const defaultFrontendCases = [
  {
    id: 'TC-FE-01',
    title: '[Frontend][Parametrized] Успешная регистрация нового пользователя с валидными форматами Email',
    description: `## 📌 Цель тест-кейса
Параметризованная проверка успешной регистрации нового пользователя в веб-приложении OWASP Juice Shop с различными валидными форматами адресов электронной почты (согласно спецификации RFC 5322).
Тест-кейс валидирует, что фронтенд корректно принимает валидные email-адреса, передает их на бэкенд и завершает регистрацию без ошибок.

---

## 📊 Матрица параметров и тестовых данных (Data-Driven Matrix)
Данный сценарий выполняется для **3 независимых наборов данных (итераций)**:

| № набора | Тип проверки / Класс эквивалентности | Email (<email>) | Пароль (<password>) | Контрольный вопрос (<question_id>) | Ответ на вопрос (<answer>) | Ожидаемый HTTP статус (<status_code>) |
|:---:|:---|:---|:---|:---|:---|:---:|
| **Набор 1** | **Стандартный Happy Path**<br>Классический email с латиницей и точкой | \`standard.user@juice-sh.op\` | \`Pass12345\` | \`1\` (Your eldest siblings middle name?) | \`SecretAnswer\` | **201 Created** |
| **Набор 2** | **Спецсимволы RFC 5322**<br>Email с символом \`+\`, дефисом и поддоменом | \`user.plus+testing@sub.juice-sh.op\` | \`SecureP@ss2026!\` | \`2\` (Mother's maiden name?) | \`MyMothersDog\` | **201 Created** |
| **Набор 3** | **Граничная длина (BVA)**<br>Длинный email (35+ символов) с цифрами | \`valid_boundary_35_chars@juice-sh.op\` | \`ValidPass888\` | \`3\` (Mother's birth date?) | \`MiddleName\` | **201 Created** |

---

## 🥒 Спецификация BDD Gherkin (совместима с Cucumber, Behave, Playwright-BDD)
\`\`\`gherkin
# language: ru
@allure.epic("OWASP Juice Shop")
@allure.feature("Customer Authentication")
@allure.story("${ctx.issueKey}: Регистрация пользователя")
@allure.severity("critical")
@fast-regression
@full-regression
Структура сценария: Успешная регистрация клиента с различными валидными форматами Email
  Дано гость не авторизован и находится на странице регистрации "/#/register"
  Когда пользователь вводит адрес электронной почты "<email>"
  И вводит пароль "<password>" в поле "Password"
  И подтверждает пароль "<password>" в поле "Repeat Password"
  И выбирает контрольный вопрос с кодом "<question_id>" и указывает ответ "<answer>"
  И нажимает кнопку "Register"
  Тогда отправляется сетевой запрос POST /api/Users/
  И сервер возвращает HTTP-статус <status_code>
  И на экране отображается зеленое уведомление "Registration completed successfully. You can now log in."
  И выполняется автоматическое перенаправление на страницу входа "/#/login"

  Примеры:
    | email                               | password        | question_id | answer       | status_code |
    | standard.user@juice-sh.op           | Pass12345       | 1           | SecretAnswer | 201         |
    | user.plus+testing@sub.juice-sh.op   | SecureP@ss2026! | 2           | MyMothersDog | 201         |
    | valid_boundary_35_chars@juice-sh.op | ValidPass888    | 3           | MiddleName   | 201         |
\`\`\``,
    covers: ['AC-01', 'F01', 'F02', 'F03'],
    type: 'smoke',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'smoke', 'parametrized', 'data-driven', 'fast-regression', 'full-regression'],
    preconditions: 'Гость находится на странице "/#/register", база данных доступна, тестовые email еще не зарегистрированы.',
    steps: [
      {
        action: '[1. Given / Подготовка] Открыть страницу регистрации нового пользователя',
        data: 'URL: http://localhost:3000/#/register',
        expected_result: 'Страница регистрации успешно загружена, форма пуста, кнопка «Register» заблокирована (disabled).'
      },
      {
        action: '[2. When / Ввод Email] Ввести значение в поле «Email» (согласно выбранному набору параметров)',
        data: 'Значения параметра <email> из матрицы:\n• Набор 1 (Happy Path): standard.user@juice-sh.op\n• Набор 2 (Спецсимволы RFC): user.plus+testing@sub.juice-sh.op\n• Набор 3 (Длинный email): valid_boundary_35_chars@juice-sh.op',
        expected_result: 'Значение принято полем ввода, под полем нет красных предупреждений об ошибке формата.'
      },
      {
        action: '[3. When / Ввод Пароля] Ввести пароль в поле «Password» и продублировать его в «Repeat Password»',
        data: 'Значения параметра <password>:\n• Набор 1: Pass12345\n• Набор 2: SecureP@ss2026!\n• Набор 3: ValidPass888',
        expected_result: 'Введенные пароли маскированы символами точек, совпадают, ошибки несовпадения не отображаются.'
      },
      {
        action: '[4. When / Секретный вопрос] Выбрать вопрос в выпадающем списке «Security Question» и заполнить поле «Answer»',
        data: 'Параметры <question_id> и <answer>:\n• Набор 1: Вопрос №1 ("Your eldest siblings middle name?"), Ответ: SecretAnswer\n• Набор 2: Вопрос №2 ("Mother\'s maiden name?"), Ответ: MyMothersDog\n• Набор 3: Вопрос №3 ("Mother\'s birth date?"), Ответ: MiddleName',
        expected_result: 'Вопрос выбран, ответ введен. Все обязательные поля заполнены, кнопка «Register» становится активной.'
      },
      {
        action: '[5. When / Отправка формы] Нажать кнопку «Register»',
        data: 'Клик по активной кнопке «Register»',
        expected_result: 'В Network отправляется POST-запрос на /api/Users/, сервер возвращает HTTP-статус 201 Created.'
      },
      {
        action: '[6. Then / Верификация] Проверить сообщение об успешной регистрации и переадресацию',
        data: 'Проверка всплывающего SnackBar и адресной строки браузера',
        expected_result: 'Отображается зеленое всплывающее уведомление: "Registration completed successfully. You can now log in.", браузер перенаправляет на "/#/login".'
      }
    ],
    postconditions: 'Учетная запись пользователя успешно создана в базе данных SQLite (таблица Users).',
    parameters: [
      {
        shared_id: '01a1174f-0c29-7051-b039-a69eeafe74c7'
      }
    ]
  },
  {
    id: 'TC-FE-02',
    title: '[Frontend][Parametrized] Проверка граничных значений длины пароля при регистрации пользователя',
    description: `## 📌 Цель тест-кейса
Параметризованное тестирование граничных значений (BVA — Boundary Value Analysis) длины поля «Пароль» при регистрации пользователя в веб-приложении OWASP Juice Shop.
Требование системы: длина пароля должна составлять строго от 5 до 40 символов включительно.

---

## 📊 Матрица параметров и тестовых данных (Data-Driven Matrix)
Тест-кейс проверяет **5 граничных наборов данных (итераций)**:

| № набора | Класс / Граничная точка | Значение (<password>) | Длина (<length>) | Ожидаемая валидность (<is_valid>) | Сообщение об ошибке (<error_message>) | Кнопка Register (<button_enabled>) |
|:---:|:---|:---|:---:|:---:|:---|:---:|
| **Набор 1** | **Граница минимума: Min - 1** (Невалидно) | \`Pass\` | **4** | ❌ Невалидно (\`false\`) | \`Password must be 5-40 characters long\` | 🔒 Заблокирована (\`disabled\`) |
| **Набор 2** | **Граница минимума: Min** (Валидно) | \`Pass5\` | **5** | ✅ Валидно (\`true\`) | Ошибок нет (\`none\`) | 🟢 Активна (\`enabled\`) |
| **Набор 3** | **Граница минимума: Min + 1** (Валидно) | \`Pass6\` | **6** | ✅ Валидно (\`true\`) | Ошибок нет (\`none\`) | 🟢 Активна (\`enabled\`) |
| **Набор 4** | **Граница максимума: Max** (Валидно) | \`ExactlyFortyCharactersLongSecurePass123!\` | **40** | ✅ Валидно (\`true\`) | Ошибок нет (\`none\`) | 🟢 Активна (\`enabled\`) |
| **Набор 5** | **Граница максимума: Max + 1** (Невалидно) | \`ExceedingFortyOneCharsLongSecurePassword!\` | **41** | ❌ Невалидно (\`false\`) | \`Password must be 5-40 characters long\` | 🔒 Заблокирована (\`disabled\`) |

---

## 🥒 Спецификация BDD Gherkin (совместима с Cucumber, Behave, Playwright-BDD)
\`\`\`gherkin
# language: ru
@allure.epic("OWASP Juice Shop")
@allure.feature("Customer Authentication")
@allure.story("\${ctx.issueKey}: Валидация пароля при регистрации")
@allure.severity("critical")
@full-regression
Структура сценария: Проверка граничных условий длины пароля (от 5 до 40 символов)
  Дано гость не авторизован и находится на странице регистрации "/#/register"
  И вводит валидный уникальный адрес электронной почты "bva.user@juice-sh.op"
  Когда пользователь вводит пароль "<password>" длиной <length> символов
  Тогда статус валидации поля пароля равен "<is_valid>"
  И под полем отображается предупреждение "<error_message>"
  И состояние кнопки отправки формы "Register" равно "<button_enabled>"

  Примеры:
    | password                                 | length | is_valid | error_message                         | button_enabled |
    | Pass                                     | 4      | false    | Password must be 5-40 characters long | disabled       |
    | Pass5                                    | 5      | true     | none                                  | enabled        |
    | Pass6                                    | 6      | true     | none                                  | enabled        |
    | ExactlyFortyCharactersLongSecurePass123! | 40     | true     | none                                  | enabled        |
    | ExceedingFortyOneCharsLongSecurePassword!| 41     | false    | Password must be 5-40 characters long | disabled       |
\`\`\``,
    covers: ['AC-01', 'F02'],
    type: 'functional',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'bva', 'validation', 'parametrized', 'full-regression'],
    preconditions: 'Открыта страница "/#/register".',
    steps: [
      {
        action: '[1. Given / Подготовка] Открыть страницу регистрации нового пользователя',
        data: 'URL: http://localhost:3000/#/register',
        expected_result: 'Форма регистрации отображена, поле пароля пустое.'
      },
      {
        action: '[2. Given / Предзаполнение Email] Ввести валидный уникальный email',
        data: 'bva.test.user@juice-sh.op',
        expected_result: 'Поле Email заполнено и валидно.'
      },
      {
        action: '[3. When / Ввод пароля] Ввести пароль граничной длины в поле «Password»',
        data: 'Значения параметра <password> (длина <length>):\n• Набор 1 (длина 4, невалидно): Pass\n• Набор 2 (длина 5, мин): Pass5\n• Набор 3 (длина 6, мин+1): Pass6\n• Набор 4 (длина 40, макс): ExactlyFortyCharactersLongSecurePass123!\n• Набор 5 (длина 41, макс+1): ExceedingFortyOneCharsLongSecurePassword!',
        expected_result: 'Символы пароля введены и скрыты маской.'
      },
      {
        action: '[4. Then / Верификация валидации] Проверить реакцию валидатора формы и текст ошибки',
        data: 'Проверка класса mat-error и текста подсказки',
        expected_result: 'Для наборов 1 и 5: отображается красная ошибка «Password must be 5-40 characters long».\nДля наборов 2, 3, 4: ошибок валидации нет.'
      },
      {
        action: '[5. Then / Проверка кнопки] Проверить доступность кнопки «Register»',
        data: 'Проверка селектора button[type=submit]',
        expected_result: 'Для наборов 1 и 5: кнопка заблокирована (disabled).\nДля наборов 2, 3, 4 (при заполненных остальных полях): кнопка активна.'
      }
    ],
    postconditions: 'Форма реагирует реактивно до отправки запроса.',
    parameters: [
      {
        shared_id: '01a11751-4319-724c-be37-bc882c4614f8'
      }
    ]
  },
  {
    id: 'TC-FE-03',
    title: '[Frontend] Валидация ошибки при несовпадении пароля и подтверждения пароля',
    description: 'Проверка клиентского валидатора соответствия полей Password и Repeat Password. Входит в полный регресс.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Customer Authentication")
@allure.story("${ctx.issueKey}: User Registration Validation")
@allure.severity("major")
@full-regression
Scenario: Блокировка отправки формы при несовпадении паролей
  Given гость находится на форме регистрации "/#/register"
  When заполняет поле Password значением "Password123"
  And заполняет поле Repeat Password значением "DifferentPassword999"
  Then под полем подтверждения пароля отображается ошибка "Passwords do not match."
  And кнопка "Register" деактивирована (disabled)
  And сетевой запрос на сервер не отправляется`,
    covers: ['AC-01', 'F02'],
    type: 'functional',
    severity: 'major',
    priority: 'high',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'validation', 'full-regression'],
    preconditions: 'Открыта страница "/#/register".',
    steps: [
      { action: '[Given] Открыть форму регистрации', data: 'URL: /#/register', expected_result: 'Форма открыта' },
      { action: '[When] Ввести пароль', data: 'Password123', expected_result: 'Пароль введен' },
      { action: '[And] Ввести отличающийся повтор пароля', data: 'DifferentPassword999', expected_result: 'Отображена ошибка "Passwords do not match."' },
      { action: '[Then] Проверить состояние кнопки Register', data: 'button status', expected_result: 'Кнопка заблокирована (disabled)' }
    ],
    postconditions: 'Форма не отправлена.'
  },
  {
    id: 'TC-FE-04',
    title: '[Frontend] Обработка ошибки 409 Conflict при регистрации с уже занятым Email',
    description: 'Проверка обработки серверной ошибки уникальности email и отображения обратной связи пользователю. Входит в полный регресс.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Customer Authentication")
@allure.story("${ctx.issueKey}: User Registration")
@allure.severity("critical")
@full-regression
Scenario: Ошибка регистрации при попытке создать дубликат Email
  Given в системе уже зарегистрирован пользователь с Email "admin@juice-sh.op"
  When гость заполняет все поля формы регистрации и указывает Email "admin@juice-sh.op"
  And нажимает кнопку "Register"
  Then сервер возвращает HTTP-статус 409 Conflict
  And на экране отображается красный SnackBar с текстом ошибки "Email must be unique."
  And поля формы не очищаются для возможности корректировки`,
    covers: ['AC-02', 'F03'],
    type: 'functional',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api-conflict', 'full-regression'],
    preconditions: 'Пользователь "admin@juice-sh.op" уже существует в БД.',
    steps: [
      { action: '[Given] Заполнить форму с занятым Email', data: 'admin@juice-sh.op', expected_result: 'Форма заполнена' },
      { action: '[When] Нажать кнопку "Register"', data: 'click "Register"', expected_result: 'POST /api/Users/ возвращает 409 Conflict' },
      { action: '[Then] Проверить сообщение об ошибке', data: 'SnackBar', expected_result: 'Красный SnackBar "Email must be unique."' }
    ],
    postconditions: 'Дубликат записи в БД не создан.'
  },
  {
    id: 'TC-FE-05',
    title: '[Frontend][Parametrized] Аутентификация пользователя и проверка безопасности сессии при входе',
    description: 'Data-driven сценарий проверки входа в систему: валидные данные, неверный пароль, несуществующий логин, SQL-инъекция. Входит в быстрый и полный регресс.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Customer Authentication")
@allure.story("${ctx.issueKey}: User Login")
@allure.severity("blocker")
@fast-regression
@full-regression
Scenario Outline: Проверка сценариев аутентификации пользователя
  Given клиент находится на странице логина "/#/login"
  When вводит логин "<email>" и пароль "<password>"
  And нажимает кнопку "Log in"
  Then сервер возвращает HTTP-ответ со статусом <expected_status>
  And наличие токена авторизации в localStorage соответствует "<token_present>"
  And отображается системное уведомление "<notification_message>"
  And статус авторизации в интерфейсе соответствует "<is_logged_in>"

  Examples:
    | email                  | password        | expected_status | token_present | notification_message         | is_logged_in |
    | user@test.com          | ValidPass123    | 200             | true          | none                         | true         |
    | user@test.com          | WrongPass999    | 401             | false         | Invalid email or password.   | false        |
    | not_found@test.com     | AnyPassword123  | 401             | false         | Invalid email or password.   | false        |
    | admin@juice-sh.op'--   | dummy           | 401             | false         | Invalid email or password.   | false        |`,
    covers: ['AC-03', 'AC-04', 'F03'],
    type: 'smoke',
    severity: 'blocker',
    priority: 'high',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'login', 'security', 'smoke', 'parametrized', 'fast-regression', 'full-regression'],
    preconditions: 'Пользователь user@test.com / ValidPass123 существует.',
    steps: [
      { action: '[Given] Открыть страницу логина "/#/login"', data: 'URL: /#/login', expected_result: 'Форма логина отображается' },
      { action: '[When] Ввести учетные данные', data: 'login: <email>, pass: <password>', expected_result: 'Поля заполнены' },
      { action: '[And] Нажать кнопку "Log in"', data: 'click "Log in"', expected_result: 'POST /rest/user/login возвращает HTTP <expected_status>' },
      { action: '[Then] Проверить состояние сессии и токен', data: 'localStorage.token', expected_result: 'Токен: <token_present>, авторизован: <is_logged_in>' }
    ],
    postconditions: 'Состояние авторизации соответствует ожидаемому.'
  },
  {
    id: 'TC-FE-06',
    title: '[Frontend] Сохранение Bearer JWT в сессии и добавление заголовка Authorization в JwtInterceptor',
    description: 'Проверка сохранения токена в localStorage и автоматического добавления заголовка Authorization во все исходящие API-запросы. Входит в быстрый и полный регресс.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Customer Authentication")
@allure.story("${ctx.issueKey}: Token & Session Management")
@allure.severity("critical")
@fast-regression
@full-regression
Scenario: Сохранение токена в localStorage и инъекция заголовка Authorization
  Given клиент успешно авторизовался с валидными учетными данными
  Then JWT Bearer токен сохраняется в localStorage под ключом 'token'
  When клиент переходит в каталог товаров и инициирует защищенный запрос
  Then Angular JwtInterceptor добавляет заголовок "Authorization: Bearer <jwt_token>"
  And сервер успешно валидирует запрос и возвращает статус 200 OK
  When пользователь перезагружает страницу в браузере (F5)
  Then сессия пользователя сохраняется без требования повторного входа`,
    covers: ['AC-03', 'F03'],
    type: 'functional',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'jwt', 'security', 'session', 'fast-regression', 'full-regression'],
    preconditions: 'Пользователь авторизован.',
    steps: [
      { action: '[Given] Авторизоваться в приложении', data: 'POST /rest/user/login', expected_result: 'Получен JWT токен' },
      { action: '[Then] Проверить запись в localStorage', data: 'localStorage.getItem("token")', expected_result: 'Токен присутствует под ключом "token"' },
      { action: '[When] Инициировать защищенный HTTP-запрос', data: 'GET /api/Basket/1', expected_result: 'В заголовках запроса присутствует Authorization: Bearer <token>' },
      { action: '[Then] Перезагрузить страницу', data: 'location.reload()', expected_result: 'Сессия сохранена, профиль активен' }
    ],
    postconditions: 'Сессия сохраняется при перезагрузке.'
  },
  {
    id: 'TC-FE-07',
    title: '[Frontend] Восстановление доступа к аккаунту через контрольный вопрос (Forgot Password)',
    description: 'Проверка сброса забытого пароля при корректном ответе на секретный вопрос пользователя. Входит в полный регресс.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Customer Authentication")
@allure.story("${ctx.issueKey}: Password Recovery")
@allure.severity("major")
@full-regression
Scenario: Сброс пароля при верном ответе на секретный вопрос
  Given пользователь забыл пароль и перешел на страницу "/#/forgot-password"
  When вводит Email "user@test.com"
  Then в поле контрольного вопроса автоматически подтягивается секретный вопрос пользователя
  When пользователь вводит верный ответ "SecretAnswer", новый пароль "NewPassword123" и подтверждение "NewPassword123"
  And нажимает кнопку "Change"
  Then сервер возвращает HTTP 200 OK
  And отображается зеленый SnackBar "Your password was changed successfully."
  And пользователь может успешно авторизоваться на "/#/login" с новым паролем`,
    covers: ['AC-05', 'F03'],
    type: 'functional',
    severity: 'major',
    priority: 'medium',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'manual',
    tags: ['bdd', 'gherkin', 'allure', 'forgot-password', 'full-regression'],
    preconditions: 'Пользователь user@test.com зарегистрирован с секретным вопросом.',
    steps: [
      { action: '[Given] Открыть страницу восстановления пароля', data: 'URL: /#/forgot-password', expected_result: 'Форма отображается' },
      { action: '[When] Ввести Email пользователя', data: 'user@test.com', expected_result: 'Секретный вопрос подтягивается через API' },
      { action: '[And] Ввести ответ на вопрос и новый пароль', data: 'SecretAnswer / NewPassword123', expected_result: 'Поля валидны' },
      { action: '[And] Нажать кнопку "Change"', data: 'click "Change"', expected_result: 'POST /rest/user/reset-password возвращает 200 OK' },
      { action: '[Then] Проверить сообщение об успехе', data: 'SnackBar', expected_result: 'Зеленый SnackBar "Your password was changed successfully."' }
    ],
    postconditions: 'Пароль пользователя обновлен в БД.'
  },
  {
    id: 'TC-FE-08',
    title: '[Frontend] Смена пароля авторизованным пользователем в настройках профиля',
    description: 'Проверка смены пароля из профиля авторизованного пользователя при вводе корректного текущего пароля. Входит в полный регресс.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("User Profile")
@allure.story("${ctx.issueKey}: Profile Password Management")
@allure.severity("major")
@full-regression
Scenario: Успешная смена пароля в профиле
  Given пользователь авторизован и открыл страницу профиля "/#/profile"
  When вводит корректный текущий пароль "CurrentPass123"
  And вводит новый пароль "NewSecurePass456" и подтверждение "NewSecurePass456"
  And нажимает кнопку "Change Password"
  Then отправляется защищенный запрос POST /rest/user/change-password с Bearer-токеном
  And сервер возвращает статус HTTP 200 OK
  And отображается зеленый SnackBar "Your password was changed successfully."
  And поля формы смены пароля очищаются`,
    covers: ['AC-06', 'F03'],
    type: 'functional',
    severity: 'major',
    priority: 'medium',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'profile', 'password', 'full-regression'],
    preconditions: 'Пользователь авторизован на "/#/profile".',
    steps: [
      { action: '[Given] Открыть форму смены пароля', data: 'URL: /#/profile', expected_result: 'Форма доступна' },
      { action: '[When] Ввести текущий пароль', data: 'CurrentPass123', expected_result: 'Поле заполнено' },
      { action: '[And] Ввести новый пароль и подтверждение', data: 'NewSecurePass456', expected_result: 'Поля валидны' },
      { action: '[And] Нажать кнопку смены пароля', data: 'click "Change Password"', expected_result: 'POST /rest/user/change-password возвращает 200 OK' },
      { action: '[Then] Проверить сообщение и очистку формы', data: 'SnackBar & inputs', expected_result: 'SnackBar об успехе, поля очищены' }
    ],
    postconditions: 'Новый пароль сохранен.'
  },
  {
    id: 'TC-FE-09',
    title: '[Frontend] Блокировка смены пароля при вводе неверного текущего пароля (HTTP 401)',
    description: 'Проверка безопасности: защита от несанкционированной смены пароля при вводе некорректного текущего пароля. Входит в полный регресс.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("User Profile")
@allure.story("${ctx.issueKey}: Profile Password Management")
@allure.severity("critical")
@full-regression
Scenario: Ошибка смены пароля при неверном текущем пароле
  Given пользователь авторизован на странице профиля "/#/profile"
  When вводит неверный текущий пароль "WrongCurrentPass999"
  And вводит новый пароль "NewPassValid123" и подтверждение "NewPassValid123"
  And нажимает кнопку "Change Password"
  Then сервер возвращает HTTP-статус 401 Unauthorized
  And на экране отображается красный SnackBar с ошибкой "Current password is not correct."
  And пароль учетной записи остается неизменным`,
    covers: ['AC-06', 'F03'],
    type: 'security',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'security', 'password', 'full-regression'],
    preconditions: 'Пользователь авторизован на "/#/profile".',
    steps: [
      { action: '[Given] Открыть экран профиля', data: 'URL: /#/profile', expected_result: 'Экран открыт' },
      { action: '[When] Ввести неверный текущий пароль', data: 'WrongCurrentPass999', expected_result: 'Поле заполнено' },
      { action: '[And] Ввести новый пароль', data: 'NewPassValid123', expected_result: 'Поля заполнены' },
      { action: '[And] Отправить форму смены пароля', data: 'click "Change Password"', expected_result: 'Сервер возвращает 401 Unauthorized' },
      { action: '[Then] Проверить уведомление об ошибке', data: 'SnackBar', expected_result: 'Красный SnackBar "Current password is not correct."' }
    ],
    postconditions: 'Пароль не изменен.'
  },
  {
    id: 'TC-FE-10',
    title: '[Frontend] Успешная загрузка валидного изображения аватара профиля (PNG/JPEG до 2 МБ)',
    description: 'Проверка успешной загрузки изображения аватара (до 2MB) и немедленного обновления превью в шапке и профиле. Входит в полный регресс.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("User Profile")
@allure.story("${ctx.issueKey}: Avatar Upload")
@allure.severity("normal")
@full-regression
Scenario: Успешная загрузка аватара и обновление превью
  Given пользователь авторизован и находится в профиле "/#/profile"
  When выбирает файл изображения "valid_avatar.png" размером 250KB (<= 2MB)
  And нажимает кнопку "Upload"
  Then отправляется multipart HTTP-запрос POST /profile/image/file с токеном Authorization
  And сервер возвращает статус HTTP 200 OK с URL нового изображения
  And отображается уведомление "Profile image updated successfully."
  And превью аватара на странице профиля немедленно обновляет атрибут src на новый URL`,
    covers: ['AC-07', 'F03'],
    type: 'functional',
    severity: 'normal',
    priority: 'medium',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'avatar', 'upload', 'full-regression'],
    preconditions: 'Пользователь авторизован на "/#/profile".',
    steps: [
      { action: '[Given] Выбрать файл аватара', data: 'valid_avatar.png (250KB)', expected_result: 'Файл выбран' },
      { action: '[When] Нажать кнопку загрузки', data: 'click "Upload"', expected_result: 'Multipart POST /profile/image/file возвращает 200 OK' },
      { action: '[Then] Проверить отображение нового аватара', data: 'img.profile-avatar', expected_result: 'Превью обновлено, отображен зеленый SnackBar' }
    ],
    postconditions: 'Аватар сохранен на сервере.'
  },
  {
    id: 'TC-FE-11',
    title: '[Frontend] Блокировка загрузки изображения аватара при превышении лимита размера (> 2 МБ)',
    description: 'Проверка клиентской валидации максимального допустимого размера файла аватара. Входит в полный регресс.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("User Profile")
@allure.story("${ctx.issueKey}: Avatar Upload Validation")
@allure.severity("normal")
@full-regression
Scenario: Превышение допустимого размера файла аватара (> 2MB)
  Given пользователь находится на странице профиля "/#/profile"
  When выбирает файл "oversized_photo.jpg" размером 3.5MB (превышает лимит 2MB)
  Then отображается ошибка валидации "File size must not exceed 2MB. Allowed formats: PNG, JPEG."
  And кнопка "Upload" деактивирована
  And отправка сетевого запроса к серверу блокируется клиентом`,
    covers: ['AC-07', 'F02'],
    type: 'functional',
    severity: 'normal',
    priority: 'low',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'manual',
    tags: ['bdd', 'gherkin', 'allure', 'validation', 'file-size', 'full-regression'],
    preconditions: 'Пользователь на странице "/#/profile".',
    steps: [
      { action: '[Given] Выбрать файл более 2MB', data: 'oversized_photo.jpg (3.5MB)', expected_result: 'Файл выбран' },
      { action: '[When] Проверить реакцию валидации', data: 'валидация формы', expected_result: 'Отображена ошибка "File size must not exceed 2MB."' },
      { action: '[Then] Проверить блокировку сетевого вызова', data: 'проверка отправки', expected_result: 'Кнопка заблокирована, запрос не отправлен' }
    ],
    postconditions: 'Файл не загружен.'
  },
  {
    id: 'TC-FE-12',
    title: '[Frontend][Parametrized] Валидация формата и длины мобильного номера телефона при добавлении адреса',
    description: 'Data-driven тестирование граничных значений длины и формата номера телефона (от 10 до 15 цифр) при добавлении адреса доставки. Входит в полный регресс.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Address Book")
@allure.story("${ctx.issueKey}: Delivery Address Management")
@allure.severity("major")
@full-regression
Scenario Outline: Валидация граничных условий номера телефона (10-15 цифр)
  Given пользователь открыл диалог добавления адреса доставки на "/#/address/saved"
  When заполняет обязательные поля (Country, Name, Address, City, ZIP) валидными данными
  And вводит номер мобильного телефона "<phone>" длиной <length> знаков
  And нажимает кнопку "Submit"
  Then валидация поля телефона соответствует "<is_valid>"
  And сервер возвращает статус-код <expected_status>
  And сохранение адреса доставки завершается со статусом "<is_saved>"

  Examples:
    | phone            | length | is_valid | expected_status | is_saved |
    | 123456789        | 9      | false    | 400             | false    |
    | 1234567890       | 10     | true     | 201             | true     |
    | 12345678901      | 11     | true     | 201             | true     |
    | 123456789012345  | 15     | true     | 201             | true     |
    | 1234567890123456 | 16     | false    | 400             | false    |
    | +7-999-ABC-00    | 13     | false    | 400             | false    |`,
    covers: ['AC-08', 'F02', 'F03'],
    type: 'functional',
    severity: 'major',
    priority: 'medium',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'manual',
    tags: ['bdd', 'gherkin', 'allure', 'address', 'bva', 'parametrized', 'full-regression'],
    preconditions: 'Пользователь авторизован, открыт диалог добавления адреса.',
    steps: [
      { action: '[Given] Открыть форму добавления адреса', data: 'Dialog: Add Address', expected_result: 'Диалог открыт' },
      { action: '[When] Заполнить основные поля адреса', data: 'Germany, John, Main 1, Berlin, 10115', expected_result: 'Поля валидны' },
      { action: '[And] Ввести тестовый номер телефона', data: '<phone>', expected_result: 'Валидность телефона: <is_valid>' },
      { action: '[And] Нажать кнопку Submit', data: 'click "Submit"', expected_result: 'Отправлен POST /api/Addresss/, статус: <expected_status>' },
      { action: '[Then] Проверить результат сохранения', data: 'список адресов', expected_result: 'Адрес сохранен: <is_saved>' }
    ],
    postconditions: 'Адрес сохранен только для валидных значений.'
  }
]

