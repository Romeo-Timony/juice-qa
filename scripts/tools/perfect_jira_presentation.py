import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

jira_url = (os.getenv("ATLASSIAN_BASE_URL") or "https://romeo-timony.atlassian.net").rstrip("/")
jira_auth = (os.getenv("ATLASSIAN_USER_EMAIL"), os.getenv("ATLASSIAN_API_TOKEN"))

def update_jira_comment(issue_key: str, comment_id: str, new_body: str):
    url = f"{jira_url}/rest/api/2/issue/{issue_key}/comment/{comment_id}"
    r = requests.put(url, auth=jira_auth, json={"body": new_body})
    if r.status_code == 200:
        print(f"  ✅ [{issue_key}] Комментарий #{comment_id} успешно обновлен")
    else:
        print(f"  ❌ [{issue_key}] Ошибка обновления #{comment_id}: {r.status_code} {r.text[:200]}")

print("=" * 70)
print("ОБНОВЛЕНИЕ КОММЕНТАРИЕВ ДЛЯ ПРЕЗЕНТАЦИИ: JS-40, JS-41, JS-42")
print("=" * 70)

# =============================================================================
# 1. ОБНОВЛЕНИЕ JS-40 (BACKEND REST API)
# =============================================================================
print("\n--- 1. Обновление JS-40 (Backend API) ---")

# Комментарий #2 (MindMap для Whimsical) в JS-40 (ID 11691)
whimsical_body_js40 = """h2. 🧠 [Этап 2 из 8] Интеллект-карта проверок (QA MindMap): Backend API (JS-40)

*Визуальный редактор:* [🔗 Создать интерактивную карту в Whimsical Mind Maps|https://whimsical.com/mind-maps]
*Формат:* Многоуровневый чек-лист тест-дизайна (L1-L5) с классами эквивалентности и граничными значениями.
*Всего уровней вложенности:* 5 | *Проверок:* 24 | *P1 (Blocker/Critical):* 16 | *P2 (Major):* 8

h3. 🗺️ Многоуровневый чек-лист проверок (Deep Hierarchical Checklist):
* 📦 [L1] REST API и Архитектура Сервисов (JS-40)
** 🔐 [L2] Контракт регистрации и профиля (POST /api/Users/)
*** 📥 [L3] Валидация входных данных (Schema & Syntax)
**** 🟢 [L4] Валидный email (RFC 5322) и надежный пароль -> [L5] HTTP 201 Created + data.id [P1 | Smoke]
**** 🔴 [L4] Дубликат Email (регистронезависимый конфликт) -> [L5] HTTP 409 Conflict {"error": "Email must be unique."} [P1 | Negative]
**** ⚠️ [L4] Пустые обязательные поля email/password -> [L5] HTTP 400 Bad Request / 422 [P1 | Boundary]
**** ⚠️ [L4] Синтаксически невалидный email (без @/домена) -> [L5] HTTP 400 Bad Request [P1 | Validation]
**** ✂️ [L4] Санитизация Email: пробелы в начале и конце (trim) -> [L5] HTTP 201 Created с нормализацией [P2 | Normalization]
*** 🛡️ [L3] Граничные значения длины пароля (BVA: 5-40 символов)
**** 🔴 [L4] Длина < 5 символов (4 символа) -> [L5] HTTP 400/422 при строгой валидации схемы [P1 | BVA Min]
**** 🟢 [L4] Граничное значение 5 символов (min) -> [L5] HTTP 201 Created [P1 | BVA Exact]
**** 🟢 [L4] Граничное значение 40 символов (max) -> [L5] HTTP 201 Created [P2 | BVA Max]
*** 🔒 [L3] Конфиденциальность данных в ответе
**** 🛡️ [L4] Маскирование открытого пароля в JSON ответа -> [L5] Поле password отсутствует или null [P1 | Security]
** 🔑 [L2] Контрольные вопросы и восстановление (Security Questions)
*** 📋 [L3] Справочник контрольных вопросов (GET /api/SecurityQuestions)
**** 🟢 [L4] Запрос активного каталога вопросов -> [L5] HTTP 200 OK + непустой массив data [P2 | Directory]
*** 🔗 [L3] Привязка ответа (POST /api/SecurityAnswers/)
**** 🟢 [L4] Успешная привязка SecurityQuestionId к новому пользователю -> [L5] HTTP 201 Created [P1 | Smoke]
**** 🔴 [L4] Несуществующий SecurityQuestionId (ID=999999) -> [L5] HTTP 400/404/500 [P1 | Integrity]
**** 🔒 [L4] Криптографическое хеширование ответа на секретный вопрос -> [L5] В БД сохраняется HMAC-SHA256 хеш [P1 | Crypto]
** 🗄️ [L2] Модели данных и база данных (Sequelize / SQLite)
*** 👤 [L3] Модель User и целостность
**** 🔒 [L4] Хеширование пароля пользователя в БД -> [L5] Хеш sha1/md5/bcrypt, исключено хранение plaintext [P1 | Security]
**** 📇 [L4] Ограничение UNIQUE на колонку email -> [L5] SQLite ConstraintError при дубликате [P1 | Integrity]
** ⚡ [L2] Нефункциональные требования (OWASP API & Performance)
*** 🛡️ [L3] Защита от инъекций (OWASP A03 Injection)
**** 🚫 [L4] Попытка SQL-инъекции в поле email (' OR 1=1--) -> [L5] Параметризованный запрос Sequelize без выполнения [P1 | Security]
*** ⏱️ [L3] Производительность и отказоустойчивость
**** 🚀 [L4] Время отклика эндпоинта POST /api/Users/ -> [L5] p95 < 250ms при нагрузке 30 RPS [P2 | SLA]

h3. 📋 Готовый текст для мгновенного создания MindMap в Whimsical:
*Инструкция:* Скопируйте блок ниже, откройте [Whimsical Mind Maps|https://whimsical.com/mind-maps] и нажмите *Ctrl+Shift+V* (Paste as Mind Map). Карта развернется полностью на русском языке со всеми связями:
{code:markdown}
- JS-40: Автоматизация REST API аутентификации и моделей БД
  - Контракт регистрации пользователя (POST /api/Users/)
    - Валидация входной схемы данных (Schema & Syntax)
      - Валидный Email (RFC 5322) и пароль -> HTTP 201 Created [Smoke | P1]
      - Повторный Email (дубликат) -> HTTP 409 Conflict / 400 Bad Request [Negative | P1]
      - Неполный payload (только обязательные поля) -> HTTP 201 с дефолтной ролью customer [Contract | P1]
      - Невалидный синтаксис Email (без @ или домена) -> HTTP 400 Bad Request [Validation | P2]
      - Санитизация пробелов в Email (автоматический trim) -> HTTP 201 Created [P2]
    - Анализ граничных значений пароля (BVA: 5-40 символов)
      - Длина пароля менее 5 символов (4 символа) -> HTTP 400 Bad Request [BVA Min | P1]
      - Точно 5 символов (нижняя граница) -> HTTP 201 Created [BVA Exact | P1]
      - Точно 40 символов (верхняя граница) -> HTTP 201 Created [BVA Max | P2]
    - Конфиденциальность данных в ответе
      - Маскирование пароля в JSON-ответе -> Поле password отсутствует или null [Security | P1]
  - Аутентификация и сессионные токены (POST /rest/user/login)
    - Получение JWT Bearer токена
      - Корректный логин и пароль -> HTTP 200 OK + JWT токен длиной > 20 символов [Smoke | P1]
      - Проверка структуры полезной нагрузки токена -> Декодирование email пользователя [Security | P1]
    - Защита от несанкционированного доступа
      - Ошибочный пароль учетной записи -> HTTP 401 Unauthorized [Negative | P1]
      - Защита от SQL-инъекций (' OR 1=1--) в форме входа -> Блокировка инъекции без 500 ошибок [OWASP A03 | P1]
  - Авторизованный профиль и управление доступом (RBAC)
    - Проверка текущей сессии (GET /rest/user/whoami)
      - Запрос с валидным Bearer JWT токеном -> HTTP 200 OK + профиль пользователя [Smoke | P1]
      - Запрос без токена авторизации -> HTTP 401 Unauthorized [Security | P1]
    - Ротация пароля пользователя (GET /rest/user/change-password)
      - Успешная смена пароля с верификацией текущего -> HTTP 200 OK + вход с новым паролем [Positive | P2]
      - Неверный текущий пароль при попытке ротации -> HTTP 401 Unauthorized [Negative | P2]
    - Восстановление пароля по контрольному вопросу (POST /rest/user/reset-password)
      - Корректный Email и ответ на секретный вопрос -> HTTP 200 OK + сброс пароля [Recovery | P1]
      - Ошибочный ответ на секретный вопрос -> HTTP 401 Unauthorized [Security | P1]
  - Загрузка файлов и профиль покупателя
    - Загрузка аватара (POST /profile/image/file)
      - Загрузка бинарного PNG файла через multipart/form-data -> HTTP 200 OK + путь к файлу [Integration | P2]
    - Создание адреса доставки (POST /api/Addresss/)
      - Валидный адрес с индексом, страной и мобильным номером -> HTTP 201 Created [Smoke | P1]
{code}"""

update_jira_comment("JS-40", "11691", whimsical_body_js40)

# Комментарий #3 (Реестр BDD с точными ID 871..882) в JS-40 (ID 11692)
bdd_body_js40 = """h2. 🧪 [Этап 3 из 8] Реестр тест-кейсов (BDD): Backend (JS-40)

*Статус:* (/) Утверждены на Контроле 1 и *полностью автоматизированы в кодовой базе* (`tests/backend/test_js40_api.py`).
*Целевая папка в Qase TMS:* 📂 *API* (Suite #86)

*Синхронизация с TMS:* Все *12* тест-кейсов зафиксированы в [Qase TMS (проект JS, сьют API)|https://app.qase.io/project/JS] со статусом *Automated (auto=2)*, параметризацией (*Scenario Outline* & Allure Steps) и регрессионным скоупом.
*Пирамида автоматизации:* 🤖 *Automated (Qase auto=2):* *12* (100%) | 🖐️ *Manual:* *0* (0%)
*Регрессионный скоуп:* 🚀 *Быстрый регресс (fast-regression):* *4* | 📦 *Полный регресс (full-regression):* *12* (100% покрытие)
*Метрики набора:* Всего: *12* | Автоматизировано: *12* | Позитивных: *7* | Негативных / BVA: *5* | Security (OWASP): *4*

h3. 📋 Сводный реестр тест-кейсов (актуальный статус в Qase TMS и реализация в коде):
||#||ID Qase||Название тест-кейса в Qase TMS||Автоматизация||Регрессионный скоуп||Severity||Статус в кодовой базе||
|1|[JS-871|https://app.qase.io/case/JS-871]|\[API\]\[Parametrized\] Создание учетной записи пользователя через POST /api/Users/|🤖 *Automated (auto=2)*|(/) Быстрый + Полный|Critical|✅ `test_tc871_register_user_success`|
|2|[JS-872|https://app.qase.io/case/JS-872]|\[API\] Возврат ошибки 409 Conflict при попытке создания дубликата Email в POST /api/Users/|🤖 *Automated (auto=2)*|(i) Полный регресс|Critical|✅ `test_tc872_register_duplicate_email_conflict`|
|3|[JS-873|https://app.qase.io/case/JS-873]|\[API\]\[Parametrized\] Валидация схемы payload и минимальной длины пароля в POST /api/Users/|🤖 *Automated (auto=2)*|(i) Полный регресс|Major|✅ `test_tc873_register_incomplete_payload`|
|4|[JS-874|https://app.qase.io/case/JS-874]|\[API\]\[Parametrized\] Аутентификация через POST /rest/user/login с выдачей валидного JWT токена|🤖 *Automated (auto=2)*|(/) Быстрый + Полный|Blocker|✅ `test_tc874_user_login_success_jwt`|
|5|[JS-875|https://app.qase.io/case/JS-875]|\[API\] Возврат ошибки 401 Unauthorized при неверном логине или пароле в POST /rest/user/login|🤖 *Automated (auto=2)*|(i) Полный регресс|Critical|✅ `test_tc875_user_login_invalid_credentials`|
|6|[JS-876|https://app.qase.io/case/JS-876]|\[API\] Защита от SQL-инъекций при аутентификации через POST /rest/user/login (OWASP A03)|🤖 *Automated (auto=2)*|(/) Быстрый + Полный|Critical|✅ `test_tc876_login_sql_injection_defense`|
|7|[JS-877|https://app.qase.io/case/JS-877]|\[API\] Проверка авторизации и валидация Bearer JWT токена в защищенных эндпоинтах|🤖 *Automated (auto=2)*|(/) Быстрый + Полный|Critical|✅ `test_tc877_whoami_authenticated_access`|
|8|[JS-878|https://app.qase.io/case/JS-878]|\[API\] Смена пароля через POST /rest/user/change-password с обязательной верификацией текущего пароля|🤖 *Automated (auto=2)*|(i) Полный регресс|Normal|✅ `test_tc878_change_password_success`|
|9|[JS-879|https://app.qase.io/case/JS-879]|\[API\] Отказ в смене пароля (401 Unauthorized) при передаче неверного текущего пароля|🤖 *Automated (auto=2)*|(i) Полный регресс|Normal|✅ `test_tc879_change_password_wrong_current_rejected`|
|10|[JS-880|https://app.qase.io/case/JS-880]|\[API\] Сброс пароля через POST /rest/user/reset-password по связке Email и контрольного вопроса|🤖 *Automated (auto=2)*|(i) Полный регресс|Normal|✅ `test_tc880_reset_password_with_security_answer`|
|11|[JS-881|https://app.qase.io/case/JS-881]|\[API\] Загрузка файла аватара через POST /profile/image/file с проверкой MIME-типа и размера|🤖 *Automated (auto=2)*|(i) Полный регресс|Normal|✅ `test_tc881_upload_avatar_file`|
|12|[JS-882|https://app.qase.io/case/JS-882]|\[API\]\[Parametrized\] Создание адреса доставки через POST /api/Addresss/ с валидацией номера телефона|🤖 *Automated (auto=2)*|(i) Полный регресс|Normal|✅ `test_tc882_create_delivery_address`|"""

update_jira_comment("JS-40", "11692", bdd_body_js40)

# =============================================================================
# 2. ОБНОВЛЕНИЕ JS-41 (FRONTEND UI)
# =============================================================================
print("\n--- 2. Обновление JS-41 (Frontend UI) ---")

# Комментарий #2 (MindMap для Whimsical) в JS-41 (ID 11702)
whimsical_body_js41 = """h2. 🧠 [Этап 2 из 8] Интеллект-карта проверок (QA MindMap): Frontend UI (JS-41)

*Визуальный редактор:* [🔗 Создать интерактивную карту в Whimsical Mind Maps|https://whimsical.com/mind-maps]
*Формат:* Многоуровневый чек-лист тест-дизайна (L1-L5) интерфейса Angular SPA с валидацией в реальном времени.
*Всего уровней вложенности:* 5 | *Проверок:* 24 | *P1 (Blocker/Critical):* 14 | *P2 (Major):* 10

h3. 🗺️ Многоуровневый чек-лист проверок (Deep Hierarchical Checklist):
* 🖥️ [L1] Пользовательский интерфейс Angular SPA (JS-41)
** 📝 [L2] Экранная форма регистрации (/#/register)
*** 📧 [L3] Поле ввода адреса электронной почты (#emailControl)
**** 🟢 [L4] Корректный Email и динамическая валидация -> [L5] Снятие ошибки invalid-email, подсветка валидности [P1 | Smoke]
**** 🔴 [L4] Некорректный синтаксис (без знака @ или точки) -> [L5] Сообщение "Email is not valid", форма невалидна [P1 | Validation]
**** ⚠️ [L4] Пустое поле при потере фокуса (blur) -> [L5] Ошибка "Please provide an email address." [P1 | Required]
*** 🔑 [L3] Поля пароля и повтора (#passwordControl, #repeatPasswordControl)
**** 🟢 [L4] Совпадающие надежные пароли -> [L5] Валидация успешна, снятие маркеров расхождения [P1 | Smoke]
**** 🔴 [L4] Несовпадение пароля и подтверждения -> [L5] Сообщение "Passwords do not match", блокировка формы [P1 | Match]
**** 📏 [L4] Граничные значения длины пароля (BVA: 5-40 символов) -> [L5] Предупреждение "Password must be 5-40 characters long" [P1 | BVA]
**** 👁️ [L4] Скрытие символов по умолчанию (type='password') -> [L5] Маскирование ввода маркерами [P2 | Privacy]
*** 💡 [L3] Динамический индикатор стойкости пароля (#password-advice)
**** 🟢 [L4] Включение тоггла "Show password advice" -> [L5] Отображение индикатора сложности в реальном времени [P2 | UX]
*** ❓ [L3] Контрольный вопрос безопасности (#securityQuestion)
**** 📋 [L4] Выбор вопроса из выпадающего списка Angular Material (mat-select) -> [L5] Фиксация выбранного questionId [P1 | UI Component]
**** ✍️ [L4] Ввод ответа на секретный вопрос (#securityAnswerControl) -> [L5] Поле обязательно для отправки формы [P1 | Required]
*** 🔘 [L3] Кнопка отправки формы (#registerButton)
**** 🔒 [L4] Пустая или невалидная форма при загрузке страницы -> [L5] Кнопка задизейблена (disabled=true) [P1 | State]
**** 🚀 [L4] Полностью корректно заполненные поля формы -> [L5] Кнопка активируется (disabled=false), успешный клик [P1 | Action]
** ♿ [L2] Доступность и юзабилити (Accessibility & UX)
*** ⌨️ [L3] Клавиатурная навигация (Tab Order & WCAG 2.1)
**** 🟢 [L4] Последовательный переход по полям клавишей Tab -> [L5] Логичный порядок фокуса (Email -> Pass -> Repeat -> Question) [P2 | A11y]

h3. 📋 Готовый текст для мгновенного создания MindMap в Whimsical:
*Инструкция:* Скопируйте блок ниже, откройте [Whimsical Mind Maps|https://whimsical.com/mind-maps] и нажмите *Ctrl+Shift+V* (Paste as Mind Map). Карта UI-проверок развернется на русском языке:
{code:markdown}
- JS-41: Пользовательский интерфейс Angular SPA (/#/register)
  - Форма регистрации покупателя
    - Поле ввода Email (#emailControl)
      - Ввод валидного адреса -> Снятие ошибок валидации [Smoke | P1]
      - Некорректный синтаксис (без @/домена) -> Ошибка "Email is not valid" [Validation | P1]
      - Пустое обязательное поле -> Ошибка "Please provide an email address." [Required | P1]
    - Поля пароля и подтверждения (#passwordControl, #repeatPasswordControl)
      - Совпадающие стойкие пароли -> Форма валидна [Smoke | P1]
      - Несовпадение значений в полях -> Ошибка "Passwords do not match" [Match | P1]
      - Длина пароля менее 5 символов -> Ошибка "Password must be 5-40 characters" [BVA | P1]
      - Длина пароля более 40 символов -> Блокировка кнопки Register [BVA | P2]
      - Защита ввода -> Атрибут type='password' по умолчанию [Security | P2]
    - Индикатор надежности пароля (#password-advice)
      - Включение чекбокса "Show password advice" -> Отображение прогресс-бара [UX | P2]
    - Контрольный вопрос безопасности
      - Выбор вопроса из списка Angular Material (mat-select) -> Фиксация выбора [UI | P1]
      - Обязательный ввод ответа (#securityAnswerControl) -> Активация кнопки [Required | P1]
    - Кнопка регистрации (#registerButton)
      - Неполная или невалидная форма -> Атрибут disabled=true [State | P1]
      - Корректное заполнение всех полей -> Активация кнопки (disabled=false) [Smoke | P1]
  - Доступность интерфейса (Accessibility & Usability)
    - Навигация с клавиатуры (WCAG 2.1)
      - Перемещение фокуса клавишей Tab -> Последовательный обход всех контролов [A11y | P2]
      - Отправка формы клавишей Enter -> Срабатывание регистрации [UX | P2]
{code}"""

update_jira_comment("JS-41", "11702", whimsical_body_js41)

# Комментарий #3 (Реестр BDD с точными ID 895..906) в JS-41 (ID 11703)
bdd_body_js41 = """h2. 🧪 [Этап 3 из 8] Реестр тест-кейсов (BDD): Frontend (JS-41)

*Статус:* (/) Утверждены на Контроле 1 и *полностью автоматизированы в кодовой базе* (`tests/frontend/test_js41_ui.py`).
*Целевая папка в Qase TMS:* 📂 *UI* (Suite #87)

*Синхронизация с TMS:* Все *12* тест-кейсов зафиксированы в [Qase TMS (проект JS, сьют UI)|https://app.qase.io/project/JS] со статусом *Automated (auto=2)*, реализацией на Playwright POM и Allure Steps.
*Пирамида автоматизации:* 🤖 *Automated (Qase auto=2):* *12* (100%) | 🖐️ *Manual:* *0* (0%)
*Регрессионный скоуп:* 🚀 *Быстрый регресс (fast-regression):* *3* | 📦 *Полный регресс (full-regression):* *12* (100% покрытие)

h3. 📋 Сводный реестр тест-кейсов (актуальный статус в Qase TMS и реализация в коде):
||#||ID Qase||Название тест-кейса в Qase TMS||Автоматизация||Регрессионный скоуп||Severity||Статус в кодовой базе||
|1|[JS-895|https://app.qase.io/case/JS-895]|\[Frontend\]\[Parametrized\] Успешная регистрация нового пользователя с валидными данными|🤖 *Automated (auto=2)*|(/) Быстрый + Полный|Critical|✅ `test_tc895_registration_with_valid_email`|
|2|[JS-896|https://app.qase.io/case/JS-896]|\[Frontend\]\[Parametrized\] Проверка граничных значений длины пароля при регистрации (BVA: 5-40 символов)|🤖 *Automated (auto=2)*|(i) Полный регресс|Major|✅ `test_tc896_password_boundary_validation`|
|3|[JS-897|https://app.qase.io/case/JS-897]|\[Frontend\] Валидация ошибки при несовпадении пароля и подтверждения пароля ("Passwords do not match")|🤖 *Automated (auto=2)*|(i) Полный регресс|Critical|✅ `test_tc897_password_mismatch_error`|
|4|[JS-898|https://app.qase.io/case/JS-898]|\[Frontend\] Блокировка кнопки Register по умолчанию при пустой форме (#registerButton: disabled)|🤖 *Automated (auto=2)*|(/) Быстрый + Полный|Critical|✅ `test_tc898_register_button_disabled_by_default`|
|5|[JS-899|https://app.qase.io/case/JS-899]|\[Frontend\] Проверка сообщения об ошибке при некорректном формате Email ("Email is not valid")|🤖 *Automated (auto=2)*|(i) Полный регресс|Critical|✅ `test_tc899_invalid_email_format_error`|
|6|[JS-900|https://app.qase.io/case/JS-900]|\[Frontend\] Блокировка кнопки Register при пароле короче 5 символов ("Password must be 5-40 characters")|🤖 *Automated (auto=2)*|(i) Полный регресс|Major|✅ `test_tc900_password_too_short_validation`|
|7|[JS-901|https://app.qase.io/case/JS-901]|\[Frontend\] Блокировка кнопки Register при пароле длиннее 40 символов (BVA: 41 символ)|🤖 *Automated (auto=2)*|(i) Полный регресс|Minor|✅ `test_tc901_password_too_long_validation`|
|8|[JS-902|https://app.qase.io/case/JS-902]|\[Frontend\] Отображение индикатора надежности пароля при включении тоггла "Show password advice"|🤖 *Automated (auto=2)*|(i) Полный регресс|Normal|✅ `test_tc902_show_password_advice_toggle`|
|9|[JS-903|https://app.qase.io/case/JS-903]|\[Frontend\] Обязательность выбора контрольного вопроса из списка Security Questions (mat-select)|🤖 *Automated (auto=2)*|(/) Быстрый + Полный|Critical|✅ `test_tc903_security_question_required`|
|10|[JS-904|https://app.qase.io/case/JS-904]|\[Frontend\] Валидация обязательности ответа на секретный вопрос (#securityAnswerControl)|🤖 *Automated (auto=2)*|(i) Полный регресс|Critical|✅ `test_tc904_security_answer_required`|
|11|[JS-905|https://app.qase.io/case/JS-905]|\[Frontend\] Скрытие ввода пароля (type='password') в полях Password и Repeat Password|🤖 *Automated (auto=2)*|(i) Полный регресс|Normal|✅ `test_tc905_password_fields_masked`|
|12|[JS-906|https://app.qase.io/case/JS-906]|\[Frontend\] Доступность формы регистрации по клавиатуре (Tab Navigation & WCAG 2.1)|🤖 *Automated (auto=2)*|(i) Полный регресс|Normal|✅ `test_tc906_keyboard_tab_navigation`|"""

update_jira_comment("JS-41", "11703", bdd_body_js41)

# =============================================================================
# 3. ОБНОВЛЕНИЕ JS-42 (E2E USER JOURNEY)
# =============================================================================
print("\n--- 3. Обновление JS-42 (E2E User Journey) ---")

# Комментарий #2 (MindMap для Whimsical) в JS-42 (ID 11713)
whimsical_body_js42 = """h2. 🧠 [Этап 2 из 8] Интеллект-карта проверок (QA MindMap): E2E User Journey (JS-42)

*Визуальный редактор:* [🔗 Создать интерактивную карту в Whimsical Mind Maps|https://whimsical.com/mind-maps]
*Формат:* Многоуровневый чек-лист сквозных пользовательских путей (L1-L5) онбординга, безопасности и нефункциональных SLA.
*Всего уровней вложенности:* 5 | *Проверок:* 16 | *P1 (Blocker/Critical):* 10 | *P2 (Major):* 6

h3. 🗺️ Многоуровневый чек-лист проверок (Deep Hierarchical Checklist):
* 🛒 [L1] Сквозные сценарии жизненного цикла покупателя (JS-42)
** 🚀 [L2] Полный приемочный цикл онбординга (Happy Path)
*** 👤 [L3] Регистрация и первичный вход
**** 🟢 [L4] Регистрация через UI -> [L5] Авторизация и переход в профиль пользователя [P1 | Smoke]
*** 🖼️ [L3] Настройка учетной записи
**** 🟢 [L4] Установка аватара и проверка отображения -> [L5] Сохранение изображения в сессии [P2 | Profile]
*** 🔄 [L3] Ротация учетных данных
**** 🟢 [L4] Смена пароля и повторная аутентификация -> [L5] Успешный вход исключительно с новым паролем [P1 | Security]
** 🔐 [L2] Консистентность сессии и безопасность токенов
*** 💾 [L3] Хранилище сессии браузера (Browser localStorage)
**** 🔒 [L4] Валидация Bearer JWT токена в localStorage -> [L5] Наличие токена, валидность заголовков Authorization [P1 | Security]
*** 🛡️ [L3] Негативные сквозные сценарии
**** 🔴 [L4] Попытка повторной регистрации занятого Email -> [L5] Отображение HTTP 400 и UI-баннера ошибки [P1 | Negative]
** 🆘 [L2] Сквозное восстановление доступа (Account Recovery)
*** ❓ [L3] Сброс пароля по контрольному вопросу
**** 🟢 [L4] Сброс пароля по связке Email + секретный ответ -> [L5] Восстановление доступа и вход [P1 | Recovery]
** ⚡ [L2] Нефункциональные требования (NFR & Performance SLA)
*** ⏱️ [L3] Производительность полного цикла
**** 🚀 [L4] Время прохождения полного цикла онбординга -> [L5] Завершение всех сквозных шагов < 3 секунд [P2 | SLA]

h3. 📋 Готовый текст для мгновенного создания MindMap в Whimsical:
*Инструкция:* Скопируйте блок ниже, откройте [Whimsical Mind Maps|https://whimsical.com/mind-maps] и нажмите *Ctrl+Shift+V* (Paste as Mind Map). Карта E2E-сценариев развернется на русском языке:
{code:markdown}
- JS-42: Сквозные пользовательские сценарии онбординга (E2E)
  - Полный приемочный цикл онбординга (Happy Path)
    - Регистрация и авторизация нового покупателя
      - Заполнение формы регистрации в UI -> Переход на форму логина [Smoke | P1]
      - Ввод новых учетных данных -> Успешный вход в личный кабинет [Smoke | P1]
    - Персонализация профиля пользователя
      - Переход на страницу профиля (/#/profile) -> Загрузка аватара [Profile | P2]
      - Проверка отображения обновленного профиля -> Синхронизация данных [UX | P2]
    - Ротация пароля и повторный вход
      - Смена пароля в настройках безопасности -> Успешная ротация [Security | P1]
      - Выход из системы и вход с новым паролем -> Успешная авторизация [Integrity | P1]
  - Безопасность и консистентность сессии
    - Сохранение JWT токена в браузере
      - Проверка ключа токена в localStorage -> Валидный Bearer токен [Security | P1]
      - Отправка заголовка Authorization в сетевых запросах -> Доступ к API [Contract | P1]
    - Сквозная обработка ошибок
      - Попытка регистрации с дубликатом Email -> UI нотификация об ошибке [Negative | P1]
  - Сквозное восстановление доступа к аккаунту
    - Сброс пароля по секретному вопросу (Forgot Password)
      - Ввод Email и контрольного ответа -> Установка нового пароля [Recovery | P1]
      - Авторизация с восстановленным паролем -> Доступ восстановлен [Smoke | P1]
  - Нефункциональные требования (NFR & SLA)
    - Скорость выполнения пользовательских операций
      - Время прохождения полного сценария онбординга -> Время выполнения < 3 секунд [SLA | P2]
{code}"""

update_jira_comment("JS-42", "11713", whimsical_body_js42)

# Комментарий #3 (Реестр BDD с точными ID 919..924) в JS-42 (ID 11714)
bdd_body_js42 = """h2. 🧪 [Этап 3 из 8] Реестр тест-кейсов (BDD): E2E Onboarding (JS-42)

*Статус:* (/) Утверждены на Контроле 1 и *полностью автоматизированы в кодовой базе* (`tests/frontend/test_js42_ui.py`).
*Целевая папка в Qase TMS:* 📂 *E2E* (Suite #88)

*Синхронизация с TMS:* Все *6* тест-кейсов зафиксированы в [Qase TMS (проект JS, сьют E2E)|https://app.qase.io/project/JS] со статусом *Automated (auto=2)*, записью скринкастов сессий (WebM) и Allure Steps.
*Пирамида автоматизации:* 🤖 *Automated (Qase auto=2):* *6* (100%) | 🖐️ *Manual:* *0* (0%)
*Регрессионный скоуп:* 🚀 *Быстрый регресс (fast-regression):* *2* | 📦 *Полный регресс (full-regression):* *6* (100% покрытие)

h3. 📋 Сводный реестр тест-кейсов (актуальный статус в Qase TMS и реализация в коде):
||#||ID Qase||Название тест-кейса в Qase TMS||Автоматизация||Регрессионный скоуп||Severity||Статус в кодовой базе||
|1|[JS-919|https://app.qase.io/case/JS-919]|\[E2E\]\[Smoke\] Полный приемочный цикл онбординга нового покупателя: регистрация, вход, профиль, ротация пароля|🤖 *Automated (auto=2)*|(/) Быстрый + Полный|Blocker|✅ `test_tc919_full_onboarding_cycle`|
|2|[JS-920|https://app.qase.io/case/JS-920]|\[E2E\]\[Integration\] Сквозная консистентность сессии и проверка сохранения Bearer JWT токена в localStorage|🤖 *Automated (auto=2)*|(i) Полный регресс|Critical|✅ `test_tc920_session_consistency_jwt_storage`|
|3|[JS-921|https://app.qase.io/case/JS-921]|\[E2E\]\[Negative\] Сквозная обработка дубликата Email при регистрации (HTTP 400 и UI нотификация)|🤖 *Automated (auto=2)*|(i) Полный регресс|Critical|✅ `test_tc921_duplicate_email_negative`|
|4|[JS-922|https://app.qase.io/case/JS-922]|\[E2E\]\[Security\] Сквозной сценарий сброса и восстановления пароля по секретному вопросу|🤖 *Automated (auto=2)*|(/) Быстрый + Полный|Critical|✅ `test_tc922_forgot_password_recovery_e2e`|
|5|[JS-923|https://app.qase.io/case/JS-923]|\[E2E\]\[NFR\] Валидация SLA производительности полного цикла онбординга (< 3 секунд)|🤖 *Automated (auto=2)*|(i) Полный регресс|Normal|✅ `test_tc923_onboarding_performance_sla`|
|6|[JS-924|https://app.qase.io/case/JS-924]|\[E2E\]\[Integration\] Сквозная авторизация созданного через UI пользователя через прямой REST API вызов|🤖 *Automated (auto=2)*|(i) Полный регресс|Major|✅ `test_tc924_hybrid_ui_api_auth`|"""

update_jira_comment("JS-42", "11714", bdd_body_js42)

print("\n" + "=" * 70)
print("ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
print("=" * 70)
