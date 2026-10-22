# [Confluence Living Spec] Функциональная спецификация: Регистрация нового пользователя (User Registration)

> **Статус:** Ready for Dev & QA (Готово к разработке и тестированию)  
> **Пространство Confluence:** `JS` (OWASP Juice Shop)  
> **Родительский Эпик:** `JS-1: User Management & Authentication`  
> **Связанная User Story:** `JS-100: Регистрация нового покупателя через Email и пароль`  
> **Источники требований:**  
> 1. Внутренняя проектная документация: `confluence_spec_163985.txt` (Бизнес-правила BR-AUTH-01 – BR-AUTH-04).  
> 2. Внутренняя архитектура и логика middleware: `server.ts` (эндпоинт `/api/Users`, `verify.ts`).  
> 3. Архитектура челленджей безопасности: `data/static/challenges.yml` (`registerAdminChallenge`, `passwordRepeatChallenge`, `emptyUserRegistration`).  
> 4. Лайв-верификация UI через Playwright: `frontend/src/app/register/` (селекторы, реактивные ошибки, состояния модалок).  

---

## 1. Бизнес-контекст и цели (Business Context & Value)

* **Проблема:** Доступ к оформлению заказов, сохранению персональной корзины, адресов доставки и отслеживанию покупок требует защищенного аккаунта покупателя.
* **Бизнес-цель:** Предоставить новому пользователю быстрый, понятный и безопасный механизм создания учетной записи в интернет-магазине Juice Shop.
* **User Story:**
  > **Как** новый покупатель интернет-магазина Juice Shop,  
  > **Я хочу** создать персональный аккаунт, указав адрес электронной почты, надежный пароль и секретный контрольный вопрос,  
  > **Чтобы** безопасно авторизовываться в магазине, сохранять историю покупок и оформлять доставку товаров.

---

## 2. Бизнес-правила (Business Rules из внутренней документации)

* **BR-AUTH-01 (Уникальность):** Email пользователя должен быть уникальным в системе (case-insensitive). Попытка регистрации дубликата блокируется бэкендом (400 Bad Request / `email must be unique`).
* **BR-AUTH-02 (Длина пароля):** Пароль должен содержать минимум 5 символов (границы 5–40 символов). Поддерживается отображение интерактивного индикатора стойкости пароля (`Show password advice`).
* **BR-AUTH-03 (Контрольный вопрос):** Пользователь обязан выбрать контрольный вопрос из справочника (14 доступных вопросов) и предоставить непустой ответ. Вопрос фиксируется при регистрации и не подлежит изменению.
* **BR-AUTH-04 (Санитизация ввода):** На сервере перед обработкой применяется тримминг пробелов (`email.trim()`, `password.trim()`, `passwordRepeat.trim()`).
* **BR-AUTH-05 (Непустые поля):** Передача пустых строк в полях email или password возвращает ошибку `400 Invalid email/password cannot be empty`.

---

## 3. Границы скоупа (In-Scope vs Out-of-Scope)

### Входит в скоуп (In-Scope)
1. **Клиентский интерфейс (UI) `/#/register`:**
   - Компонент `RegisterComponent`.
   - Поля ввода: Email, Пароль, Подтверждение пароля, Выпадающий список секретного вопроса, Ответ на секретный вопрос.
   - Свитч отображения расширенных рекомендаций по надежности пароля (`Show password advice`).
   - Динамическая реактивная валидация Angular с блокировкой кнопки отправки (`#registerButton`).
   - Ссылка на форму авторизации (`Already a customer?` -> `/#/login`).
   - Обработка входных перекрытий (Welcome Dialog, Cookie Consent).
2. **Серверный интерфейс (REST API):**
   - `GET /api/SecurityQuestions/`: получение справочника из 14 контрольных вопросов.
   - `POST /api/Users/`: регистрация сущности пользователя в БД SQLite (`Users`).
3. **Безопасность и хранение данных:**
   - Хэширование пароля на бэкенде с солью (bcrypt/HMAC-SHA256).
   - Создание записи в таблице `SecurityAnswers` со связкой `UserId`, `SecurityQuestionId` и хэшированным ответом.

### Не входит в скоуп (Out-of-Scope)
- Аутентификация и выпуск JWT токена (отдельная Story: «Авторизация пользователя»).
- Двухфакторная аутентификация TOTP 2FA (отдельная Story: «2FA Security»).
- Вход через сторонние провайдеры (Google OAuth).
- Восстановление пароля по секретному вопросу (отдельная Story: «Сброс пароля»).

---

## 4. Спецификация UI-интерфейса (Верифицировано через Playwright)

| Элемент UI | Селектор / Локатор | Тип | Правило валидации | Текст ошибки на экране |
| :--- | :--- | :--- | :--- | :--- |
| **Email Input** | `#emailControl` | `input[type="text"]` | • Обязательное поле<br>• Формат email (RFC 5322) | • *"Please provide an email address."*<br>• *"Email address is not valid."* |
| **Password Input** | `#passwordControl` | `input[type="password"]` | • Обязательное поле<br>• Длина от 5 до 40 символов | • *"Please provide a password."*<br>• *"Password must be 5-40 characters long."* |
| **Repeat Password** | `#repeatPasswordControl` | `input[type="password"]` | • Обязательное поле<br>• Полное совпадение с паролем | • *"Please repeat your password."*<br>• *"Passwords do not match"* |
| **Show password advice** | `mat-slide-toggle` | `mat-slide-toggle` | Переключатель рекомендаций | Разворачивает панель `app-password-strength-info` с правилами (строчные, прописные, цифры, спецсимволы, длина 8+). |
| **Security Question** | `mat-select[name="securityQuestion"]` | `mat-select` | • Обязательный выбор из 14 вопросов | • *"Please select a security question."*<br>• Подсказка: *"This cannot be changed later!"* |
| **Security Answer** | `#securityAnswerControl` | `input[type="text"]` | • Обязательное поле | • *"Please provide an answer to your security question."* |
| **Кнопка Register** | `#registerButton` | `button[type="submit"]` | • Заблокирована (`disabled: true`), пока форма невалидна | Активируется только при валидности всех 5 контролов. |
| **Already a customer?** | `a[routerLink="/login"]` | `a` | Навигационная ссылка | Переход на `/#/login`. |

---

## 5. REST API Контракты и поведение сервера

### 5.1. Получение контрольных вопросов: `GET /api/SecurityQuestions/`
* **Статус:** `200 OK`
* **Тело ответа:** Массив из 14 объектов `{ "id": int, "question": string }`.

### 5.2. Регистрация пользователя: `POST /api/Users/`
* **Request Payload:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "passwordRepeat": "SecurePassword123!",
  "securityQuestion": {
    "id": 1,
    "question": "Your eldest siblings middle name?"
  },
  "securityAnswer": "Alexander"
}
```
* **Успешный ответ (`201 Created`):**
```json
{
  "status": "success",
  "data": {
    "id": 105,
    "username": "",
    "email": "user@example.com",
    "role": "customer",
    "deluxeToken": "",
    "lastLoginIp": "0.0.0.0",
    "profileImage": "/assets/public/images/uploads/default.svg",
    "isActive": true,
    "createdAt": "2026-10-21T13:48:04.867Z",
    "updatedAt": "2026-10-21T13:48:04.867Z",
    "deletedAt": null
  }
}
```
* **Ошибка: Дубликат Email (`400 Bad Request`):**
```json
{
  "message": "Validation error",
  "errors": [
    {
      "field": "email",
      "message": "email must be unique"
    }
  ]
}
```
* **Ошибка: Пустые Email/Пароль (`400 Bad Request`):**
```text
"Invalid email/password cannot be empty"
```

---

## 6. Критерии приемки (Acceptance Criteria / Gherkin)

```gherkin
Scenario: Успешная регистрация нового клиента через форму
  Given гость открывает страницу "/#/register"
  And закрывает модальное окно приветствия и cookie-баннер
  When заполняет email уникальным значением "new_buyer@juice-sh.op"
  And вводит пароль "Secret123!" и подтверждение "Secret123!"
  And выбирает секретный вопрос и указывает ответ "Alexander"
  And нажимает кнопку "Register"
  Then система отображает нотификацию "Registration completed successfully. You can now log in."
  And пользователь перенаправляется на форму "/#/login"

Scenario: Блокировка кнопки при невалидном email или коротком пароле
  Given открыта страница регистрации
  When пользователь вводит невалидный email "test@"
  Or пароль длиной менее 5 символов "1234"
  Then отображается сообщение "Email address is not valid." или "Password must be 5-40 characters long."
  And кнопка "Register" остается неактивной (disabled)

Scenario: Попытка регистрации существующего email
  Given в системе уже есть учетная запись "existing@juice-sh.op"
  When пользователь пытается зарегистрировать аккаунт с этим email
  Then отображается серверное сообщение об ошибке "email must be unique"
  And пользователь остается на странице регистрации
```

---

## 7. Граничные, редкие и архитектурные сценарии (Edge Cases & Challenges)

1. **Граничные значения длины пароля:**
   - 4 символа (длина < 5): блокируется валидатором UI (`minlength=5`), кнопка неактивна.
   - 5 символов: минимально допустимый пароль, форма валидна.
   - 40 символов: максимальная длина пароля по подсказке UI.
   - 41 символ: блокируется валидатором `maxlength=40`.
2. **Специфика челленджей Juice Shop (Архитектурные уязвимости):**
   - **Admin Registration Challenge (`registerAdminChallenge`):** при передаче `role: "admin"` в теле POST запроса сервер присваивает права администратора (Mass Assignment).
   - **Password Repeat Challenge (`passwordRepeatChallenge`):** при прямой отправке запроса с несовпадающими `password` и `passwordRepeat` бэкенд не валидирует повтор пароля (уязвимость клиентской валидации).
   - **Empty User Registration Challenge (`emptyUserRegistration`):** регистрация с пустым объектом `{}` создает пользователя с `email: null`.
3. **Белые пробелы и регистронезависимость:**
   - Пробелы по краям email и пароля тримятся на бэкенде.
   - Email `Client@test.com` и `client@test.com` считаются идентичными (дубликат).
