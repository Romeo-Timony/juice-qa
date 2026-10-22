# 🔬 Детальная телеметрия прогона n8n: Задача JS-17 (Execution #2788)

В данном документе зафиксированы **все 34 ноды**, выполненные движком n8n при обработке задачи **JS-17**.
Для каждого шага приведены: входящие данные (Input), внутренняя логика обработки и выходные данные (Output).

**Статус выполнения:** `success`  
**Время старта:** `2026-10-09T10:12:15.194Z`  
**Время завершения:** `2026-10-09T10:12:29.759Z`  
**Всего нод в цепочке:** `34`  

---

### Шаг 1. `Расписание: Проверка задач (1 мин)` (0 мс)
**1. Входные данные (Input от предыдущей ноды):**
- *Триггер:* Внутренний таймер n8n (`scheduleTrigger`, интервал 1 минута)
**2. Что делает нода (Processing Logic):**
- Обработка служебных данных.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "timestamp": "2026-10-09T06:12:15.032-04:00",
  "Readable date": "October 9th 2026, 6:12:15 am",
  "Readable time": "6:12:15 am",
  "Day of week": "Friday",
  "Year": "2026",
  "Month": "October",
  "Day of month": "09",
  "Hour": "06",
  "Minute": "12",
  "Second": "15",
  "Timezone": "America/New_York (UTC-04:00)"
}
```

### Шаг 2. `Jira: Найти задачи В работе` (486 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Выполняет JQL-поиск через Jira REST API: `status = 10046 AND (labels is EMPTY OR labels not in (...))`
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issues": [
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "10267",
      "self": "https://romeo-timony.atlassian.net/rest/api/3/issue/10267",
      "key": "JS-17",
      "fields": {
        "summary": "[Backend] ТЗ: Разработка REST API аутентификации, JWT-токенов и моделей БД",
        "assignee": {
          "self": "https://romeo-timony.atlassian.net/rest/api/3/user?accountId=712020%3A22a8d03d-b36a-4f6a-b856-7461be4a8205",
          "accountId": "712020:22a8d03d-b36a-4f6a-b856-7461be4a8205",
          "emailAddress...
```

### Шаг 3. `Фильтр: Задача взята в работу` (45 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Фильтрует перехваченные события, извлекает `issueKey` (JS-17), проверяет права и статус.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "issueId": "10267",
  "fromStatus": "К выполнению",
  "toStatus": "В работе",
  "actor": "Roman Timoshenko",
  "receivedAt": "2026-10-09T10:12:15.806Z",
  "config": {
    "jiraBase": "https://romeo-timony.atlassian.net",
    "projectKey": "JS",
    "inProgressStatusId": "10046",
    "inProgressNames": [
      "В работе",
      "In Progress"
    ],
    "todoStatusId": "10045",
    "geminiModel": "gemini-3.5-flash",
    "webhookToken": "ea6a65ab5323c0438dade394447a09fff6ec10360a1f34f6"
  }
}
```

### Шаг 4. `Jira: Загрузить данные задачи` (224 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Загружает полную структуру полей задачи: summary, description, issueType, subtasks, parent.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
  "id": "10267",
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/10267",
  "key": "JS-17",
  "fields": {
    "summary": "[Backend] ТЗ: Разработка REST API аутентификации, JWT-токенов и моделей БД",
    "issuetype": {
      "self": "https://romeo-timony.atlassian.net/rest/api/2/issuetype/10049",
      "id": "10049",
      "description": "Subtasks track small pieces of work that are part of a larger task.",
      "iconUrl": "https://romeo-timony.atlassian.net/rest/api/2/universal_av...
```

### Шаг 5. `Jira: Загрузить ссылки задачи` (672 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (2 item)
**2. Что делает нода (Processing Logic):**
- Загружает привязанные Remote Links (Confluence, внешние спецификации).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "id": 10157,
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/JS-17/remotelink/10157",
  "globalId": "qase-project-JS-JS-17",
  "application": {
    "type": "com.qase.tms",
    "name": "Qase TMS"
  },
  "relationship": "tested by",
  "object": {
    "url": "https://app.qase.io/project/JS",
    "title": "Qase TMS: Тест-кейсы задачи JS-17",
    "summary": "Пошаговые сценарии тестирования в системе Qase TMS (проект JS)",
    "icon": {
      "url16x16": "https://app.qase.io/favicon.ico",
      "title": "Qase TMS"
    },
    "status": {
      "icon": {}
    }
  }
}
```

### Шаг 6. `Правила проверки готовности задачи` (173 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Инициализирует эталонный стандарт DoR: 10 критериев оценки качества требований (INVEST, BABOK, ISTQB).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "standard": {
    "name": "QA Definition of Ready",
    "version": "1.0",
    "thresholds": {
      "minScorePercent": 75,
      "minDescriptionLength": 300,
      "weights": {
        "mandatory": 2,
        "recommended": 1
      },
      "statusScore": {
        "pass": 1,
        "partial": 0.5,
        "fail": 0
      }
    },
    "vagueWords": [
      "быстро",
      "удобно",
      "красиво",
      "интуитивно",
      "понятно",
      "оптимально",
      "корректно",
      "и т.д.",
      "и т.п.",
      "и др.",
      "по возможности",
      "при необходимости",
      "как-нибудь",...
```

### Шаг 7. `Подготовка задачи к проверке` (135 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Классифицирует задачу по ключевым словам и типу: определен профиль `backend`. Анализирует структуру описания.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "kind": "backend",
  "summary": "[Backend] ТЗ: Разработка REST API аутентификации, JWT-токенов и моделей БД",
  "description": "h2. 1. Техническое задание: Backend-разработка\n\n*Цель задачи:* Реализация серверных контроллеров, маршрутов Express, моделей Sequelize и бизнес-логики для управления учетными записями и авторизацией.\n\nh3. 2. Архитектурный контекст и модели базы данных\n\n* Маршрутизаторы и контроллеры: routes/register.ts, routes/login.ts, routes/resetPassword.ts, routes/authenticatedUsers.ts\n* Модели Sequelize: models/user.ts, models/securityQuestion.ts...
```

### Шаг 8. `Проверка задачи на готовность` (267 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Проверяет требования по 10 критериям. Результат: `score = 100/100`, вердикт: `passed = True`.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "kind": "backend",
  "autoPassDor": false,
  "passed": true,
  "score": 100,
  "mandatoryFailed": [],
  "results": [
    {
      "id": "C01",
      "title": "Заголовок",
      "rule": "Заголовок конкретный, отражает результат работы, не длиннее 120 символов; у подзадач есть префикс слоя ([Frontend]/[Backend]).",
      "mandatory": true,
      "status": "pass",
      "comment": "Заголовок конкретный (74 символов).",
      "evidence": "[Backend] ТЗ: Разработка REST API аутентификации, JWT-токенов и моделей БД"
    },
    {
      "id": "C02",
      "title": "Цель и бизн...
```

### Шаг 9. `Условие: Требования задачи понятны?` (20 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Логический шлюз (`n8n IF node`): проверяет булевы флаги (успешность DoR, одобрение Gate, наличие новых кейсов).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "kind": "backend",
  "autoPassDor": false,
  "passed": true,
  "score": 100,
  "mandatoryFailed": [],
  "results": [
    {
      "id": "C01",
      "title": "Заголовок",
      "rule": "Заголовок конкретный, отражает результат работы, не длиннее 120 символов; у подзадач есть префикс слоя ([Frontend]/[Backend]).",
      "mandatory": true,
      "status": "pass",
      "comment": "Заголовок конкретный (74 символов).",
      "evidence": "[Backend] ТЗ: Разработка REST API аутентификации, JWT-токенов и моделей БД"
    },
    {
      "id": "C02",
      "title": "Цель и бизн...
```

### Шаг 10. `Jira: Отчет 1 — Задача готова к работе (DoR Gate)` (568 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Отправляет форматированный отчет через Atlassian Jira Cloud REST API (`POST /rest/api/2/issue/{key}/comment`).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/10267/comment/11051",
  "id": "11051",
  "author": {
    "self": "https://romeo-timony.atlassian.net/rest/api/2/user?accountId=712020%3A22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "accountId": "712020:22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "emailAddress": "roman.timoshenko@gmail.com",
    "avatarUrls": {
      "48x48": "https://secure.gravatar.com/avatar/6b98620eff93dad801287a1605e0c4b6?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FRT-1.png",
      "24x24": "https://secure.gravatar....
```

### Шаг 11. `Подготовка данных для чек-листа` (21 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Обработка служебных данных.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "kind": "backend",
  "prefix": "BE",
  "geminiRequest": {
    "systemInstruction": {
      "parts": [
        {
          "text": "Ты — Senior QA Engineer (ISTQB Advanced). Составляешь практичный QA чек-лист по лучшим практикам тест-дизайна:\nклассы эквивалентности, граничные значения, таблицы решений, переходы состояний, позитивные/негативные сценарии, безопасность (OWASP), доступность (WCAG 2.1 AA).\nКаждый пункт — одна атомарная проверка, сформулированная как проверяемое утверждение (\"Проверить, что ...\"), с конкретными значениями из требований.\nНе дублируй пун...
```

### Шаг 12. `Создание карты проверок` (22 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Строит 4-уровневую интеллект-карту проверок (MindMap) для REST API, JWT авторизации и моделей БД.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "kind": "backend"
}
```

### Шаг 13. `Jira: Отчет 2 — Интеллект-карта проверок` (351 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Отправляет форматированный отчет через Atlassian Jira Cloud REST API (`POST /rest/api/2/issue/{key}/comment`).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/10267/comment/11053",
  "id": "11053",
  "author": {
    "self": "https://romeo-timony.atlassian.net/rest/api/2/user?accountId=712020%3A22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "accountId": "712020:22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "emailAddress": "roman.timoshenko@gmail.com",
    "avatarUrls": {
      "48x48": "https://secure.gravatar.com/avatar/6b98620eff93dad801287a1605e0c4b6?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FRT-1.png",
      "24x24": "https://secure.gravatar....
```

### Шаг 14. `Подготовка данных для тест-кейсов` (20 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Обработка служебных данных.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "kind": "backend",
  "geminiRequest": {
    "systemInstruction": {
      "parts": [
        {
          "text": "Ты — Senior QA Automation Engineer. Пишешь тест-кейсы по стандарту BDD Gherkin (Given/When/Then) и Allure Steps (@allure.step) для последующей автоматизации и импорта в Qase TMS.\nКаждый тест-кейс оформляется как BDD сценарий:\n- В description включается полный текст сценария Gherkin с Allure-метаданными (@allure.epic, @allure.feature, @allure.story, @allure.severity).\n- Каждый шаг в steps оформляется как атомарный Allure Step с префиксами [Given], [When]...
```

### Шаг 15. `Qase: Загрузить список папок` (383 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Обращается к Qase TMS REST API v1 для получения актуального дерева сьютов и существующих кейсов.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "status": true,
  "result": {
    "total": 2,
    "filtered": 2,
    "count": 2,
    "entities": [
      {
        "id": 37,
        "title": "Frontend",
        "description": null,
        "preconditions": null,
        "position": 1,
        "cases_count": 0,
        "parent_id": null,
        "created": "2026-10-09 08:06:02",
        "updated": "2026-10-09 08:06:02",
        "created_at": "2026-10-09T08:06:02+00:00",
        "updated_at": "2026-10-09T08:06:02+00:00"
      },
      {
        "id": 38,
        "title": "JS-16: [Frontend] ТЗ: Разработка интерфейса, форм регистрации/логина...
```

### Шаг 16. `Qase: Загрузить существующие тесты` (632 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Обращается к Qase TMS REST API v1 для получения актуального дерева сьютов и существующих кейсов.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "status": true,
  "result": {
    "total": 12,
    "filtered": 12,
    "count": 12,
    "entities": [
      {
        "id": 319,
        "position": 1,
        "title": "[Frontend][Parametrized] Успешная регистрация нового пользователя с валидными форматами Email",
        "description": "## 📌 Цель тест-кейса\nПараметризованная проверка успешной регистрации нового пользователя в веб-приложении OWASP Juice Shop с различными валидными форматами адресов электронной почты (согласно спецификации RFC 5322).\nТест-кейс валидирует, что фронтенд корректно принимает валидные email-адреса, передает и...
```

### Шаг 17. `Создание тест-кейсов без повторов` (905 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Генерирует реестр из 12 тест-кейсов BDD Gherkin с тегами регресса, проверяет дубликаты и строит матрицу RTM.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "kind": "backend",
  "cases": [
    {
      "id": "TC-BE-01",
      "title": "[API][Parametrized] Создание учетной записи пользователя через POST /api/Users/",
      "description": "Data-driven интеграционный API тест создания пользователя с хешированием пароля и связью с SecurityQuestion. 100% автотест API.",
      "gherkin": "@allure.epic(\"OWASP Juice Shop\")\n@allure.feature(\"Backend REST API\")\n@allure.story(\"JS-17: User Creation Endpoint\")\n@allure.severity(\"critical\")\n@fast-regression\n@full-regression\nScenario Outline: Успешное создание пользователя ч...
```

### Шаг 18. `Jira: Отчет 3 — Реестр тест-кейсов (BDD)` (382 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Отправляет форматированный отчет через Atlassian Jira Cloud REST API (`POST /rest/api/2/issue/{key}/comment`).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/10267/comment/11055",
  "id": "11055",
  "author": {
    "self": "https://romeo-timony.atlassian.net/rest/api/2/user?accountId=712020%3A22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "accountId": "712020:22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "emailAddress": "roman.timoshenko@gmail.com",
    "avatarUrls": {
      "48x48": "https://secure.gravatar.com/avatar/6b98620eff93dad801287a1605e0c4b6?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FRT-1.png",
      "24x24": "https://secure.gravatar....
```

### Шаг 19. `Jira: Отчет 4 — Матрица трассируемости (RTM)` (462 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Отправляет форматированный отчет через Atlassian Jira Cloud REST API (`POST /rest/api/2/issue/{key}/comment`).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/10267/comment/11057",
  "id": "11057",
  "author": {
    "self": "https://romeo-timony.atlassian.net/rest/api/2/user?accountId=712020%3A22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "accountId": "712020:22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "emailAddress": "roman.timoshenko@gmail.com",
    "avatarUrls": {
      "48x48": "https://secure.gravatar.com/avatar/6b98620eff93dad801287a1605e0c4b6?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FRT-1.png",
      "24x24": "https://secure.gravatar....
```

### Шаг 20. `Контроль 1: Подтверждение тест-кейсов` (23 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Quality Gate 1: аудит тест-кейсов (полнота, соотношение позитивных/негативных, безопасность). Оценка: 96/100.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "kind": "backend",
  "cases": [
    {
      "id": "TC-BE-01",
      "title": "[API][Parametrized] Создание учетной записи пользователя через POST /api/Users/",
      "description": "Data-driven интеграционный API тест создания пользователя с хешированием пароля и связью с SecurityQuestion. 100% автотест API.",
      "gherkin": "@allure.epic(\"OWASP Juice Shop\")\n@allure.feature(\"Backend REST API\")\n@allure.story(\"JS-17: User Creation Endpoint\")\n@allure.severity(\"critical\")\n@fast-regression\n@full-regression\nScenario Outline: Успешное создание пользователя ч...
```

### Шаг 21. `Jira: Карточка подтверждения тестов (Gate 1)` (404 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Отправляет форматированный отчет через Atlassian Jira Cloud REST API (`POST /rest/api/2/issue/{key}/comment`).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/10267/comment/11059",
  "id": "11059",
  "author": {
    "self": "https://romeo-timony.atlassian.net/rest/api/2/user?accountId=712020%3A22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "accountId": "712020:22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "emailAddress": "roman.timoshenko@gmail.com",
    "avatarUrls": {
      "48x48": "https://secure.gravatar.com/avatar/6b98620eff93dad801287a1605e0c4b6?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FRT-1.png",
      "24x24": "https://secure.gravatar....
```

### Шаг 22. `Условие: Тест-кейсы подтверждены?` (3 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Логический шлюз (`n8n IF node`): проверяет булевы флаги (успешность DoR, одобрение Gate, наличие новых кейсов).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/10267/comment/11059",
  "id": "11059",
  "author": {
    "self": "https://romeo-timony.atlassian.net/rest/api/2/user?accountId=712020%3A22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "accountId": "712020:22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "emailAddress": "roman.timoshenko@gmail.com",
    "avatarUrls": {
      "48x48": "https://secure.gravatar.com/avatar/6b98620eff93dad801287a1605e0c4b6?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FRT-1.png",
      "24x24": "https://secure.gravatar....
```

### Шаг 23. `Условие: Есть новые тесты для добавления?` (2 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Логический шлюз (`n8n IF node`): проверяет булевы флаги (успешность DoR, одобрение Gate, наличие новых кейсов).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/10267/comment/11059",
  "id": "11059",
  "author": {
    "self": "https://romeo-timony.atlassian.net/rest/api/2/user?accountId=712020%3A22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "accountId": "712020:22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "emailAddress": "roman.timoshenko@gmail.com",
    "avatarUrls": {
      "48x48": "https://secure.gravatar.com/avatar/6b98620eff93dad801287a1605e0c4b6?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FRT-1.png",
      "24x24": "https://secure.gravatar....
```

### Шаг 24. `Qase: Создать новые тесты в базе` (6298 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Выполняет пакетную вставку (Bulk API `POST /v1/case/JS/bulk`) новых тестов в систему Qase TMS.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "status": true,
  "result": {
    "ids": [
      343,
      344,
      345,
      346,
      347,
      348,
      349,
      350,
      351,
      352,
      353,
      354
    ]
  }
}
```

### Шаг 25. `Jira: Прикрепить ссылку на тесты в Qase` (476 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Создает прямую интерактивную связь задачи Jira со сьютом в Qase TMS (`POST /remotelink`).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "id": 10157,
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/JS-17/remotelink/10157"
}
```

### Шаг 26. `Jira: Поставить метку Готово к разработке` (326 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Проставляет технические метки в Jira: `qa-dor-passed`, `qa-ready-for-autotests`.
**3. Выходные данные (Output для следующей ноды):**
```json
{}
```

### Шаг 27. `Создание файлов автотестов на Python` (20 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Генерирует каркас автотестов на Python: test_js17_api.py.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "issueSummary": "[Backend] ТЗ: Разработка REST API аутентификации, JWT-токенов и моделей БД",
  "kind": "backend",
  "scaffoldTimestamp": "2026-10-09T10:12:28.618Z",
  "files": [
    {
      "type": "backend",
      "fileName": "test_js17_api.py",
      "stagingPath": "tests/review/backend/test_js17_api.py",
      "targetPath": "tests/backend/test_js17_api.py",
      "testCount": 12,
      "code": "\"\"\"\nBackend API Automated Test Suite for JS-17: [Backend] ТЗ: Разработка REST API аутентификации, JWT-токенов и моделей БД\nGenerated by n8n QA Autotest Scaffolding En...
```

### Шаг 28. `Jira: Отчет 5 — Код сгенерирован` (387 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Отправляет форматированный отчет через Atlassian Jira Cloud REST API (`POST /rest/api/2/issue/{key}/comment`).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/10267/comment/11062",
  "id": "11062",
  "author": {
    "self": "https://romeo-timony.atlassian.net/rest/api/2/user?accountId=712020%3A22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "accountId": "712020:22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "emailAddress": "roman.timoshenko@gmail.com",
    "avatarUrls": {
      "48x48": "https://secure.gravatar.com/avatar/6b98620eff93dad801287a1605e0c4b6?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FRT-1.png",
      "24x24": "https://secure.gravatar....
```

### Шаг 29. `Контроль 2: Проверка качества кода тестов` (19 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Quality Gate 2: валидация кода автотестов, проверка синтаксиса и структуры. Оценка: 98/100.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "files": [
    {
      "type": "backend",
      "fileName": "test_js17_api.py",
      "stagingPath": "tests/review/backend/test_js17_api.py",
      "targetPath": "tests/backend/test_js17_api.py",
      "testCount": 12,
      "code": "\"\"\"\nBackend API Automated Test Suite for JS-17: [Backend] ТЗ: Разработка REST API аутентификации, JWT-токенов и моделей БД\nGenerated by n8n QA Autotest Scaffolding Engine\n\"\"\"\nimport pytest\nimport allure\nfrom api.client import JuiceShopApiClient\nfrom schemas.models import UserRegistrationResponse, LoginResponse, ApiErrorRespo...
```

### Шаг 30. `Jira: Карточка проверки кода (Gate 2)` (345 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Отправляет форматированный отчет через Atlassian Jira Cloud REST API (`POST /rest/api/2/issue/{key}/comment`).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/10267/comment/11064",
  "id": "11064",
  "author": {
    "self": "https://romeo-timony.atlassian.net/rest/api/2/user?accountId=712020%3A22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "accountId": "712020:22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "emailAddress": "roman.timoshenko@gmail.com",
    "avatarUrls": {
      "48x48": "https://secure.gravatar.com/avatar/6b98620eff93dad801287a1605e0c4b6?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FRT-1.png",
      "24x24": "https://secure.gravatar....
```

### Шаг 31. `Условие: Код тестов подтвержден?` (8 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Логический шлюз (`n8n IF node`): проверяет булевы флаги (успешность DoR, одобрение Gate, наличие новых кейсов).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/10267/comment/11064",
  "id": "11064",
  "author": {
    "self": "https://romeo-timony.atlassian.net/rest/api/2/user?accountId=712020%3A22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "accountId": "712020:22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "emailAddress": "roman.timoshenko@gmail.com",
    "avatarUrls": {
      "48x48": "https://secure.gravatar.com/avatar/6b98620eff93dad801287a1605e0c4b6?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FRT-1.png",
      "24x24": "https://secure.gravatar....
```

### Шаг 32. `Перенос автотестов в рабочий проект` (16 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Переносит утвержденный код в целевой путь проекта: test_js17_api.py.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "promotedFiles": [
    {
      "type": "backend",
      "fileName": "test_js17_api.py",
      "stagingPath": "tests/review/backend/test_js17_api.py",
      "targetPath": "tests/backend/test_js17_api.py",
      "testCount": 12,
      "code": "\"\"\"\nBackend API Automated Test Suite for JS-17: [Backend] ТЗ: Разработка REST API аутентификации, JWT-токенов и моделей БД\nGenerated by n8n QA Autotest Scaffolding Engine\n\"\"\"\nimport pytest\nimport allure\nfrom api.client import JuiceShopApiClient\nfrom schemas.models import UserRegistrationResponse, LoginResponse, ApiEr...
```

### Шаг 33. `Jira: Финальный отчет о внедрении автотестов` (339 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Отправляет форматированный отчет через Atlassian Jira Cloud REST API (`POST /rest/api/2/issue/{key}/comment`).
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "self": "https://romeo-timony.atlassian.net/rest/api/2/issue/10267/comment/11065",
  "id": "11065",
  "author": {
    "self": "https://romeo-timony.atlassian.net/rest/api/2/user?accountId=712020%3A22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "accountId": "712020:22a8d03d-b36a-4f6a-b856-7461be4a8205",
    "emailAddress": "roman.timoshenko@gmail.com",
    "avatarUrls": {
      "48x48": "https://secure.gravatar.com/avatar/6b98620eff93dad801287a1605e0c4b6?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FRT-1.png",
      "24x24": "https://secure.gravatar....
```

### Шаг 34. `Сохранение файлов на диск` (18 мс)
**1. Входные данные (Input от предыдущей ноды):**
- Получен поток объектов из предыдущего шага (1 item)
**2. Что делает нода (Processing Logic):**
- Финализирует выполнение и сохраняет метаданные запуска.
**3. Выходные данные (Output для следующей ноды):**
```json
{
  "issueKey": "JS-17",
  "savedCount": 0,
  "errors": [
    "Module 'fs' is disallowed [line 13]"
  ],
  "message": "Файлы не сохранены"
}
```
