# Проектное досье и материалы для резюме QA / SDET / QAOps инженера

> **Назначение документа:** Комплексное резюме-досье (Project Case Study) для составления и обогащения резюме инженера по автоматизации тестирования (AQA / SDET / QA Lead / QAOps).  
> **GitHub-репозиторий проекта:** [https://github.com/Romeo-Timony/juice-qa](https://github.com/Romeo-Timony/juice-qa)  
> **Целевое приложение (SUT):** [OWASP Juice Shop](https://github.com/juice-shop/juice-shop)  
> **Роль:** Lead Automation QA / SDET / QAOps Architect  

---

## 1. Краткое описание проекта (Elevator Pitch для резюме)

Проектирование и сквозное внедрение **автономной экосистемы обеспечения качества нового поколения (Autonomous QA & QAOps Ecosystem)** для высоконагруженной e-commerce платформы **OWASP Juice Shop**.  
Комплекс объединяет:
1. **Фреймворк автоматизации тестирования** на **Python 3.12 (Pytest + Playwright + Requests + Pydantic v2 + Allure)**;
2. **Событийно-ориентированную оркестрацию** на **n8n** и **Python Daemon**;
3. **AI-агентов (LLM-as-a-Judge на базе Gemini 2.5 Flash / DeepEval)** для автоматической валидации требований (DoR), генерации тест-дизайна и аудита кода;
4. **Промышленный контур QAOps с 6 архитектурными швами (Seams 1–6)**: контрактный контроль (INVEST), идемпотентность, персистентный Circuit Breaker, человеко-машинный контроль (HITL) и телеметрия со сквозным расчетом **Release Quality Index (RQI)**;
5. **CI/CD в GitHub Actions** с параллельным запуском, записью видео-скринкастов (WebM), публикацией отчетов Allure на GitHub Pages и мгновенными оповещениями команды в Telegram.

---

## 2. Описание тестируемого приложения (System Under Test)

**OWASP Juice Shop** — сложная распределенная одностраничная платформа (SPA) для электронной коммерции:
* **Frontend:** Angular 21, TypeScript, RxJS, Angular Material (M3), компонентная архитектура, SPA hash-routing, HTTP Interceptors (JWT Bearer injection, error handling);
* **Backend:** Node.js (LTS v24), Express 4.x REST API, Socket.io (двусторонние WebSocket-уведомления и чат-бот JuiceBot);
* **Базы данных:** SQLite3 + Sequelize ORM (реляционные данные: пользователи, корзины, заказы, адреса, платежи), MarsDB (in-memory NoSQL хранилище для отзывов и чатов);
* **Безопасность и авторизация:** Stateless JWT (jsonwebtoken), bcrypt хэширование, 2FA/TOTP аутентификация.

### Основные тестируемые бизнес-домены:
1. **Идентификация и безопасность:** Регистрация, логин (JWT), смена и сброс паролей с секретными вопросами, 2FA, редактирование профиля и загрузка аватаров (multipart/form-data и URL);
2. **Каталог и витрина:** Полнотекстовый поиск, динамическая фильтрация, карточки товаров, древовидные отзывы с лайками;
3. **Корзина и чекаут:** Мультитоварные корзины, динамический расчет стоимости доставки, валидация платежных карт, генерация PDF-инвойсов;
4. **Клиентский сервис:** Форма обратной связи с CAPTCHA, оформление рекламаций с вложениями, чат-бот;
5. **Безопасность (Security Testing):** Предотвращение регресса уязвимостей (SQLi, IDOR, XSS, Broken Object Level Auth).

---

## 3. Архитектура тестового фреймворка и QAOps-контура

```text
                                  +-------------------------------------------------------------+
                                  |                 Jira Cloud (Backlog / User Stories)         |
                                  +------------------------------+------------------------------+
                                                                 | Webhook: Ready for QA
                                                                 v
+-----------------------------------------------------------------------------------------------+
|                       ОРКЕСТРАЦИЯ И AI ТЕСТ-ДИЗАЙН (n8n + Gemini Flash)                      |
|                                                                                               |
|  [Seam 1: DoR Gate]           --> [Seam 2: Semantic Test Design]  --> [Qase TMS Sync]         |
|  - Валидация INVEST (Pydantic)    - Генерация кейсов по AC            - Двусторонний синк     |
|  - Авто-пауза при дефекте ТЗ      - LLM-as-a-Judge (G-Eval)           - Управление сьютами    |
+------------------------------------------------+----------------------------------------------+
                                                 |
                                                 v
+-----------------------------------------------------------------------------------------------+
|                     ИЗОЛИРОВАННАЯ ГЕНЕРАЦИЯ И СТАТИЧЕСКИЙ АУДИТ (Python Daemon)               |
|                                                                                               |
|  [Git Worktree Isolation]     --> [Seam 3: Static Code Gate]      --> [Seam 4: Resilience]    |
|  - Ветка qa/<issue-key>           - AST-парсер + Ruff linter          - SQLite транзакции     |
|  - Изоляция окружения             - Docker collect-only (--net none)  - Circuit Breaker       |
+------------------------------------------------+----------------------------------------------+
                                                 |
                                                 v
+-----------------------------------------------------------------------------------------------+
|                        ВЕРИФИКАЦИЯ, ПРОГОН И CI/CD (GitHub Actions)                           |
|                                                                                               |
|  [Seam 5: HITL Gate 2]        --> [CI/CD Execution & Allure]      --> [Seam 6: Observability] |
|  - Evidence Pack в Jira           - Playwright UI + Requests API      - Маскирование PII      |
|  - Аппрув лида перед слиянием     - WebM видео + cURL шаги            - Release Quality Index |
|                                   - Live Allure на GitHub Pages       - Итоговый вердикт      |
+-----------------------------------------------------------------------------------------------+
```

### Ключевые компоненты решения:
1. **E2E UI Автоматизация (Playwright):**
   - Реализован классический паттерн **Page Object Model (POM)**: `BasePage`, `LoginPage`, `RegisterPage`, `ProfilePage`, `ChangePasswordPage`;
   - Надежные стратегии ожидания (`wait_for_selector`, `expect(locator).to_be_visible()`) без жестких `time.sleep()`;
   - Автоматический перехват скриншотов при падениях и запись полного видео прогона в формате **WebM** с прикреплением к Allure.
2. **Backend API Автоматизация (Requests + Pydantic v2):**
   - Клиент `JuiceShopApiClient` с поддержкой сохранения сессий, Bearer-токенов, multipart-загрузок;
   - Автоматическое формирование **cURL команд** для каждого запроса прямо в шагах Allure (упрощает мгновенное ручное воспроизведение багов разработчиками);
   - Валидация схем ответов API через строгие Pydantic v2 модели (`UserRegistrationResponse`, `LoginResponse`, `AddressResponse`).
3. **Двусторонняя интеграция с Qase TMS (`sync_qase_tests.py`, `qase_lifecycle_sync.py`):**
   - AST-анализатор кодовой базы: сканирует декораторы `@pytest.mark.qase(id=...)` и сопоставляет с тест-планами в Qase TMS;
   - Автоматическое обнаружение расхождений (Drift Detection) и обновление статусов тестов (`Automated` / `To-be-automated`);
   - Генерация отчетов покрытия в формате Markdown и прикрепление к Jira.
4. **Контур QAOps: 6 Архитектурных Швов (Industrial Seams):**
   * **Seam 1 (DoR Gate):** Проверка контракта User Story по критериям **INVEST** (Independent, Negotiable, Valuable, Estimable, Small, Testable). При неполноте требований задача автоматически блокируется меткой `qa-paused` без допуска в спринт.
   * **Seam 2 (Semantic Design Gate):** Оценка сгенерированных кейсов AI-судьей (Gemini Flash + DeepEval G-Eval) на предмет привязки к Acceptance Criteria (Groundedness). Автоматический прунинг неразмеченных тестов.
   * **Seam 3 (Static Code Gate):** Валидация синтаксического дерева через `ast.parse`, проверка линтером Ruff (блокирующие ошибки E9, F82), проверка сбора через `pytest --collect-only` в изолированном Docker-контейнере без доступа в сеть (`--network none`).
   * **Seam 4 (Idempotency & External Resilience):** Гарантия ровно одного выполнения мутаций (Jira, Qase, Git push) через SQLite `BEGIN IMMEDIATE` транзакции (ключи `SHA-256(scope + args)`). Персистентный Circuit Breaker (CLOSED/OPEN/HALF_OPEN), повторные попытки с экспоненциальным Backoff и полным джиттером, Outbox-паттерн с CLI-реплеем.
   * **Seam 5 (Human-in-the-Loop Quality Gate 2):** Сборка структурированного **Evidence Pack** в комментарии Jira (метрики LLM-Judge, AST, Ruff, Allure-вложения, ссылка на трейс). Автоматический переход к слиянию только после аппрува инженера (`ok` / `❤️`).
   * **Seam 6 (Observability & Release Decision Engine):** Трейсинг выполнения с автоматическим маскированием секретов (JWT, пароли, email, токены). Расчет **Release Quality Index (RQI)** от 0 до 100 баллов на основе взвешенных метрик и вынесение жесткого вердикта: **GO** или **NO-GO**.
5. **Telegram Bot Notifier (`scripts/telegram_notifier.py`):**
   - Строгий конечный автомат состояний уведомлений;
   - Информирование о статусе прохождения DoR, готовности тестов к ревью, старте пайплайна GitHub Actions и финальном вердикте релиза.

---

## 4. Достигнутые результаты и метрики качества

| Метрика | Значение | Как измеряется | Бизнес-эффект |
| :--- | :---: | :--- | :--- |
| **Schema Compliance Rate (DoR Gate)** | **100%** | Pydantic v2 валидация в Seam 1 | Полное исключение задач с неполными требованиями из разработки |
| **Test Design Integrity** | **$\ge$ 92%** | G-Eval Groundedness + детерминированный аудит тегов | 0 галлюцинированных или оторванных от требований тест-кейсов |
| **Syntax & Collect Validity** | **100%** | AST parse + Ruff + Docker изолированный collect | Предотвращение поломки CI/CD из-за синтаксических ошибок в сгенерированном коде |
| **Idempotency Leaks** | **0** | SQLite `qaops_idempotency` audit | Исключение дублирования тикетов, веток, пушей и прогонов |
| **Recovery Rate (External Outages)** | **$\ge$ 88%** | Статистика Circuit Breaker и Outbox | Бесперебойная работа при сбоях внешних API (Jira/Qase/Gemini) |
| **Release Quality Index (RQI)** | **0–100** | Модуль `qaops.metrics` | Объективное математическое решение о допуске релиза в прод (Hard Gates) |
| **Время полного прогона тестов** | **< 3 мин** | Параллельное исполнение в CI/CD | Быстрый Time-to-Feedback для инженеров |
| **Покрытие автоматизацией тестового контура** | **27 unit-тестов** | Pytest в `tests/qaops/` (Seams 1–6) | 100% стабильность и предсказуемость самого фреймворка |

---

## 5. Готовые формулировки для резюме (Bullet Points)

### Вариант 1: Для позиции Senior Automation QA Engineer / SDET
* Спроектировал и с нуля внедрил модульный фреймворк автоматизации тестирования на **Python 3.12 (Pytest, Playwright, Requests, Pydantic v2, Allure)** для SPA-приложения **OWASP Juice Shop** (Angular 21 / Node.js Express).
* Разработал библиотеку Page Object Model (POM) для Playwright с автоматическим перехватом видеозаписей прогонов (WebM) и скриншотов при падениях.
* Создал REST API клиент с автоматическим формированием cURL-команд в отчетах Allure и валидацией контрактов через схемы Pydantic v2.
* Настроил двустороннюю синхронизацию тестов с **Qase TMS** через AST-парсер кодовой базы, сократив расхождения документации и кода (Test Drift) до 0%.
* Интегрировал сквозной пайплайн в **GitHub Actions** с параллельным запуском, публикацией интерактивных отчетов Allure на GitHub Pages и нотификациями в Telegram.

### Вариант 2: Для позиции QA Lead / QAOps Architect
* Разработал архитектуру автономного контура обеспечения качества **QAOps** на базе 6 контрольных швов (**Seams 1–6**), снизив время подготовки тестового покрытия на **70%**.
* Внедрил автоматический **DoR Gate (Seam 1)** на базе Pydantic-контрактов для аудита пользовательских историй в **Jira Cloud** по критериям **INVEST**.
* Развернул подсистему семантического тест-дизайна с использованием **LLM-as-a-Judge (Gemini Flash / DeepEval)** для проверки обоснованности кейсов (Groundedness $\ge$ 90%).
* Спроектировал подсистему отказоустойчивости и идемпотентности (**Seam 4**): транзакции SQLite `BEGIN IMMEDIATE`, Circuit Breaker, Exponential Jitter Backoff и Outbox-паттерн, гарантировавшие 0 утечек дублирующих операций.
* Разработал модуль расчета индекса качества релиза (**Release Quality Index**, RQI 0–100) с жесткими гейтами (Hard Gates) для автоматического принятия решения **GO / NO-GO** перед релизом.
* Настроил процесс **Human-in-the-Loop (Gate 2)** с автоматической генерацией Evidence Pack в Jira и аппрувом слияния веток через Git Worktree.

---

## 6. Технологический стек и ключевые навыки (Skills Matrix)

| Категория | Технологии и инструменты |
| :--- | :--- |
| **Языки программирования** | Python 3.12, TypeScript, JavaScript, SQL (SQLite3), Bash/PowerShell |
| **Фреймворки автоматизации** | Pytest, Playwright (Sync/Async), Requests, Pydantic v2 |
| **Архитектурные паттерны** | Page Object Model (POM), Circuit Breaker, Outbox Pattern, Idempotency Guard, AST Analysis |
| **Тестовая отчетность и TMS** | Allure Report, Qase TMS (REST API & Webhooks), Allure Steps & cURL attachments, WebM screencasting |
| **CI/CD и DevOps** | GitHub Actions, Git Worktree, Docker (`python:3.12-slim`), GitHub Pages, ngrok/Cloudflare Tunnels |
| **Оркестрация и автоматизация процессов** | n8n (Webhooks, Node workflow logic), Atlassian Jira Cloud (REST API, Webhooks, JQL, Transitions) |
| **AI в тестировании (AI in QA)** | Gemini 2.5 Flash, DeepEval (G-Eval), LLM-as-a-Judge, Groundedness scoring, Prompt Engineering |
| **Наблюдаемость и телеметрия** | Langfuse Tracing, PII Sanitization, SQLite WAL storage, p95 latency tracking, Release Quality Index (RQI) |
| **Мессенджеры и алертинг** | Telegram Bot API, линейные стейт-машины уведомлений |

---

## 7. Вопросы для собеседования и готовые ответы на базе проекта

<details>
<summary><b>1. Как вы решали проблему нестабильности (flaky-тестов) в UI?</b></summary>

* В фреймворке Playwright исключены любые статические ожидания (`time.sleep`).
* Использованы умные авто-ожидания Playwright (`expect(locator).to_be_visible()`) и явные ожидания завершения сетевых запросов (`page.wait_for_response()`) при динамической загрузке данных в Angular SPA.
* Реализована запись видео каждого теста: при локализации проблемы инженер изучает не только лог ошибки, но и посекундный видео-скринкаст WebM, прикрепленный к Allure.
</details>

<details>
<summary><b>2. Как была обеспечена идемпотентность и защита от повторных срабатываний вебхуков?</b></summary>

* Внедрен модуль `qaops/idempotency.py`. Каждая мутирующая операция (создание коммита, пуш в Git, перевод статуса в Jira, синхронизация с Qase) заворачивается в контекстный менеджер `idempotent(scope, key)`.
* Ключ операции вычисляется как SHA-256 от параметров. В SQLite базе транзакцией `BEGIN IMMEDIATE` фиксируется статус `IN_FLIGHT`. При повторном вебхуке второй процесс либо блокируется, либо получает закэшированный результат завершенной операции. При зависании предусмотрен 10-минутный TTL.
</details>

<details>
<summary><b>3. Как вы гарантировали качество сгенерированных AI автотестов перед их запуском?</b></summary>

* Реализован трехуровневый шлюз:
  1. **Семантический шлюз (Seam 2):** LLM-as-a-Judge оценивает соответствие критериям приемки (Groundedness $\ge$ 90%).
  2. **Статический шлюз (Seam 3):** Файл проверяется через абстрактное синтаксическое дерево `ast.parse()` и линтер Ruff (E9, F82).
  3. **Изолированный запуск (Seam 3):** `pytest --collect-only` запускается в песочнице Docker без доступа к сети. Только после этого код отправляется на согласование человеку (Gate 2 HITL).
</details>
