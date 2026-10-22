# [Jira Architecture] Декомпозиция задач: Регистрация нового пользователя

> **Родительский Epic:** `JS-1: User Management & Authentication`  
> **Связанная спецификация Confluence:** `[Confluence Spec] Функциональная спецификация: Регистрация нового пользователя`  
> **Подход:** Vertical Story + Layered Task Delivery (API / UI / E2E)  

---

## 📋 Иерархия задач в Jira

```text
[EPIC] JS-1: User Management & Authentication
  │
  └── [STORY] JS-100: Регистрация нового покупателя через Email и пароль
        │
        ├── [TASK] JS-101: [API] Автоматизация API-контрактов и валидаций POST /api/Users
        │     └── [SUB-TASK / BUG] (при падении): Дефекты API слоя
        │
        ├── [TASK] JS-102: [UI] Автоматизация формы регистрации и валидации полей
        │     └── [SUB-TASK / BUG] (при падении): Дефекты клиентской формы
        │
        └── [TASK] JS-103: [E2E] Сквозные сценарии, безопасность и граничные кейсы регистрации
              └── [SUB-TASK / BUG] (при падении): Дефекты интеграционного потока
```

---

## 1. STORY: JS-100 — Регистрация нового покупателя через Email и пароль

* **Тип:** `Story`
* **Приоритет:** `High`
* **Story Points:** 5
* **Описание:**  
  *Как новый покупатель интернет-магазина Juice Shop, я хочу зарегистрироваться в системе с уникальным email, паролем и секретным вопросом, чтобы получить защищенный доступ к профилю и заказам.*
* **DoR (Definition of Ready):**
  - [x] Функциональная спецификация утверждена в Confluence.
  - [x] Описаны все поля, валидаторы и тексты сообщений об ошибках.
  - [x] Зафиксированы API контракты (`POST /api/Users/`, `GET /api/SecurityQuestions/`).
  - [x] Заведены 3 дочерние инженерные таски (API, UI, E2E).
* **DoD (Definition of Done):**
  - [ ] Все 3 инженерные таски (JS-101, JS-102, JS-103) переведены в статус `Done`.
  - [ ] 100% тест-кейсов в Qase TMS имеют статус `Passed`.
  - [ ] Отсутствуют открытые блокирующие дефекты (`Sub-task: Bug`).

---

## 2. TASK: JS-101 — [API] Автоматизация API-контрактов и валидаций POST /api/Users

* **Тип:** `Task` (Связана с JS-100)
* **Компоненты:** `Backend`, `API-Automation`, `Pydantic-Contracts`
* **Файл автотестов:** `tests/api/auth/test_user_registration_api.py`
* **Скоуп автоматизации (Pytest + Requests + Pydantic v2):**
  1. `test_register_user_success_201`: отправка валидного тела -> статус 201 Created -> валидация схемы `UserRegistrationResponse` (наличие полей `id`, `email`, `role='customer'`, `isActive=true`).
  2. `test_security_questions_list_200`: проверка эндпоинта `GET /api/SecurityQuestions/` -> статус 200 -> наличие 14 стандартных вопросов.
  3. `test_register_duplicate_email_400`: повторная регистрация с тем же email -> статус 400 Bad Request -> тело ошибки содержит `email must be unique`.
  4. `test_register_missing_security_question_link`: проверка связки пользователя с таблицей `SecurityAnswers` в SQLite.
* **DoR для таски:** Confluence API контракт зафиксирован, тестовый сервер доступен на `localhost:3000`.
* **DoD для таски:** 
  - [ ] 100% API автотестов зеленые.
  - [ ] Pydantic v2 модели описаны в `schemas/models.py`.
  - [ ] Кейсы в Qase TMS переведены в статус `Automated`.

---

## 3. TASK: JS-102 — [UI] Автоматизация формы регистрации и валидации полей

* **Тип:** `Task` (Связана с JS-100)
* **Компоненты:** `Frontend`, `UI-Automation`, `Playwright`
* **Файлы реализации:** `pages/register_page.py`, `tests/ui/auth/test_auth_ui.py`
* **Скоуп автоматизации (Playwright Page Object):**
  1. `test_register_button_initially_disabled`: при первой загрузке страницы кнопка `#registerButton` заблокирована.
  2. `test_email_field_required_and_format_validation`: проверка появления ошибки *"Please provide an email address."* при клике и потере фокуса, и ошибки *"Email address is not valid."* при вводе некорректного формата.
  3. `test_password_length_boundary_validation`: проверка отображения ошибки *"Password must be 5-40 characters long."* при вводе < 5 символов.
  4. `test_password_mismatch_validation`: ввод разных значений в поля пароля и подтверждения -> ошибка *"Passwords do not match"*.
  5. `test_password_advice_toggle_expansion`: клик по свитчу `Show password advice` -> разворачивание блока `app-password-strength-info`.
  6. `test_security_question_selection`: открытие выпадающего списка -> выбор одного из 14 вопросов -> проверка сохранения в форме.
  7. `test_successful_ui_registration_flow`: заполнение всех полей -> активация кнопки `#registerButton` -> клик -> появление уведомления об успехе -> редирект на `/#/login`.
* **DoD для таски:**
  - [ ] Page Object `RegisterPage` покрывает все контролы формы.
  - [ ] UI тесты проходят без флакования (Green run).
  - [ ] Запись видеосессий Playwright (`.webm`) и скриншоты проверены.

---

## 4. TASK: JS-103 — [E2E] Сквозные сценарии, безопасность и граничные кейсы регистрации

* **Тип:** `Task` (Связана с JS-100)
* **Компоненты:** `E2E-Journeys`, `Edge-Cases`, `Security-QA`
* **Файл автотестов:** `tests/e2e/auth/test_registration_journey.py`
* **Скоуп сложных сценариев и редких кейсов:**
  1. `test_full_customer_onboarding_journey`:
     - Регистрация нового покупателя через UI.
     - Авторизация под созданными учетными данными на странице `/#/login`.
     - Проверка появления email в меню `Account` шапки сайта.
     - Добавление товара в корзину под новой сессией.
  2. `test_duplicate_email_ui_error_banner`:
     - Попытка зарегистрировать уже существующего пользователя через UI.
     - Проверка всплывающего красного баннера ошибки с текстом сервера.
     - Проверка, что форма не очистилась полностью, а пользователь остался на экране регистрации.
  3. `test_registration_with_sql_injection_payload`:
     - Специфика OWASP Juice Shop: отправка пейлоада `' or 1=1--` в поле email и проверка реакции системы (перехват серверной ошибки / санитизация).
  4. `test_registration_modal_interruptions`:
     - Регистрация пользователя в условиях появления поверх модального окна Welcome Dialog и Cookie Consent (проверка устойчивости автотестов к баннерам).
* **DoD для таски:**
  - [ ] Сквозной сценарий регистрации и входа успешно завершается в headless и headed режимах.
  - [ ] Отработаны негативные серверные ответы.
  - [ ] Результаты прикреплены к отчету Allure.

---

## 5. Шаблон Sub-task при обнаружении дефекта (Bug Template)

Если во время нахождения таски в колонке **«В тестировании»** падает тест, оформляется сабтаска:

* **Issue Type:** `Sub-task` (или `Bug`)
* **Parent Issue:** `JS-101` / `JS-102` / `JS-103`
* **Summary:** `[UI-Bug] Кнопка Register остается неактивной при вставке пароля из буфера обмена`
* **Поля описания:**
  ```markdown
  ### Предусловия:
  Открыта страница http://localhost:3000/#/register, баннеры закрыты.

  ### Шаги воспроизведения:
  1. Ввести валидный email: test@juice-sh.op
  2. Вставить валидный пароль "Pass1234!" через Ctrl+V в оба поля пароля.
  3. Выбрать секретный вопрос и заполнить ответ.

  ### Фактический результат:
  Кнопка Register остается disabled, так как событие paste не вызвало перерасчет reactive form.

  ### Ожидаемый результат:
  Форма переходит в статус valid, кнопка Register становится кликабельной.

  ### Вложения:
  - Скриншот: register_failure.png
  - Видео Playwright: video_test_run_12.webm
  ```
