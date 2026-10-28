const js41RegistrationCases = [
  {
    id: 'TC-FE-01',
    title: '[Frontend][Parametrized] Успешная регистрация нового пользователя с валидными форматами Email',
    description: `## 📌 Цель тест-кейса
Параметризованная проверка успешной регистрации нового пользователя на странице /#/register в веб-приложении OWASP Juice Shop с различными валидными форматами email (согласно RFC 5322).
Валидирует, что форма принимает корректные данные, активирует кнопку #registerButton и завершает регистрацию с редиректом на /#/login.

## 🥒 Спецификация BDD Gherkin
\`\`\`gherkin
@allure.epic("OWASP Juice Shop")
@allure.feature("Customer Registration")
@allure.story("${ctx.issueKey}: Успешная регистрация")
@allure.severity("critical")
@smoke @fast-regression @full-regression
Scenario Outline: Успешная регистрация клиента с валидными данными
  Given гость находится на странице регистрации "/#/register"
  When пользователь вводит email "<email>"
  And вводит пароль "<password>" и повторяет "<password>"
  And выбирает секретный вопрос и указывает ответ "<answer>"
  Then кнопка "#registerButton" активна (enabled)
  And после клика происходит редирект на "/#/login"
\`\`\``,
    covers: ['AC-UI-01', 'AC-UI-02', 'AC-UI-07'],
    type: 'smoke',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'smoke', 'parametrized', 'fast-regression', 'full-regression'],
    preconditions: 'Гость открыл форму регистрации /#/register.',
    steps: [
      { action: '[Given] Открыть страницу /#/register', data: '/#/register', expected_result: 'Форма регистрации отображается' },
      { action: '[When] Заполнить валидный email, пароль, повтор пароля и секретный вопрос', data: 'user@juice-sh.op, ValidPass123!', expected_result: 'Поля валидны' },
      { action: '[Then] Нажать кнопку регистрации', data: 'click #registerButton', expected_result: 'Регистрация успешна, редирект на /#/login' }
    ]
  },
  {
    id: 'TC-FE-02',
    title: '[Frontend][Parametrized] Проверка граничных значений длины пароля при регистрации пользователя (BVA: 5-40 символов)',
    description: `## 📌 Цель тест-кейса
Проверка граничных значений длины пароля в форме /#/register согласно правилу AC-UI-03: допустимая длина от 5 до 40 символов включительно.

## 🥒 Спецификация BDD Gherkin
\`\`\`gherkin
@allure.epic("OWASP Juice Shop")
@allure.feature("Customer Registration")
@allure.story("${ctx.issueKey}: Валидация длины пароля")
@allure.severity("critical")
@regress @bva
Scenario Outline: Граничные значения длины пароля
  Given гость находится на странице "/#/register"
  When пользователь вводит пароль длиной <length> символов
  Then состояние валидации поля соответствует <is_valid>
\`\`\``,
    covers: ['AC-UI-03'],
    type: 'functional',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'bva', 'password', 'regress'],
    preconditions: 'Страница /#/register открыта.',
    steps: [
      { action: '[Given] Открыть /#/register', data: '/#/register', expected_result: 'Форма открыта' },
      { action: '[When] Ввести пароли граничной длины (5 и 40 символов)', data: '12345 и строка из 40 символов', expected_result: 'Пароль валиден, ошибки длины нет' },
      { action: '[Then] Проверить валидацию', data: '#passwordControl', expected_result: 'Поле не подсвечено ошибкой' }
    ]
  },
  {
    id: 'TC-FE-03',
    title: '[Frontend] Валидация ошибки при несовпадении пароля и подтверждения пароля ("Passwords do not match")',
    description: `## 📌 Цель тест-кейса
Проверка вывода сообщения об ошибке "Passwords do not match" и блокировки кнопки регистрации при несовпадении значений в полях Password и Repeat Password (AC-UI-04).`,
    covers: ['AC-UI-04'],
    type: 'functional',
    severity: 'major',
    priority: 'high',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'password-mismatch', 'negative', 'regress'],
    preconditions: 'Пользователь на странице /#/register.',
    steps: [
      { action: '[Given] Открыть форму регистрации', data: '/#/register', expected_result: 'Форма отображается' },
      { action: '[When] Ввести пароль и несовпадающий повтор пароля', data: 'Password123! vs DifferentPass456!', expected_result: 'Поле repeat password не совпадает' },
      { action: '[Then] Проверить сообщение об ошибке и кнопку Register', data: 'error text & #registerButton', expected_result: 'Отображается "Passwords do not match", кнопка disabled' }
    ]
  },
  {
    id: 'TC-FE-04',
    title: '[Frontend] Блокировка кнопки Register по умолчанию при пустой форме (#registerButton disabled)',
    description: `## 📌 Цель тест-кейса
Проверка начального состояния кнопки регистрации при открытии формы /#/register: кнопка #registerButton должна быть заблокирована (disabled) до заполнения всех обязательных полей (AC-UI-01).`,
    covers: ['AC-UI-01'],
    type: 'smoke',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'smoke', 'button-state'],
    preconditions: 'Чистая сессия браузера.',
    steps: [
      { action: '[Given] Открыть страницу /#/register', data: '/#/register', expected_result: 'Страница загружена' },
      { action: '[When] Поля формы остаются пустыми', data: 'empty fields', expected_result: 'Поля не заполнены' },
      { action: '[Then] Проверить состояние кнопки #registerButton', data: '#registerButton', expected_result: 'Кнопка disabled' }
    ]
  },
  {
    id: 'TC-FE-05',
    title: '[Frontend] Проверка сообщения об ошибке при некорректном формате Email ("Email is not valid")',
    description: `## 📌 Цель тест-кейса
Проверка реактивной валидации поля Email (#emailControl): при вводе некорректного адреса отображается ошибка "Email is not valid" (AC-UI-02).`,
    covers: ['AC-UI-02'],
    type: 'functional',
    severity: 'major',
    priority: 'high',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'email-validation', 'negative', 'regress', 'fast-regression'],
    preconditions: 'Пользователь на странице /#/register.',
    steps: [
      { action: '[Given] Открыть /#/register', data: '/#/register', expected_result: 'Форма открыта' },
      { action: '[When] Ввести некорректный email без знака @', data: 'invalid-email-format', expected_result: 'Фокус снят с поля email' },
      { action: '[Then] Проверить сообщение валидации', data: 'mat-error', expected_result: 'Отображается "Email is not valid", кнопка disabled' }
    ]
  },
  {
    id: 'TC-FE-06',
    title: '[Frontend] Блокировка кнопки Register при пароле короче 5 символов ("Password must be 5-40 characters long")',
    description: `## 📌 Цель тест-кейса
Негативная проверка нижней границы длины пароля (BVA): при вводе 4 символов выводится ошибка "Password must be 5-40 characters long" и кнопка блокируется (AC-UI-03).`,
    covers: ['AC-UI-03'],
    type: 'functional',
    severity: 'major',
    priority: 'high',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'bva', 'password-min', 'negative', 'regress', 'fast-regression'],
    preconditions: 'Пользователь на /#/register.',
    steps: [
      { action: '[Given] Открыть /#/register', data: '/#/register', expected_result: 'Форма загружена' },
      { action: '[When] Ввести пароль длиной 4 символа', data: '1234', expected_result: 'Пароль короче минимальной границы' },
      { action: '[Then] Проверить валидацию', data: '#passwordControl', expected_result: 'Отображается ошибка длины, кнопка disabled' }
    ]
  },
  {
    id: 'TC-FE-07',
    title: '[Frontend] Блокировка кнопки Register при пароле длиннее 40 символов (BVA: 41 символ)',
    description: `## 📌 Цель тест-кейса
Негативная проверка верхней границы длины пароля (BVA): при вводе 41 символа выводится ошибка превышения максимальной длины (AC-UI-03).`,
    covers: ['AC-UI-03'],
    type: 'functional',
    severity: 'normal',
    priority: 'medium',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'bva', 'password-max', 'negative', 'regress', 'fast-regression'],
    preconditions: 'Пользователь на /#/register.',
    steps: [
      { action: '[Given] Открыть /#/register', data: '/#/register', expected_result: 'Форма открыта' },
      { action: '[When] Ввести пароль длиной 41 символ', data: 'a'.repeat(41), expected_result: 'Длина превышает 40' },
      { action: '[Then] Проверить валидацию', data: '#passwordControl', expected_result: 'Отображается ошибка длины, кнопка disabled' }
    ]
  },
  {
    id: 'TC-FE-08',
    title: '[Frontend] Отображение индикатора надежности пароля при включении тоггла "Show password advice"',
    description: `## 📌 Цель тест-кейса
Проверка UI-контрола mat-slide-toggle ("Show password advice"): при переключении тоггла под полем пароля отображается шкала стойкости пароля (AC-UI-05).`,
    covers: ['AC-UI-05'],
    type: 'functional',
    severity: 'normal',
    priority: 'medium',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'ui-ux', 'password-advice', 'regress', 'fast-regression'],
    preconditions: 'Пользователь на странице /#/register.',
    steps: [
      { action: '[Given] Открыть /#/register', data: '/#/register', expected_result: 'Форма загружена' },
      { action: '[When] Переключить свитч mat-slide-toggle', data: 'click mat-slide-toggle', expected_result: 'Тоггл включен' },
      { action: '[Then] Проверить индикатор стойкости пароля', data: '.mat-progress-bar', expected_result: 'Индикатор стойкости пароля отображается' }
    ]
  },
  {
    id: 'TC-FE-09',
    title: '[Frontend] Обязательность выбора контрольного вопроса из списка Security Questions (mat-select)',
    description: `## 📌 Цель тест-кейса
Проверка обязательности выбора секретного вопроса: если вопрос не выбран из mat-select, форма не считается валидной и кнопка Register заблокирована (AC-UI-06).`,
    covers: ['AC-UI-06'],
    type: 'functional',
    severity: 'major',
    priority: 'high',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'security-question', 'validation', 'regress', 'fast-regression'],
    preconditions: 'Пользователь на /#/register.',
    steps: [
      { action: '[Given] Открыть /#/register', data: '/#/register', expected_result: 'Форма открыта' },
      { action: '[When] Заполнить email, пароль, повтор пароля и ответ, но оставить вопрос невыбранным', data: 'user@test.com, Pass123!, Answer', expected_result: 'Дропдаун вопроса не выбран' },
      { action: '[Then] Проверить кнопку Register', data: '#registerButton', expected_result: 'Кнопка заблокирована (disabled)' }
    ]
  },
  {
    id: 'TC-FE-10',
    title: '[Frontend] Валидация обязательности ответа на секретный вопрос (#securityAnswerControl)',
    description: `## 📌 Цель тест-кейса
Проверка валидатора обязательности поля ответа на секретный вопрос: при пустом #securityAnswerControl регистрация невозможна (AC-UI-06).`,
    covers: ['AC-UI-06'],
    type: 'functional',
    severity: 'major',
    priority: 'high',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'security-answer', 'negative', 'regress', 'fast-regression'],
    preconditions: 'Пользователь на /#/register.',
    steps: [
      { action: '[Given] Открыть /#/register', data: '/#/register', expected_result: 'Форма открыта' },
      { action: '[When] Заполнить все поля кроме ответа на секретный вопрос', data: 'email, password, question', expected_result: 'Поле ответа пусто' },
      { action: '[Then] Проверить кнопку #registerButton', data: '#registerButton', expected_result: 'Кнопка остается disabled' }
    ]
  },
  {
    id: 'TC-FE-11',
    title: '[Frontend] Скрытие ввода пароля (type=\'password\') в полях Password и Repeat Password',
    description: `## 📌 Цель тест-кейса
Проверка безопасности пользовательского ввода согласно NFR-UI-01: символы пароля должны быть скрыты звездочками/точками (атрибут type='password').`,
    covers: ['NFR-UI-01'],
    type: 'security',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'security', 'input-masking', 'regress', 'fast-regression'],
    preconditions: 'Пользователь на странице /#/register.',
    steps: [
      { action: '[Given] Открыть страницу /#/register', data: '/#/register', expected_result: 'Форма открыта' },
      { action: '[When] Проверить DOM-атрибуты полей ввода пароля', data: '#passwordControl, #repeatPasswordControl', expected_result: 'Атрибуты получены' },
      { action: '[Then] Убедиться что type="password"', data: 'attribute type', expected_result: 'type="password" у обоих полей' }
    ]
  },
  {
    id: 'TC-FE-12',
    title: '[Frontend] Доступность формы регистрации по клавиатуре (Tab Navigation & WCAG 2.1 AA)',
    description: `## 📌 Цель тест-кейса
Проверка стандартов доступности NFR-UI-03 (WCAG 2.1 AA): последовательная навигация по полям формы регистрации клавишей Tab.`,
    covers: ['NFR-UI-03'],
    type: 'functional',
    severity: 'normal',
    priority: 'medium',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'registration', 'accessibility', 'wcag', 'keyboard-nav', 'regress', 'fast-regression'],
    preconditions: 'Пользователь на странице /#/register.',
    steps: [
      { action: '[Given] Открыть /#/register', data: '/#/register', expected_result: 'Форма открыта' },
      { action: '[When] Нажимать клавишу Tab последовательно', data: 'key "Tab"', expected_result: 'Фокус последовательно переходит между полями' },
      { action: '[Then] Проверить попадание фокуса на контролы формы', data: 'focused elements', expected_result: 'Фокус проходит Email -> Password -> Repeat Password -> Question -> Answer -> Register' }
    ]
  }
];
