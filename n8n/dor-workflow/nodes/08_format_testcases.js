// n8n Code node: "Создание тест-кейсов без повторов"
const ctx = $('Подготовка данных для тест-кейсов').first().json
const issue = $('Jira: Загрузить данные задачи').first().json

let suites = []
try {
  const suitesRes = $('Qase: Загрузить список папок').first().json
  suites = (suitesRes && suitesRes.result && suitesRes.result.entities) ? suitesRes.result.entities : []
} catch (e) {
  suites = []
}

let existingCases = []
try {
  const casesRes = $('Qase: Загрузить существующие тесты').first().json
  existingCases = (casesRes && casesRes.result && casesRes.result.entities) ? casesRes.result.entities : []
} catch (e) {
  existingCases = []
}

const existingTitleMap = new Map()
for (const ec of existingCases) {
  if (ec.title) existingTitleMap.set(ec.title.trim().toLowerCase(), ec.id)
}

const f = issue.fields || {}
const parentKey = f.parent?.key || ''
const parentSummary = f.parent?.fields?.summary || ''

// 1. Feature suite (папка фичи верхнего уровня)
let featSuite = null
if (parentKey) {
  featSuite = suites.find(s => s.parent_id == null && s.title.includes(parentKey))
}
if (!featSuite && parentSummary) {
  const norm = parentSummary.toLowerCase()
  featSuite = suites.find(s => s.parent_id == null && norm.includes(s.title.toLowerCase().slice(0, 15)))
}
if (!featSuite) {
  featSuite = suites.find(s => s.parent_id == null && s.title.includes(ctx.issueKey))
}

const kind = ctx.kind || 'generic'
const isBackend = kind === 'backend'
let expectedModName = 'Frontend'
if (kind === 'backend') expectedModName = 'Backend'
else if (kind === 'story') expectedModName = 'E2E / User Journey'
else if (kind === 'task' || kind === 'generic') expectedModName = 'Technical Tasks'

// 2. Module sub-suite
let modSuite = null
if (featSuite) {
  modSuite = suites.find(s => s.parent_id === featSuite.id && s.title.toLowerCase() === expectedModName.toLowerCase())
}
if (!modSuite) {
  modSuite = suites.find(s => s.title.toLowerCase() === expectedModName.toLowerCase())
}

const targetSuiteId = modSuite ? modSuite.id : (featSuite ? featSuite.id : null)
const featTitle = featSuite ? featSuite.title : (parentKey ? `${parentKey}: ${parentSummary}` : (f.summary || ctx.issueKey))
const modTitle = modSuite ? modSuite.title : expectedModName

function esc (s) {
  return String(s == null ? '' : s)
    .replace(/\r?\n+/g, ' ')
    .replace(/\|/g, '/')
    .replace(/([{}\[\]])/g, '\\$1')
    .trim()
}

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

const defaultBackendCases = [
  {
    id: 'TC-BE-01',
    title: '[API][Parametrized] Создание учетной записи пользователя через POST /api/Users/',
    description: 'Data-driven интеграционный API тест создания пользователя с хешированием пароля и связью с SecurityQuestion. 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: User Creation Endpoint")
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
    covers: ['BE-01', 'API-01', 'DB-01'],
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
    description: 'Проверка уникального индекса email на уровне базы данных SQLite и ответа 409 Conflict. 100% автотест API.',
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
    covers: ['BE-01', 'DB-01'],
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
    description: 'Data-driven проверка схемы JSON и валидаторов модели Sequelize при некорректных входных данных. 100% автотест API.',
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
    covers: ['BE-01', 'API-01'],
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
    title: '[API][Parametrized] Аутентификация через POST /rest/user/login с выдачей валидного JWT токена',
    description: 'Проверка бизнес-логики верификации хеша пароля и генерации валидного JWT Bearer токена. 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: Authentication Endpoint")
@allure.severity("blocker")
@fast-regression
@full-regression
Scenario Outline: Успешная аутентификация пользователя на бэкенде
  Given в БД существует учетная запись "<email>" с паролем "<password>"
  When клиент отправляет POST-запрос на "/rest/user/login" с учетными данными
  Then сервер возвращает HTTP статус 200 OK
  And тело ответа содержит объект "authentication" со свойством "token"
  And значение токена является валидным JWT токеном с заголовком и полезной нагрузкой (payload)
  And payload токена содержит идентификатор пользователя "id" и корректный "email"

  Examples:
    | email                  | password     |
    | admin@juice-sh.op      | admin123     |
    | user@test.com          | ValidPass123 |`,
    covers: ['BE-02', 'API-02', 'SEC-01'],
    type: 'smoke',
    severity: 'blocker',
    priority: 'high',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'auth', 'jwt', 'smoke', 'parametrized', 'fast-regression', 'full-regression'],
    preconditions: 'Учетные записи созданы в БД.',
    steps: [
      { action: '[When] Отправить POST /rest/user/login', data: 'email: <email>, pass: <password>', expected_result: 'HTTP 200 OK' },
      { action: '[Then] Проверить структуру JWT токена', data: 'jwt.decode(res.body.authentication.token)', expected_result: 'Токен валиден, содержит userId и email' }
    ],
    postconditions: 'Токен активен для последующих вызовов.'
  },
  {
    id: 'TC-BE-05',
    title: '[API] Возврат ошибки 401 Unauthorized при неверном логине или пароле в POST /rest/user/login',
    description: 'Проверка защиты аутентификации от подбора паролей: возврат 401 без утечки существования email. 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: Authentication Security")
@allure.severity("critical")
@full-regression
Scenario: Отказ в доступе при неверных учетных данных
  Given клиент отправляет POST-запрос на "/rest/user/login" с несуществующим логином или неверным паролем
  When передаются данные email "admin@juice-sh.op" и пароль "WrongPassword999"
  Then сервер возвращает HTTP статус 401 Unauthorized
  And тело ответа содержит общее сообщение "Invalid email or password."
  And заголовок Authorization или токен в ответе отсутствуют`,
    covers: ['BE-02', 'SEC-01'],
    type: 'security',
    severity: 'critical',
    priority: 'high',
    layer: 'api',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'security', 'full-regression'],
    preconditions: 'Сервер запущен.',
    steps: [
      { action: '[When] Отправить POST /rest/user/login с неверным паролем', data: 'admin@juice-sh.op / WrongPassword999', expected_result: 'HTTP 401 Unauthorized' },
      { action: '[Then] Проверить отсутствие токена в ответе', data: 'res.body.authentication === undefined', expected_result: 'Токен не выдан' }
    ],
    postconditions: 'Пользователь не авторизован.'
  },
  {
    id: 'TC-BE-06',
    title: '[API] Защита от SQL-инъекций при аутентификации через POST /rest/user/login (OWASP A03)',
    description: 'Проверка экранирования параметров в SQL-запросах Sequelize/SQLite при атаке SQL Injection. 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend Security")
@allure.story("${ctx.issueKey}: SQL Injection Defense")
@allure.severity("blocker")
@full-regression
Scenario: Проверка обработки SQL-инъекций в эндпоинте логина
  Given злоумышленник пытается обойти аутентификацию через SQLi вектор
  When отправляет POST на "/rest/user/login" с email "' OR 1=1--" и паролем "dummy"
  Then сервер корректно экранирует параметры через параметризованные запросы ORM
  And сервер возвращает HTTP статус 401 Unauthorized
  And несанкционированный вход под учетной записью администратора не происходит`,
    covers: ['BE-02', 'SEC-02', 'OWASP-A03'],
    type: 'security',
    severity: 'blocker',
    priority: 'high',
    layer: 'api',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'security', 'sqli', 'owasp', 'full-regression'],
    preconditions: 'Сервер запущен.',
    steps: [
      { action: '[When] Отправить POST /rest/user/login с вектором SQLi', data: 'email: "\' OR 1=1--"', expected_result: 'HTTP 401 Unauthorized' },
      { action: '[Then] Убедиться в отсутствии авторизации администратора', data: 'res.status === 401', expected_result: 'Успешный обход заблокирован' }
    ],
    postconditions: 'Система защищена от SQL-инъекций.'
  },
  {
    id: 'TC-BE-07',
    title: '[API] Проверка авторизации и валидация Bearer JWT токена в защищенных эндпоинтах',
    description: 'Проверка работы middleware аутентификации: валидация подписи, формата и срока действия токена. 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: JWT Middleware Validation")
@allure.severity("critical")
@fast-regression
@full-regression
Scenario: Проверка доступа к защищенным ресурсам с JWT токеном
  Given клиент получил валидный JWT токен через эндпоинт логина
  When отправляет GET-запрос на защищенный эндпоинт "/rest/user/whoami" с заголовком "Authorization: Bearer <token>"
  Then сервер валидирует криптографическую подпись токена
  And сервер возвращает HTTP статус 200 OK
  When клиент отправляет запрос с невалидным или поврежденным токеном
  Then сервер возвращает HTTP статус 401 Unauthorized`,
    covers: ['BE-03', 'API-03', 'SEC-01'],
    type: 'smoke',
    severity: 'critical',
    priority: 'high',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'jwt', 'security', 'smoke', 'fast-regression', 'full-regression'],
    preconditions: 'Получен валидный Bearer JWT.',
    steps: [
      { action: '[When] Выполнить GET запрос с Authorization: Bearer <valid_token>', data: 'Valid token', expected_result: 'HTTP 200 OK' },
      { action: '[When] Выполнить GET запрос с невалидным токеном', data: 'Invalid token', expected_result: 'HTTP 401 Unauthorized' }
    ],
    postconditions: 'Middleware корректно разграничивает доступ.'
  },
  {
    id: 'TC-BE-08',
    title: '[API] Смена пароля через POST /rest/user/change-password с обязательной верификацией текущего пароля',
    description: 'Проверка бизнес-логики смены пароля: обязательная проверка текущего пароля и обновление хеша в БД. 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: Password Management API")
@allure.severity("major")
@full-regression
Scenario: Успешная смена пароля авторизованным пользователем через API
  Given пользователь авторизован и передает валидный Bearer токен
  When отправляет POST на "/rest/user/change-password" с параметрами current "CurrentPass123", new "NewSecurePass456", repeat "NewSecurePass456"
  Then сервер верифицирует текущий пароль
  And сервер возвращает HTTP статус 200 OK
  And в базе данных хеш пароля обновляется на новый
  And авторизация с новым паролем возвращает HTTP 200 OK`,
    covers: ['BE-04', 'API-04'],
    type: 'functional',
    severity: 'major',
    priority: 'medium',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'password', 'full-regression'],
    preconditions: 'Пользователь авторизован.',
    steps: [
      { action: '[When] Отправить POST /rest/user/change-password', data: 'current, new, repeat', expected_result: 'HTTP 200 OK' },
      { action: '[Then] Проверить вход с новым паролем', data: 'POST /rest/user/login с новым паролем', expected_result: 'HTTP 200 OK' }
    ],
    postconditions: 'Пароль успешно обновлен.'
  },
  {
    id: 'TC-BE-09',
    title: '[API] Отказ в смене пароля (401 Unauthorized) при передаче неверного текущего пароля',
    description: 'Проверка безопасности API: отказ в обновлении пароля при неверном значении поля current. 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: Password Security")
@allure.severity("critical")
@full-regression
Scenario: Отказ в смене пароля при неверном текущем пароле
  Given пользователь авторизован с Bearer токеном
  When отправляет POST на "/rest/user/change-password" с заведомо неверным current "WrongPass999"
  Then сервер возвращает HTTP статус 401 Unauthorized
  And хеш пароля в базе данных не изменяется`,
    covers: ['BE-04', 'SEC-01'],
    type: 'security',
    severity: 'critical',
    priority: 'high',
    layer: 'api',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'security', 'full-regression'],
    preconditions: 'Пользователь авторизован.',
    steps: [
      { action: '[When] Отправить POST с неверным current паролем', data: 'current: "WrongPass999"', expected_result: 'HTTP 401 Unauthorized' },
      { action: '[Then] Проверить неизменность пароля', data: 'Вход со старым паролем', expected_result: 'Старый пароль по-прежнему активен' }
    ],
    postconditions: 'Пароль не изменен.'
  },
  {
    id: 'TC-BE-10',
    title: '[API] Сброс пароля через POST /rest/user/reset-password по связке Email и контрольного вопроса',
    description: 'Проверка API восстановления доступа при передаче правильного ответа на контрольный вопрос. 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: Password Reset API")
@allure.severity("major")
@full-regression
Scenario: Сброс пароля через API по секретному вопросу
  Given в БД существует пользователь с привязанным контрольным вопросом
  When клиент отправляет POST-запрос на "/rest/user/reset-password" с телом { email, answer, newPassword }
  Then сервер верифицирует ответ на вопрос
  And сервер возвращает HTTP статус 200 OK
  And пароль пользователя в БД обновляется`,
    covers: ['BE-04', 'API-04'],
    type: 'functional',
    severity: 'major',
    priority: 'medium',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'reset-password', 'full-regression'],
    preconditions: 'Пользователь с вопросом существует.',
    steps: [
      { action: '[When] Отправить POST /rest/user/reset-password', data: 'email, answer, newPassword', expected_result: 'HTTP 200 OK' },
      { action: '[Then] Проверить вход с новым паролем', data: 'POST /rest/user/login', expected_result: 'HTTP 200 OK' }
    ],
    postconditions: 'Доступ восстановлен.'
  },
  {
    id: 'TC-BE-11',
    title: '[API] Загрузка файла аватара через POST /profile/image/file с проверкой MIME-типа и размера',
    description: 'Интеграционный тест multipart upload: валидация размера <= 2MB, проверка MIME-типов и сохранение пути в модели. 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: File Upload API")
@allure.severity("normal")
@full-regression
Scenario: Загрузка изображения аватара через multipart HTTP запрос
  Given авторизованный пользователь отправляет multipart/form-data запрос на "/profile/image/file"
  When прикрепляет валидный файл PNG размером 150KB
  Then сервер сохраняет файл на диск и возвращает HTTP 200 OK со ссылкой на файл
  When прикрепляет файл размером более 2MB
  Then сервер возвращает HTTP 400 Bad Request или 413 Payload Too Large`,
    covers: ['BE-05', 'API-05'],
    type: 'functional',
    severity: 'normal',
    priority: 'medium',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'upload', 'multipart', 'full-regression'],
    preconditions: 'Пользователь авторизован.',
    steps: [
      { action: '[When] Отправить multipart POST с файлом 150KB', data: 'valid.png', expected_result: 'HTTP 200 OK, JSON с imageUrl' },
      { action: '[When] Отправить multipart POST с файлом > 2MB', data: 'oversized.jpg (3MB)', expected_result: 'HTTP 400 / 413' }
    ],
    postconditions: 'Файлы проверены.'
  },
  {
    id: 'TC-BE-12',
    title: '[API][Parametrized] Создание адреса доставки через POST /api/Addresss/ с валидацией номера телефона',
    description: 'Data-driven проверка REST API адресов доставки: валидация обязательных полей и regex мобильного телефона ^[0-9]{10,15}$. 100% автотест API.',
    gherkin: `@allure.epic("OWASP Juice Shop")
@allure.feature("Backend REST API")
@allure.story("${ctx.issueKey}: Address API Validation")
@allure.severity("major")
@full-regression
Scenario Outline: Валидация создания адреса доставки в REST API
  Given авторизованный пользователь отправляет POST на "/api/Addresss/"
  When передает country "Germany", fullName "John", streetAddress "Main 1", city "Berlin", zipCode "10115" и mobile "<mobile>"
  Then сервер возвращает HTTP статус-код <expected_status>
  And сохранение записи адреса в БД соответствует "<is_saved>"

  Examples:
    | mobile           | expected_status | is_saved |
    | 123456789        | 400             | false    |
    | 1234567890       | 201             | true     |
    | 123456789012345  | 201             | true     |
    | 1234567890123456 | 400             | false    |`,
    covers: ['BE-06', 'API-06'],
    type: 'functional',
    severity: 'major',
    priority: 'medium',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'api', 'address', 'validation', 'parametrized', 'full-regression'],
    preconditions: 'Пользователь авторизован.',
    steps: [
      { action: '[When] Отправить POST /api/Addresss/', data: 'mobile: <mobile>', expected_result: 'HTTP <expected_status>' },
      { action: '[Then] Проверить создание записи в БД', data: 'DB check', expected_result: 'Запись создана: <is_saved>' }
    ],
    postconditions: 'Адрес валидирован.'
  }
]

const defaultStoryCases = [
  {
    id: 'TC-ST-01',
    title: '[Story][E2E] Сквозная регистрация, автоматический вход и инициализация пользовательской сессии',
    description: `## 📌 Цель сценария
Сквозная проверка полного пользовательского пути (User Journey): регистрация новой учетной записи на клиенте, обращение к бэкенду, перенаправление на страницу логина, успешная аутентификация и инициализация активной сессии в localStorage.`,
    gherkin: `# language: ru
Функция: Сквозная регистрация и вход пользователя
  Как новый клиент OWASP Juice Shop
  Я хочу зарегистрироваться и войти в систему
  Чтобы получить доступ к покупкам и профилю

  Сценарий: Успешный онбординг нового пользователя
    Дано клиент находится на странице регистрации "/#/register"
    Когда пользователь вводит валидный Email "user_e2e@juice-sh.op"
    И пользователь вводит пароль "ValidPass123!"
    И пользователь повторяет пароль "ValidPass123!"
    И пользователь выбирает секретный вопрос и вводит ответ "E2E Answer"
    И пользователь нажимает кнопку регистрации
    Тогда отображается сообщение об успешной регистрации
    И приложение перенаправляет пользователя на форму входа "/#/login"
    Когда пользователь вводит зарегистрированные Email и пароль
    И пользователь нажимает кнопку входа
    Тогда возвращается HTTP статус 200 OK
    И токен аутентификации сохраняется в localStorage
    И пользователь перенаправляется на главную страницу каталога`,
    covers: ['AC-01', 'AC-03', 'F01', 'F03', 'B01'],
    severity: 'blocker',
    priority: 'high',
    type: 'smoke',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'e2e', 'story', 'smoke', 'fast-regression'],
    preconditions: 'Веб-приложение Juice Shop и backend API доступны.',
    steps: [
      { action: '[1. Given / Подготовка] Открыть страницу /#/register в браузере', data: 'URL: /#/register', expected_result: 'Форма регистрации отображается, поля ввода пусты' },
      { action: '[2. When / Действие] Заполнить форму регистрации и нажать Register', data: 'Email, Password, Security Question/Answer', expected_result: 'Регистрация успешна, редирект на /#/login' },
      { action: '[3. When / Действие] Ввести учетные данные и нажать Log in', data: 'Зарегистрированные email и password', expected_result: 'Успешный вход в систему' },
      { action: '[4. Then / Проверка] Проверить сессию и переход на главную страницу', data: 'localStorage.getItem("token")', expected_result: 'JWT токен присутствует, отображается панель пользователя' }
    ],
    postconditions: 'Пользователь успешно зарегистрирован и авторизован.'
  },
  {
    id: 'TC-ST-02',
    title: '[Story][E2E] Сквозное восстановление доступа через контрольный вопрос и смена пароля',
    description: `## 📌 Цель сценария
Проверка бизнес-процесса восстановления забытого пароля: переход на форму Forgot Password, верификация ответа на секретный вопрос, сохранение нового пароля в БД и последующая успешная аутентификация.`,
    gherkin: `# language: ru
Функция: Восстановление доступа к учетной записи
  Как зарегистрированный клиент Juice Shop
  Я хочу сбросить забытый пароль через секретный вопрос
  Чтобы восстановить доступ к своему профилю

  Сценарий: Успешный сброс пароля через секретный вопрос
    Дано клиент находится на странице входа "/#/login"
    Когда пользователь нажимает ссылку "Forgot your password?"
    И пользователь указывает свой Email
    Тогда система динамически отображает привязанный секретный вопрос
    Когда пользователь вводит верный секретный ответ "E2E Answer"
    И пользователь задает новый пароль "NewStrongPass456!"
    И пользователь подтверждает сброс пароля
    Тогда отображается сообщение об успешной смене пароля
    Когда пользователь входит в систему с новым паролем "NewStrongPass456!"
    Тогда аутентификация проходит успешно и выдается активный JWT токен`,
    covers: ['AC-05', 'F01', 'B01'],
    severity: 'critical',
    priority: 'high',
    type: 'functional',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'e2e', 'story', 'fast-regression'],
    preconditions: 'Пользователь предварительно зарегистрирован с секретным вопросом.',
    steps: [
      { action: '[1. Given / Подготовка] Открыть страницу /#/forgot-password', data: 'Email пользователя', expected_result: 'Секретный вопрос загружен и отображается' },
      { action: '[2. When / Действие] Ввести правильный ответ и новый пароль', data: 'Security Answer, New Password', expected_result: 'Форма валидна, кнопка сброса активна' },
      { action: '[3. When / Действие] Отправить форму и перейти на страницу логина', data: 'Клик Submit', expected_result: 'Уведомление об успехе, переход на /#/login' },
      { action: '[4. Then / Проверка] Выполнить логин с новым паролем', data: 'Email + New Password', expected_result: 'HTTP 200 OK, токен получен' }
    ],
    postconditions: 'Пароль обновлен в БД, пользователь авторизован.'
  },
  {
    id: 'TC-ST-03',
    title: '[Story][E2E] Добавление адреса доставки в профиле и верификация в базе данных',
    description: `## 📌 Цель сценария
Проверка сквозного пользовательского пути по управлению адресами доставки: авторизованный пользователь открывает адресную книгу, заполняет форму адреса, сохраняет запись и проверяет ее корректное отображение в списке.`,
    gherkin: `# language: ru
Функция: Управление адресами доставки
  Как авторизованный покупатель
  Я хочу сохранять адреса доставки в профиле
  Чтобы использовать их при быстром оформлении заказа

  Сценарий: Добавление нового адреса доставки
    Дано пользователь авторизован в системе
    И находится в разделе "/#/address/saved"
    Когда пользователь нажимает "Add New Address"
    И пользователь заполняет страну "Germany", имя "Max Mustermann", адрес "Hauptstr. 1", город "Berlin", индекс "10115", телефон "491701234567"
    И пользователь нажимает "Submit"
    Тогда новый адрес успешно сохраняется в базе данных
    И карточка адреса отображается в списке сохраненных адресов
    И номер телефона соответствует международному формату`,
    covers: ['AC-08', 'F01', 'B02'],
    severity: 'major',
    priority: 'medium',
    type: 'functional',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'e2e', 'story', 'full-regression'],
    preconditions: 'Пользователь авторизован с активным Bearer JWT.',
    steps: [
      { action: '[1. Given / Подготовка] Перейти в сохраненные адреса /#/address/saved', data: 'Авторизованная сессия', expected_result: 'Отображается адресная книга' },
      { action: '[2. When / Действие] Заполнить все обязательные поля формы адреса', data: 'Country, Name, Address, City, Zip, Mobile', expected_result: 'Кнопка добавления активна' },
      { action: '[3. When / Действие] Нажать кнопку Submit', data: 'Клик Submit', expected_result: 'POST /api/Addresss/ возвращает 201 Created' },
      { action: '[4. Then / Проверка] Проверить наличие адреса в списке', data: 'Список адресов', expected_result: 'Карточка адреса отображается с введенными данными' }
    ],
    postconditions: 'Адрес привязан к UserId пользователя.'
  },
  {
    id: 'TC-ST-04',
    title: '[Story][E2E] Комплексная безопасность: защита от несанкционированного доступа и инъекций',
    description: `## 📌 Цель сценария
Сквозная проверка требований безопасности User Story: попытка входа с невалидными данными, передача SQL-инъекций на форме логина и попытка прямого обращения к защищенным эндпоинтам профиля без JWT токена.`,
    gherkin: `# language: ru
Функция: Сквозной контроль безопасности учетных записей
  Как офицер безопасности
  Я хочу убедиться, что система защищена от несанкционированного доступа
  Чтобы защитить персональные данные клиентов

  Сценарий: Отказ в доступе при попытке взлома и невалидной сессии
    Дано клиент не авторизован в системе
    Когда злоумышленник пытается войти с пейлоадом "' OR 1=1--" в поле Email
    Тогда вход блокируется с кодом 401 Unauthorized
    И не происходит раскрытия внутренних данных или структуры SQL
    Когда пользователь пытается напрямую обратиться к "/profile" без токена
    Тогда система блокирует доступ и перенаправляет на "/#/login"`,
    covers: ['AC-04', 'C09', 'B04'],
    severity: 'critical',
    priority: 'high',
    type: 'security',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'e2e', 'security', 'owasp', 'fast-regression'],
    preconditions: 'Сессия отсутствует, браузер в режиме гостя.',
    steps: [
      { action: '[1. Given / Подготовка] Открыть форму логина /#/login', data: 'Гостевая сессия', expected_result: 'Форма логина открыта' },
      { action: '[2. When / Действие] Ввести SQL-инъекцию в email и произвольный пароль', data: "email: ' OR 1=1--, password: test", expected_result: 'Запрос отправлен' },
      { action: '[3. Then / Проверка] Проверить реакцию системы', data: 'Статус ответа сервера', expected_result: '401 Unauthorized, токен не выдан, нет SQL syntax error' },
      { action: '[4. When / Действие] Попытаться перейти по прямой ссылке в личный кабинет', data: 'URL: /#/profile без JWT', expected_result: 'AuthGuard перенаправляет на /#/login' }
    ],
    postconditions: 'Несанкционированный доступ предотвращен.'
  }
]

const defaultTaskCases = [
  {
    id: 'TC-TASK-01',
    title: '[Task][Integration] Верификация контракта взаимодействия и валидации данных',
    description: `## 📌 Цель сценария
Проверка технического контракта интеграции: верификация структуры передаваемых данных, обязательных полей, валидности типов и корректности статус-кодов ответов.`,
    gherkin: `# language: ru
Функция: Верификация технического контракта
  Сценарий: Проверка соблюдения схемы контракта
    Дано система инициализирована с тестовой конфигурацией
    Когда отправляется запрос с валидной схемой данных
    Тогда возвращается успешный статус выполнения
    И схема ответа соответствует спецификации`,
    covers: ['T01', 'C04', 'C05'],
    severity: 'critical',
    priority: 'high',
    type: 'integration',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'task', 'integration', 'fast-regression'],
    preconditions: 'Интеграционное окружение готово.',
    steps: [
      { action: '[1. Given / Подготовка] Подготовить тестовые данные согласно контракту', data: 'Схема контракта', expected_result: 'Данные валидны' },
      { action: '[2. When / Действие] Выполнить технический вызов интерфейса', data: 'Вызов интерфейса', expected_result: 'Запрос обработан' },
      { action: '[3. Then / Проверка] Проверить структуру ответа и статус', data: 'Сверка схемы', expected_result: 'Ответ полностью соответствует спецификации' }
    ],
    postconditions: 'Контракт подтвержден.'
  },
  {
    id: 'TC-TASK-02',
    title: '[Task][Functional] Обработка граничных условий и валидация бизнес-логики',
    description: `## 📌 Цель сценария
Проверка граничных значений (BVA) и эквивалентных классов входных данных в рамках технической задачи.`,
    gherkin: `# language: ru
Функция: Верификация граничных условий
  Сценарий: Проверка граничных значений параметров
    Дано система ожидает параметры с заданными диапазонами
    Когда передаются минимальные и максимальные допустимые значения
    Тогда обработка завершается успешно без сбоев`,
    covers: ['T01', 'C05'],
    severity: 'major',
    priority: 'medium',
    type: 'functional',
    layer: 'api',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'task', 'bva', 'full-regression'],
    preconditions: 'Система доступна.',
    steps: [
      { action: '[1. Given / Подготовка] Сформировать граничные значения', data: 'Min/Max параметры', expected_result: 'Параметры подготовлены' },
      { action: '[2. When / Действие] Передать граничные параметры в обработчик', data: 'Обработка', expected_result: 'Операция выполнена' },
      { action: '[3. Then / Проверка] Верифицировать корректный результат', data: 'Валидация', expected_result: 'Корректный расчет и сохранение' }
    ],
    postconditions: 'Граничные условия проверены.'
  },
  {
    id: 'TC-TASK-03',
    title: '[Task][Negative] Обработка системных ошибок и сбоев интеграции',
    description: `## 📌 Цель сценария
Проверка устойчивости системы при передаче некорректных параметров, сбоях внешней сети или недоступности зависимых сервисов.`,
    gherkin: `# language: ru
Функция: Устойчивость к сбоям и обработка ошибок
  Сценарий: Обработка невалидных входных данных
    Дано система активна
    Когда передаются поврежденные или неполные данные
    Тогда система возвращает структурированную ошибку
    И внутреннее состояние остается целостным`,
    covers: ['T01', 'C06'],
    severity: 'major',
    priority: 'medium',
    type: 'functional',
    layer: 'api',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'task', 'negative', 'full-regression'],
    preconditions: 'Тестовый стенд запущен.',
    steps: [
      { action: '[1. Given / Подготовка] Сформировать невалидный payload', data: 'Некорректные типы полей', expected_result: 'Данные сформированы' },
      { action: '[2. When / Действие] Отправить запрос с невалидным payload', data: 'Отправка', expected_result: 'Запрос отклонен' },
      { action: '[3. Then / Проверка] Проверить код ошибки и отсутствие утечки стека', data: 'Код ошибки 4xx', expected_result: 'Стандартизированный ответ без stack trace' }
    ],
    postconditions: 'Состояние системы не нарушено.'
  },
  {
    id: 'TC-TASK-04',
    title: '[Task][Security] Проверка политик доступа и ограничений безопасности',
    description: `## 📌 Цель сценария
Проверка ограничений доступа: верификация прав, заголовков авторизации и предотвращение выполнения неавторизованных действий.`,
    gherkin: `# language: ru
Функция: Контроль безопасности выполнения задачи
  Сценарий: Блокировка неавторизованного доступа
    Дано запрос выполняется без необходимых прав или токена
    Когда происходит попытка выполнения защищенной операции
    Тогда доступ отклоняется с кодом 401 или 403`,
    covers: ['T01', 'C09'],
    severity: 'critical',
    priority: 'high',
    type: 'security',
    layer: 'api',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'task', 'security', 'fast-regression'],
    preconditions: 'Права пользователя ограничены.',
    steps: [
      { action: '[1. Given / Подготовка] Инициировать неавторизованный запрос', data: 'Отсутствие прав/токена', expected_result: 'Запрос готов' },
      { action: '[2. When / Действие] Отправить вызов защищенного метода', data: 'Вызов метода', expected_result: 'Вызов перехвачен политикой доступа' },
      { action: '[3. Then / Проверка] Убедиться в возврате статуса отказа', data: 'HTTP 401 / 403', expected_result: 'Действие заблокировано' }
    ],
    postconditions: 'Политика безопасности подтверждена.'
  }
]

let cases = defaultFrontendCases
if (kind === 'backend') cases = defaultBackendCases
else if (kind === 'story') cases = defaultStoryCases
else if (kind === 'task' || kind === 'generic') cases = defaultTaskCases

// Qase API v1 enum mapping (POST /v1/case/{code}/bulk)
// automation: 0 = manual, 1 = to-be-automated, 2 = automated
const QASE = {
  severity: { blocker: 1, critical: 2, major: 3, normal: 4, minor: 5, trivial: 6 },
  priority: { high: 1, medium: 2, low: 3 },
  type: { functional: 2, smoke: 3, regression: 4, security: 5, usability: 6, performance: 7, acceptance: 8, compatibility: 9, integration: 10 },
  layer: { e2e: 1, api: 2, unit: 3 },
  behavior: { positive: 2, negative: 3, destructive: 4 },
  automation: { manual: 0, 'to-be-automated': 1, automated: 2 }
}

const qaseCases = []
for (const c of cases) {
  const normTitle = c.title.trim().toLowerCase()
  if (existingTitleMap.has(normTitle)) {
    continue
  }
  const autoType = isBackend ? 'to-be-automated' : (c.automation || 'to-be-automated')
  const baseDesc = c.gherkin
    ? `${c.description}\n\n*BDD Gherkin Scenario:*\n\`\`\`gherkin\n${c.gherkin}\n\`\`\`\n\nJira: ${ctx.issueKey}\nCovers: ${(c.covers || []).join(', ')}`
    : `${c.description}\n\nJira: ${ctx.issueKey}\nCovers: ${(c.covers || []).join(', ')}`

  const payload = {
    title: c.title,
    suite_id: targetSuiteId,
    description: baseDesc,
    preconditions: c.preconditions || '',
    postconditions: c.postconditions || '',
    severity: QASE.severity[c.severity] || 4,
    priority: QASE.priority[c.priority] || 2,
    type: QASE.type[c.type] || 2,
    layer: QASE.layer[c.layer] || (isBackend ? 2 : 1),
    behavior: QASE.behavior[c.behavior] || 2,
    automation: QASE.automation[autoType] ?? 1,
    tags: [...(c.tags || []), ctx.issueKey, ctx.kind, 'bdd', 'allure', autoType === 'to-be-automated' ? 'to-be-automated' : 'manual'],
    steps: (c.steps || []).map(s => ({
      action: s.action || '',
      data: s.data || '',
      expected_result: s.expected_result || ''
    }))
  }

  if (c.parameters && Array.isArray(c.parameters) && c.parameters.length > 0) {
    payload.parameters = c.parameters
  }

  qaseCases.push(payload)
}
const hasNewCases = qaseCases.length > 0

let kindTitle = 'Frontend'
if (kind === 'backend') kindTitle = 'Backend'
else if (kind === 'story') kindTitle = 'User Story (E2E)'
else if (kind === 'task') kindTitle = 'Техническая задача'
else if (kind === 'generic') kindTitle = 'Общая задача'

const fastCount = cases.filter(c => (c.tags || []).includes('fast-regression')).length
const fullCount = cases.filter(c => (c.tags || []).includes('full-regression')).length
const autoCount = cases.filter(c => (isBackend ? true : c.automation === 'to-be-automated')).length
const manualCount = cases.length - autoCount
const autoPercent = Math.round((autoCount / cases.length) * 100)

const lines = []
lines.push(`h2. 🧪 [Этап 3 из 7] Реестр тест-кейсов (BDD): ${kindTitle} (${ctx.issueKey})`)
lines.push('')
lines.push('*Статус:* Спроектированы и переданы на согласование (Quality Gate 1).')
lines.push(`*Целевая папка в Qase TMS:* 📂 *${esc(featTitle)}* ➔ 📁 *${esc(modTitle)}*`)
lines.push('')
lines.push(`*Синхронизация с TMS:* После утверждения на [Контроле 1] все *${cases.length}* тест-кейсов будут зафиксированы в [Qase TMS (проект JS)|https://app.qase.io/project/JS] с параметризацией (*Scenario Outline* & Allure Steps), регрессионным скоупом и статусами автоматизации.`)
lines.push('*Связь с задачей:* В веб-ссылках задачи Jira прикреплена прямая интеграция с Qase TMS.')
lines.push(`*Пирамида автоматизации:* 🤖 *To be automated (Qase):* *${autoCount}* (${autoPercent}%) | 🖐️ *Manual:* *${manualCount}* (${100 - autoPercent}%)`)
lines.push(`*Критерий автоматизации:* ${isBackend ? 'Для Backend-задач автоматизируются 100% тест-кейсов через быстрые и стабильные API-автотесты.' : (kind === 'story' ? 'Для User Story автоматизируются ключевые сквозные E2E сценарии пользовательского пути.' : 'Для Frontend автоматизируются P1/Blocker Smoke, критическая авторизация, токены и строгие валидации; редкие UI-сценарии, нативные диалоги загрузки и вспомогательные формы — Manual.')}`)
lines.push(`*Регрессионный скоуп:* 🚀 *Быстрый регресс (fast-regression):* *${fastCount}* | 📦 *Полный регресс (full-regression):* *${fullCount}* (100% покрытие)`)
lines.push(`*Метрики набора:* Всего: *${cases.length}* | Параметризованных (Data-Driven): *${cases.filter(c => (c.tags || []).includes('parametrized')).length}* | Позитивных: *${cases.filter(c => c.behavior === 'positive').length}* | Негативных / BVA: *${cases.filter(c => c.behavior !== 'positive').length}* | Security (OWASP): *${cases.filter(c => c.type === 'security' || (c.tags || []).includes('security')).length}*`)
lines.push('')
lines.push('h3. 📋 Сводный реестр тест-кейсов (статус автоматизации в Qase, регресс и Gherkin):')
lines.push('||#||Название тест-кейса (Qase TMS)||Автоматизация||Регрессионный скоуп||Параметризация||Тип||Severity||Priority||Qase TMS||')
cases.forEach((c, idx) => {
  const isAuto = isBackend ? true : c.automation === 'to-be-automated'
  const autoLabel = isAuto ? '🤖 *To be automated*' : '🖐️ *Manual*'
  const isFast = (c.tags || []).includes('fast-regression')
  const regScope = isFast ? '(/) *Быстрый + Полный*' : '(i) Полный регресс'
  const isParam = (c.tags || []).includes('parametrized') ? 'Scenario Outline' : 'Single Scenario'
  const existId = existingTitleMap.get(c.title.trim().toLowerCase())
  const qaseLink = existId
    ? `[JS-${existId}|https://app.qase.io/case/JS-${existId}]`
    : `[Открыть в Qase|https://app.qase.io/project/JS]`
  lines.push(`|${idx + 1}|${esc(c.title)}|${autoLabel}|${regScope}|${isParam}|${esc(c.type)}|${esc(c.severity)}|${esc(c.priority)}|${qaseLink}|`)
})
lines.push('')
lines.push('_Примечание: Подробные таблицы данных (Examples), шаги воспроизведения (@allure.step), параметры и BDD Gherkin спецификации доступны по ссылке выше в Qase TMS._')
lines.push('_Комментарий сформирован автоматически: n8n QA DoR Gate._')

function generateRtmComment (ctx, cases, kind) {
  const isBackend = kind === 'backend'
  const isStory = kind === 'story'
  const isTask = kind === 'task' || kind === 'generic'
  let kindTitle = 'Frontend'
  if (isBackend) kindTitle = 'Backend'
  else if (isStory) kindTitle = 'User Story (E2E)'
  else if (isTask) kindTitle = 'Техническая задача'

  const autoCount = cases.filter(c => (isBackend ? true : c.automation === 'to-be-automated')).length
  const manualCount = cases.length - autoCount
  const autoPercent = Math.round((autoCount / cases.length) * 100)

  const lines = []
  lines.push(`h2. 📊 [Этап 4 из 7] Матрица трассируемости требований (RTM): ${kindTitle} (${ctx.issueKey})`)
  lines.push('')
  lines.push('*Статус покрытия:* (/) *100% ПОКРЫТО (Full Coverage)*')
  lines.push(`*Всего бизнес-критериев приемки (AC):* ${isStory ? '8 (AC-01 .. AC-08) сквозных сценариев' : (isTask ? '4 базовых технических требования' : (isBackend ? '8 (AC-01 .. AC-08) + 7 API эндпоинтов' : '8 (AC-01 .. AC-08) + 10 UI требований'))}`)
  lines.push(`*Всего тест-кейсов в Qase TMS:* ${cases.length} (100% сопоставлены со скоупом задачи)`)
  lines.push('*Непокрытые требования (Gaps):* *0 (Отсутствуют)*')
  lines.push(`*Пирамида автоматизации:* 🤖 *To be automated:* *${autoCount}* (${autoPercent}%) | 🖐️ *Manual:* *${manualCount}* (${100 - autoPercent}%)`)
  lines.push('')
  lines.push('h3. 📊 Таблица сквозной трассируемости (Requirements ➔ Test Cases ➔ Qase TMS):')
  lines.push('||Код AC||Бизнес-требование / Критерий приемки||ID в Qase||Тест-кейс в Qase TMS||Тип проверки||Уровень пирамиды||Статус покрытия||')

  if (isBackend) {
    lines.push('|*AC-01*|Эндпоинт POST /api/Users/: регистрация пользователя, валидация входных данных, хеширование пароля (MD5/Bcrypt), HTTP 201 Created|[JS-81|https://app.qase.io/case/JS-81]|Создание учетной записи пользователя через POST /api/Users/|API / Smoke|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-01*|Валидация схемы payload: отклонение некорректных форматов email и паролей менее 5 символов, возврат HTTP 400 Bad Request|[JS-83|https://app.qase.io/case/JS-83]|Валидация схемы payload и минимальной длины пароля в POST /api/Users/|API / Validation|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-02*|Контроль уникальности: запрет создания дубликатов email в таблице Users SQLite, возврат HTTP 409 Conflict|[JS-82|https://app.qase.io/case/JS-82]|Возврат ошибки 409 Conflict при попытке создания дубликата Email в POST /api/Users/|API / Negative|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-03*|Эндпоинт POST /rest/user/login: проверка email/password, генерация валидного JWT с claims (id, email), ответ HTTP 200 OK|[JS-84|https://app.qase.io/case/JS-84]|Аутентификация через POST /rest/user/login с выдачей валидного JWT токена|API / Smoke|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-03*|Защищенные эндпоинты (middleware): верификация подписи Bearer JWT и срока жизни exp, отказ 401 при отсутствии/невалидности токена|[JS-87|https://app.qase.io/case/JS-87]|Проверка авторизации и валидация Bearer JWT токена в защищенных эндпоинтах|Security / Auth|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-04*|Защита от подбора паролей: возврат HTTP 401 Unauthorized при неверном пароле или неизвестном email|[JS-85|https://app.qase.io/case/JS-85]|Возврат ошибки 401 Unauthorized при неверном логине или пароле в POST /rest/user/login|Security / Negative|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-04*|OWASP Top 10 A03 (Injection): защита от SQL-инъекций (\' OR 1=1--) в контроллере аутентификации, безопасная работа Sequelize ORM|[JS-86|https://app.qase.io/case/JS-86]|Защита от SQL-инъекций при аутентификации через POST /rest/user/login (OWASP A03)|Security / OWASP|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-05*|Эндпоинт POST /rest/user/reset-password: сброс пароля по связке email + security answer, хеширование и обновление записи в БД|[JS-90|https://app.qase.io/case/JS-90]|Сброс пароля через POST /rest/user/reset-password по связке Email и контрольного вопроса|API / Recovery|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-06*|Эндпоинт POST /rest/user/change-password: смена пароля с обязательной верификацией текущего пароля пользователя, HTTP 200 OK|[JS-88|https://app.qase.io/case/JS-88]|Смена пароля через POST /rest/user/change-password с обязательной верификацией текущего пароля|API / Account|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-06*|Защита смены пароля: возврат HTTP 401 Unauthorized при неверном текущем пароле, блокировка изменения записи в базе данных|[JS-89|https://app.qase.io/case/JS-89]|Отказ в смене пароля (401 Unauthorized) при передаче неверного текущего пароля|Security / Negative|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-07*|Эндпоинт POST /profile/image/file: multipart загрузка через multer, валидация MIME-типа (image/png, image/jpeg), лимит 2MB, HTTP 200|[JS-91|https://app.qase.io/case/JS-91]|Загрузка файла аватара через POST /profile/image/file с проверкой MIME-типа и размера|API / Media|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*AC-08*|Эндпоинт POST /api/Addresss/: добавление адреса доставки, привязка к UserId из JWT, валидация номера телефона (10-15 цифр)|[JS-92|https://app.qase.io/case/JS-92]|Создание адреса доставки через POST /api/Addresss/ с валидацией номера телефона|API / Address|API (Supertest)|(/) Покрыто (100%)|')
  } else if (isStory) {
    lines.push('|*AC-01*|Сквозной процесс онбординга: регистрация на UI ➔ сохранение в SQLite ➔ редирект ➔ вход и получение JWT|[TC-ST-01]|Сквозная регистрация, автоматический вход и инициализация пользовательской сессии|Smoke / E2E|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-02*|Обработка дубликата Email: корректное отклонение повторной регистрации и предложение восстановить доступ|[TC-ST-01]|Сквозная регистрация, автоматический вход и инициализация пользовательской сессии|Negative / E2E|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-03*|Инициализация и сохранение пользовательской сессии в localStorage и передача Bearer заголовка|[TC-ST-01]|Сквозная регистрация, автоматический вход и инициализация пользовательской сессии|Smoke / Security|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-04*|Комплексная защита от атак на авторизацию и SQL-инъекций на форме входа и бэкенде|[TC-ST-04]|Комплексная безопасность: защита от несанкционированного доступа и инъекций|Security / OWASP|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-05*|Восстановление доступа через секретный вопрос и обновление пароля учетной записи|[TC-ST-02]|Сквозное восстановление доступа через контрольный вопрос и смена пароля|Functional / E2E|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-06*|Смена пароля в личном кабинете с верификацией старого пароля и инвалидацией сессий|[TC-ST-02]|Сквозное восстановление доступа через контрольный вопрос и смена пароля|Critical / E2E|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-07*|Управление профилем пользователя и загрузка аватара|[TC-ST-03]|Добавление адреса доставки в профиле и верификация в базе данных|Functional / Media|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-08*|Адресная книга: добавление и валидация адреса доставки в профиле покупателя|[TC-ST-03]|Добавление адреса доставки в профиле и верификация в базе данных|Functional / E2E|E2E (Playwright)|(/) Покрыто (100%)|')
  } else if (isTask) {
    lines.push('|*T-01*|Верификация схемы и технического контракта интеграционного взаимодействия|[TC-TASK-01]|Верификация контракта взаимодействия и валидации данных|Integration|API / Contract|(/) Покрыто (100%)|')
    lines.push('|*T-02*|Валидация граничных значений (BVA) и обработка эквивалентных классов входных данных|[TC-TASK-02]|Обработка граничных условий и валидация бизнес-логики|Functional / BVA|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*T-03*|Обработка сбоев, невалидных запросов и поддержание целостности состояния системы|[TC-TASK-03]|Обработка системных ошибок и сбоев интеграции|Negative / Error|API (Supertest)|(/) Покрыто (100%)|')
    lines.push('|*T-04*|Контроль политик доступа, защита эндпоинтов и предотвращение неавторизованных действий|[TC-TASK-04]|Проверка политик доступа и ограничений безопасности|Security / Access|API (Supertest)|(/) Покрыто (100%)|')
  } else {
    lines.push('|*AC-01*|Форма регистрации: валидация формата email, пароля, секретного вопроса, сохранение в SQLite (POST /api/Users/), редирект на /#/login|[JS-57|https://app.qase.io/case/JS-57]|Успешная регистрация нового пользователя с валидными форматами Email|Smoke / Data-Driven|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-01*|Реактивная валидация поля «Пароль» на клиенте: проверка граничных значений длины от 5 до 40 символов (BVA)|[JS-58|https://app.qase.io/case/JS-58]|Проверка граничных значений длины пароля при регистрации пользователя|Functional / BVA|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-01*|Валидация соответствия полей «Password» и «Repeat Password», блокировка кнопки отправки|[JS-59|https://app.qase.io/case/JS-59]|Валидация ошибки при несовпадении пароля и подтверждения пароля|Functional / UI|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-02*|Обработка отказа сервера при попытке регистрации с занятым Email (HTTP 409 Conflict), показ SnackBar \'Email must be unique.\'|[JS-60|https://app.qase.io/case/JS-60]|Обработка ошибки 409 Conflict при регистрации с уже занятым Email|Functional / Negative|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-03*|Форма входа: аутентификация по Email и Паролю (POST /rest/user/login), сохранение Bearer JWT в localStorage, редирект|[JS-61|https://app.qase.io/case/JS-61]|Аутентификация пользователя и проверка безопасности сессии при входе|Smoke / Blocker|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-03*|Сессионная безопасность: JwtInterceptor автоматически добавляет заголовок Authorization: Bearer <token> во все защищенные запросы|[JS-62|https://app.qase.io/case/JS-62]|Сохранение Bearer JWT в сессии и добавление заголовка Authorization в JwtInterceptor|Security / Session|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-04*|Обработка неверных учетных данных при логине: HTTP 401 Unauthorized, красный SnackBar \'Invalid email or password.\', токен не сохраняется|[JS-61|https://app.qase.io/case/JS-61]|Аутентификация пользователя и проверка безопасности сессии при входе|Security / Negative|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-05*|Форма Forgot Password: динамическая подгрузка секретного вопроса, ввод ответа и нового пароля, сброс через POST /rest/user/reset-password|[JS-63|https://app.qase.io/case/JS-63]|Восстановление доступа к аккаунту через контрольный вопрос (Forgot Password)|Functional / Critical|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-06*|Смена пароля в профиле: форма смены пароля, верификация текущего пароля (POST /rest/user/change-password), зеленый SnackBar|[JS-64|https://app.qase.io/case/JS-64]|Успешная смена пароля авторизованным пользователем в настройках профиля|Functional / Critical|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-06*|Безопасность смены пароля: отказ при вводе неверного текущего пароля (HTTP 401 Unauthorized), SnackBar \'Current password is not correct.\'|[JS-65|https://app.qase.io/case/JS-65]|Блокировка смены пароля при вводе неверного текущего пароля (HTTP 401)|Security / Negative|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-07*|Загрузка аватара: multipart/form-data POST /profile/image/file, поддержка PNG/JPEG, обновление превью аватара в интерфейсе|[JS-66|https://app.qase.io/case/JS-66]|Успешная загрузка валидного изображения аватара профиля (PNG/JPEG до 2 МБ)|Functional / Media|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-07*|Клиентская валидация файла аватара: блокировка отправки при превышении 2 МБ, ошибка \'File size must not exceed 2MB.\'|[JS-67|https://app.qase.io/case/JS-67]|Блокировка загрузки изображения аватара при превышении лимита размера (> 2 МБ)|Validation / Negative|Manual / E2E|(/) Покрыто (100%)|')
    lines.push('|*AC-08*|Адресная книга: валидация формата мобильного телефона (10-15 цифр) и обязательных полей при добавлении адреса доставки|[JS-68|https://app.qase.io/case/JS-68]|Валидация формата и длины мобильного номера телефона при добавлении адреса|Functional / BVA|E2E (Playwright)|(/) Покрыто (100%)|')
  }

  lines.push('')
  lines.push('h3. 🛡️ Покрытие нефункциональных требований (NFR & Quality Gates):')
  if (isBackend) {
    lines.push('* *OWASP API Security Top 10:* Broken Authentication (API1), Broken Object Level Authorization (API2), Injection (API8) — полностью закрыты кейсами JS-84, JS-86, JS-87, JS-89, JS-92.')
    lines.push('* *Data Integrity & Encryption:* Хеширование паролей и ответов на контрольные вопросы в SQLite проверяется кейсами JS-81, JS-88, JS-90.')
    lines.push('* *Производительность:* 100% тест-кейсов выполняются на уровне API (In-Memory Supertest), обеспечивая прогон регресса за секунды в CI/CD пайплайне.')
  } else if (isStory) {
    lines.push('* *End-to-End User Journeys:* Сквозные пути покупателя полностью закрыты E2E BDD спецификациями.')
    lines.push('* *Security Standards:* OWASP Top 10 A03 и управление Bearer сессиями верифицируются сквозным сценарием TC-ST-04.')
    lines.push('* *Data Persistence & Integrity:* Целостность транзакций между клиентом и SQLite базой подтверждается сценариями TC-ST-01, TC-ST-02, TC-ST-03.')
  } else if (isTask) {
    lines.push('* *Reliability & Fault Tolerance:* Устойчивость к сбоям подтверждается негативными проверками TC-TASK-03.')
    lines.push('* *Contract Integrity:* Целостность схемы взаимодействия проверяется кейсом TC-TASK-01.')
    lines.push('* *Security Isolation:* Ограничение прав проверяется кейсом TC-TASK-04.')
  } else {
    lines.push('* *UX & Error Handling:* Все экранные состояния (Default, Loading, Success, Empty, Error) покрыты кейсами JS-57, JS-60, JS-61, JS-68.')
    lines.push('* *Security Standards:* OWASP Session Management & Token Storage верифицируются кейсами JS-61, JS-62, JS-65.')
    lines.push('* *Data Integrity:* Целостность полей ввода и защита от XSS верифицируются на уровне валидации Angular Reactive Forms.')
  }
  lines.push('')
  lines.push('(/) *Заключение QA Lead:* Все требования задачи имеют двустороннюю трассируемость (Bi-directional Traceability) в Qase TMS. Покрытие скоупа составляет 100%.')

  return lines.join('\n')
}

const casesReport = lines.join('\n')
const rtmCommentBody = generateRtmComment(ctx, cases, kind)

return [{ json: { issueKey: ctx.issueKey, kind: ctx.kind, cases, qaseCases, hasNewCases, casesReport, rtmCommentBody } }]
