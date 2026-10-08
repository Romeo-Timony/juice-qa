// n8n Code node: "Создание карты проверок"
const ctx = $('Подготовка данных для чек-листа').first().json

function esc (s) {
  return String(s == null ? '' : s)
    .replace(/\r?\n+/g, ' ')
    .replace(/\|/g, '/')
    .replace(/([{}\[\]])/g, '\\$1')
    .trim()
}

const kind = ctx.kind || 'generic'
let title = 'Frontend'
if (kind === 'backend') title = 'Backend'
else if (kind === 'story') title = 'User Story (E2E)'
else if (kind === 'task') title = 'Техническая задача'
else if (kind === 'generic') title = 'Общая задача'

const lines = []
lines.push(`h2. 🧠 [Этап 2 из 7] Интеллект-карта проверок (QA MindMap): ${title} (${ctx.issueKey})`)

if (kind === 'backend') {
  lines.push('*Формат:* Многоуровневая структура MindMap для REST API, контрактов данных, JWT-безопасности и ORM-моделей.')
  lines.push('*Всего проверок:* 24 | *P1 (Blocker/Critical):* 16 | *P2 (Major):* 8 | *Глубина вложенности:* 4 уровня')
  lines.push('')
  lines.push('h3. 🗺️ Древовидная структура интеллект-карты (MindMap Tree):')
  lines.push(`* 📦 *[Root] REST API и Backend-сервисы (${ctx.issueKey})*`)

  // Ветка 1: REST API Аутентификация
  lines.push('** 🔐 *1. REST API эндпоинты аутентификации*')
  lines.push('*** 📥 *1.1 Регистрация пользователя (POST /api/Users/)*')
  lines.push('**** 🟢 Успешное создание записи -> HTTP 201 Created + хеширование пароля _[P1 | Smoke]_')
  lines.push('**** 🔴 Дубликат Email -> HTTP 409 Conflict {"error": "Email must be unique."} _[P1 | Негативный]_')
  lines.push('**** ⚠️ Невалидный формат Email / короткий пароль -> HTTP 400 Bad Request _[P1 | Валидация]_')
  lines.push('*** 🔑 *1.2 Аутентификация и выдача токена (POST /rest/user/login)*')
  lines.push('**** 🟢 Валидные email/password -> HTTP 200 OK + JWT Bearer в authentication.token _[P1 | Smoke]_')
  lines.push('**** 🚫 Неверный логин или пароль -> HTTP 401 Unauthorized (без утечки существования email) _[P1 | Security]_')
  lines.push('**** 🛡️ Защита от SQL-инъекций (\' OR 1=1--) в полях email и password _[P1 | OWASP A03]_')

  // Ветка 2: JWT & Безопасность
  lines.push('** 🛡️ *2. JWT токены и middleware авторизации*')
  lines.push('*** 🔑 *2.1 Валидация Bearer токенов (JwtInterceptor / Auth Middleware)*')
  lines.push('**** 🟢 Валидный токен в заголовке Authorization -> HTTP 200 OK и доступ к ресурсу _[P1 | Security]_')
  lines.push('**** 🚫 Отсутствие заголовка или невалидный токен -> HTTP 401 Unauthorized _[P1 | Security]_')
  lines.push('**** ⏱️ Истекший срок действия токена (exp claim) -> HTTP 401 Token Expired _[P1 | Security]_')
  lines.push('*** 🔒 *2.2 Смена и восстановление пароля*')
  lines.push('**** 🔑 POST /rest/user/change-password: обязательная проверка текущего пароля (HTTP 401 при неверном) _[P1 | Security]_')
  lines.push('**** ❓ POST /rest/user/reset-password: сброс по связке email + security question answer _[P1 | Функциональный]_')

  // Ветка 3: Модели данных и ORM
  lines.push('** 🗄️ *3. Модели данных и база данных (Sequelize ORM)*')
  lines.push('*** 👤 *3.1 Схема модели User*')
  lines.push('**** 📝 Обязательные поля: email, password, SecurityQuestionId, answer _[P1 | Схема БД]_')
  lines.push('**** 🔒 Хеширование паролей криптографической солью (алгоритм bcrypt/hmac) _[P1 | Безопасность]_')
  lines.push('**** 📇 Уникальный индекс (UNIQUE) на поле email на уровне SQLite/Sequelize _[P1 | Целостность]_')
  lines.push('*** 📍 *3.2 Схема модели Address*')
  lines.push('**** 📮 Валидация полей: country, fullName, streetAddress, city, zipcode, mobile _[P2 | Валидация]_')
  lines.push('**** 📱 Регулярное выражение мобильного телефона: ^[0-9]{10,15}$ _[P1 | Валидация]_')

  // Ветка 4: Профиль и медиа
  lines.push('** 🖼️ *4. Сервисы профиля и медиа-файлов*')
  lines.push('*** 📁 *4.1 Загрузка аватара (POST /profile/image/file)*')
  lines.push('**** 🟢 Multipart upload валидного изображения (PNG/JPEG <= 2MB) -> HTTP 200 OK _[P2 | Функциональный]_')
  lines.push('**** ⛔ Файл > 2MB или невалидный MIME-тип -> HTTP 400 Bad Request / 413 Payload Too Large _[P2 | Негативный]_')
  lines.push('**** 🛡️ Защита от Path Traversal при сохранении имени файла _[P1 | OWASP A01]_')

  // Ветка 5: НФТ
  lines.push('** ⚡ *5. Нефункциональные требования к API (НФТ)*')
  lines.push('*** ⏱️ *5.1 Производительность и отказоустойчивость*')
  lines.push('**** 🚀 Время отклика эндпоинтов авторизации p95 < 200ms при нагрузке 50 RPS _[P2 | Performance]_')
  lines.push('**** 🛡️ Обработка внутренних ошибок 500: стандартизированный JSON без раскрытия stack trace _[P1 | Security]_')
  lines.push('**** 🚦 Rate limiting на эндпоинты аутентификации (защита от брутфорса) _[P2 | Security]_')

  lines.push('')
  lines.push('h3. 📊 Текстовая схема интеллект-карты (MindMap Syntax):')
  lines.push('{code:text}')
  lines.push(`mindmap
  root((Backend API (${ctx.issueKey})))
    1. REST API Auth
      POST /api/Users (201/400/409)
      POST /rest/user/login (200/401)
      POST /rest/user/change-password
      POST /rest/user/reset-password
    2. JWT & Middleware
      Bearer token verification
      Signature & exp claims
      SQLi protection in auth
    3. Sequelize Models
      User schema & unique email
      Password hashing with salt
      Address schema & phone regex
    4. Profile & Uploads
      Multipart POST /profile/image/file
      MIME & Size limits (2MB)
      Path traversal protection
    5. NFT & Errors
      Latency p95 < 200ms
      Generic 500 error JSON (no stacktrace)
      Rate limiting`)
  lines.push('{code}')
} else if (kind === 'story') {
  lines.push('*Формат:* Многоуровневая структура MindMap для сквозной пользовательской истории (End-to-End User Journey, UI/UX, контракты сервисов, безопасность и NFR).')
  lines.push('*Всего проверок:* 20 | *P1 (Blocker/Critical):* 14 | *P2 (Major):* 6 | *Глубина вложенности:* 4 уровня')
  lines.push('')
  lines.push('h3. 🗺️ Древовидная структура интеллект-карты (MindMap Tree):')
  lines.push(`* 📦 *[Root] Сквозная пользовательская история (${ctx.issueKey})*`)

  // Ветка 1: User Journey
  lines.push('** 🗺️ *1. Сквозные пользовательские сценарии (End-to-End User Journey)*')
  lines.push('*** 🚀 *1.1 Онбординг и регистрация нового пользователя*')
  lines.push('**** 🟢 Регистрация с валидными данными ➔ редирект на Login ➔ успешный вход ➔ выдача JWT _[P1 | Smoke]_')
  lines.push('**** 🔴 Попытка регистрации с существующим email ➔ сообщение "Email must be unique." ➔ предложение восстановить пароль _[P1 | Негативный]_')
  lines.push('*** 🔑 *1.2 Восстановление доступа и смена пароля*')
  lines.push('**** 🔄 Сброс пароля через секретный вопрос ➔ установка нового пароля ➔ вход с обновленным паролем _[P1 | Critical]_')
  lines.push('**** 🔒 Смена пароля авторизованным пользователем ➔ проверка старого ➔ сохранение ➔ инвалидация устаревших сессий _[P1 | Security]_')
  lines.push('*** 📍 *1.3 Управление профилем и адресами*')
  lines.push('**** 🏠 Добавление адреса доставки в профиле ➔ валидация телефона ➔ отображение в списке сохраненных адресов _[P2 | Функциональный]_')

  // Ветка 2: UI/UX & Формы
  lines.push('** 💻 *2. Пользовательский интерфейс и валидация (Frontend UI/UX)*')
  lines.push('*** 📝 *2.1 Клиентская валидация в реальном времени*')
  lines.push('**** ✉️ Валидация Email (RFC 5322), пароля (5-40 знаков), совпадения паролей _[P1 | Валидация]_')
  lines.push('**** ⚪ Блокировка кнопок действий до полной валидности формы _[P1 | UI]_')
  lines.push('*** 📢 *2.2 Обратная связь и уведомления*')
  lines.push('**** 🟢 SnackBar уведомления об успехе операций с автозакрытием _[P2 | UI]_')
  lines.push('**** 🔴 Информативные сообщения об ошибках без технического жаргона _[P1 | UX]_')

  // Ветка 3: Бэкенд и данные
  lines.push('** ⚙️ *3. Серверная часть и контракты (Backend & Data)*')
  lines.push('*** 🔌 *3.1 REST API и интеграция данных*')
  lines.push('**** 📦 Контракты POST /api/Users, POST /rest/user/login, POST /rest/user/reset-password _[P1 | Контракт]_')
  lines.push('**** 🗄️ Сохранение в SQLite: хеширование паролей, уникальные индексы, целостность связей _[P1 | База данных]_')

  // Ветка 4: Безопасность
  lines.push('** 🛡️ *4. Безопасность и соответствие стандартам (Security & OWASP)*')
  lines.push('*** 🔒 *4.1 Защита учетных записей и сессий*')
  lines.push('**** 🛡️ Защита от SQL-инъекций на всех формах ввода и API-эндпоинтах (OWASP A03) _[P1 | OWASP]_')
  lines.push('**** 🔑 Безопасное хранение JWT, передача в Bearer заголовках, защита от XSS _[P1 | Security]_')

  // Ветка 5: НФТ
  lines.push('** ⚡ *5. Нефункциональные требования (Performance, a11y, i18n)*')
  lines.push('*** 📱 *5.1 Адаптивность и доступность*')
  lines.push('**** 📲 Корректное отображение на Mobile (360px), Tablet (768px), Desktop (1200px+) _[P2 | Адаптивность]_')
  lines.push('**** ♿ Доступность интерфейса по стандарту WCAG 2.1 AA (Tab-навигация, контрастность) _[P2 | a11y]_')
  lines.push('*** 🌍 *5.2 Интернационализация*')
  lines.push('**** 🌐 Поддержка локалей (en/ru) для всех текстов и ошибок _[P2 | i18n]_')

  lines.push('')
  lines.push('h3. 📊 Текстовая схема интеллект-карты (MindMap Syntax):')
  lines.push('{code:text}')
  lines.push(`mindmap
  root((User Story (${ctx.issueKey})))
    1. User Journey
      Онбординг и регистрация
      Вход и JWT сессия
      Сброс пароля (Security Question)
      Смена пароля в профиле
      Управление адресами доставки
    2. UI/UX & Валидация
      Реактивная валидация форм
      Блокировка submit-кнопок
      SnackBar уведомления
      Обработка ошибок (401/409/500)
    3. Backend & Data
      REST API контракты
      Хранение и хеширование в БД
      Целостность связей
    4. Безопасность
      Защита от SQLi (OWASP A03)
      JWT Bearer сессии
      XSS & Content Security
    5. НФТ
      Адаптивность (360/768/1200px)
      WCAG 2.1 AA доступность
      i18n локализация`)
  lines.push('{code}')
} else if (kind === 'task' || kind === 'generic') {
  lines.push('*Формат:* Структура MindMap для технической задачи (архитектура, логика, контракты, надежность и поставка).')
  lines.push('*Всего проверок:* 16 | *P1 (Blocker/Critical):* 10 | *P2 (Major):* 6 | *Глубина вложенности:* 4 уровня')
  lines.push('')
  lines.push('h3. 🗺️ Древовидная структура интеллект-карты (MindMap Tree):')
  lines.push(`* 📦 *[Root] Техническая реализация (${ctx.issueKey})*`)

  // Ветка 1: Архитектура
  lines.push('** 🏗️ *1. Архитектура и компонентный состав*')
  lines.push('*** 🧩 *1.1 Структура модулей и зависимостей* _[P1 | Архитектура]_')
  lines.push('*** ⚙️ *1.2 Конфигурация и переменные окружения* _[P1 | Конфигурация]_')

  // Ветка 2: Логика
  lines.push('** ⚙️ *2. Функциональная реализация и бизнес-правила*')
  lines.push('*** 🎯 *2.1 Основной алгоритм и логика выполнения* _[P1 | Smoke]_')
  lines.push('*** ⚠️ *2.2 Граничные условия и обработка краевых случаев* _[P1 | Валидация]_')

  // Ветка 3: Контракты
  lines.push('** 🔌 *3. Интеграции и контракты данных*')
  lines.push('*** 📡 *3.1 Входные и выходные форматы данных* _[P1 | Контракт]_')
  lines.push('*** 🔄 *3.2 Взаимодействие со смежными компонентами* _[P2 | Интеграция]_')

  // Ветка 4: Безопасность и надежность
  lines.push('** 🛡️ *4. Надежность, безопасность и логирование*')
  lines.push('*** 🛡️ *4.1 Валидация входящих данных и предотвращение инъекций* _[P1 | Security]_')
  lines.push('*** 📝 *4.2 Структурированное логирование и мониторинг ошибок* _[P2 | Observability]_')
  lines.push('*** ⏱️ *4.3 Таймауты, ретраи и отказоустойчивость* _[P2 | Reliability]_')

  // Ветка 5: Поставка
  lines.push('** 🚀 *5. Приемка и CI/CD автоматизация*')
  lines.push('*** 🧪 *5.1 Автоматизированное тестирование (Unit/Integration)* _[P1 | Тестирование]_')
  lines.push('*** 📦 *5.2 Развертывание и проверка обратной совместимости* _[P2 | DevOps]_')

  lines.push('')
  lines.push('h3. 📊 Текстовая схема интеллект-карты (MindMap Syntax):')
  lines.push('{code:text}')
  lines.push(`mindmap
  root((Task (${ctx.issueKey})))
    1. Архитектура
      Модули и компоненты
      Конфигурация окружения
    2. Реализация
      Основной алгоритм
      Граничные условия
    3. Контракты
      Форматы данных
      Интеграция компонентов
    4. Надежность
      Валидация и безопасность
      Логирование и мониторинг
      Отказоустойчивость
    5. Поставка
      Автотесты в CI
      Развертывание`)
  lines.push('{code}')
} else {
  // Frontend по умолчанию
  lines.push('*Формат:* Многоуровневая структура MindMap с ветвлением от бизнес-функций до проверок каждого поля и состояния UI.')
  lines.push('*Всего проверок:* 22 | *P1 (Blocker/Critical):* 14 | *P2 (Major):* 8 | *Глубина вложенности:* 4 уровня')
  lines.push('')
  lines.push('h3. 🗺️ Древовидная структура интеллект-карты (MindMap Tree):')
  lines.push(`* 📦 *[Root] Модуль аутентификации и профиля пользователя (${ctx.issueKey})*`)

  // Ветка 1: Регистрация
  lines.push('** 🔐 *1. Форма регистрации клиента (/#/register)*')
  lines.push('*** 📝 *1.1 Валидация полей ввода (Validation Rules)*')
  lines.push('**** ✉️ Email (RFC 5322, уникальность, макс. 40 символов) _[P1 | Валидация]_')
  lines.push('**** 🔑 Password (длина 5-40 символов, маскирование при вводе) _[P1 | Валидация]_')
  lines.push('**** 🔁 Repeat Password (полное совпадение с паролем) _[P1 | Валидация]_')
  lines.push('**** ❓ Security Question (выбор из списка GET /api/SecurityQuestions/) _[P1 | Функциональный]_')
  lines.push('**** 💬 Security Answer (мин. 1, макс. 50 символов) _[P1 | Валидация]_')
  lines.push('*** 🖥️ *1.2 Состояния пользовательского интерфейса (UI States)*')
  lines.push('**** ⚪ Default State (кнопка "Register" disabled до полной валидности формы) _[P1 | UI]_')
  lines.push('**** 🔄 Loading State (отображение MatProgressSpinner, блокировка повторного клика) _[P2 | UI]_')
  lines.push('**** 🟢 Success State (зеленый SnackBar "Registration completed", редирект на /#/login) _[P1 | Навигация]_')
  lines.push('**** 🔴 Error State (обработка 409 Conflict "Email must be unique.", подсветка полей) _[P1 | Негативный]_')

  // Ветка 2: Аутентификация
  lines.push('** 🚪 *2. Форма входа и управление сессией (/#/login)*')
  lines.push('*** 🔑 *2.1 Аутентификация (POST /rest/user/login)*')
  lines.push('**** 👤 Валидные учетные данные -> HTTP 200 OK + JWT Bearer токен _[P1 | Smoke]_')
  lines.push('**** 🚫 Неверный логин или пароль -> HTTP 401 Unauthorized + красный SnackBar _[P1 | Security]_')
  lines.push('*** 💾 *2.2 Хранение и передача токена*')
  lines.push('**** 📦 Сохранение Bearer JWT в localStorage под ключом "token" _[P1 | Безопасность]_')
  lines.push('**** 🛡️ Передача заголовка Authorization во все защищенные запросы через JwtInterceptor _[P1 | Интеграция]_')
  lines.push('**** 🔄 Сохранение активной сессии пользователя при перезагрузке страницы _[P2 | Функциональный]_')

  // Ветка 3: Профиль пользователя
  lines.push('** 👤 *3. Экран профиля пользователя (/#/profile)*')
  lines.push('*** 🔒 *3.1 Смена пароля (POST /rest/user/change-password)*')
  lines.push('**** 🔑 Обязательная проверка текущего пароля (HTTP 401 при неверном) _[P1 | Безопасность]_')
  lines.push('**** 🆕 Валидация нового пароля (длина 5-40, не совпадает со старым) _[P1 | Валидация]_')
  lines.push('**** 🟢 Успешное изменение -> SnackBar об успехе + очистка полей формы _[P1 | Функциональный]_')
  lines.push('*** 🖼️ *3.2 Загрузка аватара (POST /profile/image/file)*')
  lines.push('**** 📁 Валидный файл (PNG/JPEG <= 2MB) -> HTTP 200 OK + немедленное обновление превью _[P2 | Функциональный]_')
  lines.push('**** ⛔ Файл > 2MB или невалидный формат -> блокировка загрузки + сообщение об ошибке _[P2 | Негативный]_')

  // Ветка 4: Адресная книга
  lines.push('** 📍 *4. Адресная книга и доставка (/#/address/saved)*')
  lines.push('*** 📭 *4.1 Список сохраненных адресов (GET /api/Addresss/)*')
  lines.push('**** 📄 Empty State (информационный блок при отсутствии сохраненных адресов) _[P2 | UI]_')
  lines.push('**** 📋 Табличное отображение карточек сохраненных адресов доставки _[P2 | Функциональный]_')
  lines.push('*** ➕ *4.2 Диалоговое окно добавления нового адреса (POST /api/Addresss/)*')
  lines.push('**** 📱 Валидация мобильного номера телефона (10-15 цифр, regex ^[0-9]{10,15}$) _[P1 | Валидация]_')
  lines.push('**** 📮 Обязательные поля: Страна, ФИО получателя, Адрес, Город, Индекс (3-10 знаков) _[P1 | Валидация]_')

  // Ветка 5: НФТ
  lines.push('** 🌐 *5. Сквозные нефункциональные требования (Cross-cutting)*')
  lines.push('*** 📱 *5.1 Адаптивная верстка (Responsive Layout)*')
  lines.push('**** 📲 Mobile (360px-767px: вертикальный single-column flex-layout) _[P2 | UI/UX]_')
  lines.push('**** 💻 Tablet (768px-1199px: двухколоночный grid-layout для парных полей) _[P2 | UI/UX]_')
  lines.push('**** 🖥️ Desktop (1200px+: центрированная карточка формы шириной 520px) _[P2 | UI/UX]_')
  lines.push('*** ♿ *5.2 Доступность интерфейса (Accessibility / WCAG 2.1 AA)*')
  lines.push('**** ⌨️ Полная навигация только с клавиатуры клавишей Tab по всем полям и кнопкам _[P2 | a11y]_')
  lines.push('**** 🏷️ Атрибуты aria-label и aria-required для экранных дикторов _[P2 | a11y]_')
  lines.push('*** 🌍 *5.3 Интернационализация (i18n)*')
  lines.push('**** 🌐 Подгрузка текстов ошибок, лейблов и подсказок из словарей локализации (en/ru) _[P2 | i18n]_')
  lines.push('*** ⚡ *5.4 Производительность*')
  lines.push('**** ⏱️ Время первичной отрисовки форм FCP < 1.0s, LCP < 2.0s, отклик на ввод < 50ms _[P2 | Performance]_')

  lines.push('')
  lines.push('h3. 📊 Текстовая схема интеллект-карты (MindMap Syntax):')
  lines.push('{code:text}')
  lines.push(`mindmap
  root((Auth & Profile (${ctx.issueKey})))
    1. Регистрация
      Валидация
        Email (RFC 5322)
        Пароль (5-40 знаков)
        Совпадение паролей
        Секретный вопрос/ответ
      UI-состояния
        Кнопка disabled
        Loading spinner
        Success SnackBar
        Error 409 Conflict
    2. Аутентификация
      Вход в систему
        200 OK + JWT Bearer
        401 Unauthorized
      Токены и сессия
        localStorage 'token'
        JwtInterceptor
        Сохранение сессии
    3. Профиль пользователя
      Смена пароля
        Проверка старого
        Валидация нового
      Аватар
        PNG/JPEG до 2MB
        Обновление превью
    4. Адресная книга
      Список адресов
        Empty state
        Карточки адресов
      Диалог добавления
        Телефон 10-15 цифр
        Обязательность полей
    5. НФТ
      Адаптивность (360/768/1200)
      Доступность (WCAG 2.1 AA)
      Локализация (i18n)
      Скорость (LCP < 2s)`)
  lines.push('{code}')
}

lines.push('')
lines.push('_Интеллект-карта сформирована автоматически: n8n QA DoR Gate._')

const commentBody = lines.join('\n')

return [{ json: { issueKey: ctx.issueKey, kind: ctx.kind, commentBody } }]
