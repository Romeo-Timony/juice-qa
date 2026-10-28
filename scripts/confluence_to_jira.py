#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================================================
OWASP Juice Shop — QA Automation & Agile Project Management
Модуль: Confluence-to-Jira Specification Engine (DoR Compliant Generator)
Автор:  QA Lead / Agile Project Manager
Назначение:
  Автоматическое извлечение спецификаций из Confluence Living Documentation и генерация
  эталонных технических заданий (DoR v1.0) для Jira:
    1. User Story (JS-39 / JS-X) со 100% соответствием критериям INVEST, AC и DoD.
    2. Инженерные задачи для кросс-функциональной команды:
       - [API] Реализация серверной логики и контрактов
       - [UI] Разработка клиентской формы и валидации
       - [E2E] Сквозная интеграция и приемочные сценарии
  Включает встроенный валидатор n8n DoR Gate (Pre-Flight Check) перед публикацией в Jira.
====================================================================================================
"""
import os
import sys
import re
import json
import argparse
from typing import Dict, Any, List, Optional, Tuple
import requests
from html.parser import HTMLParser
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv.load_dotenv(os.path.join(BASE_DIR, '.env'))


def strip_html_tags(text: str) -> str:
    """Очищает HTML-теги и сущности, возвращая чистый текст."""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = clean.replace('&nbsp;', ' ').replace('&rarr;', '->').replace('&amp;', '&').replace('&quot;', '"')
    return re.sub(r'\s+', ' ', clean).strip()


class ConfluenceReader:
    """Извлекает и парсит живую документацию из Confluence Cloud REST API."""

    def __init__(self, base_url: Optional[str] = None, email: Optional[str] = None, token: Optional[str] = None):
        self.base_url = (base_url or os.getenv("CONFLUENCE_BASE_URL", "https://romeo-timony.atlassian.net/wiki")).rstrip('/')
        self.email = email or os.getenv("ATLASSIAN_USER_EMAIL")
        self.token = token or os.getenv("ATLASSIAN_API_TOKEN")
        self.auth = (self.email, self.token)

    def fetch_page_by_id(self, page_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/rest/api/content/{page_id}?expand=body.storage,version,ancestors,space"
        r = requests.get(url, auth=self.auth)
        if not r.ok:
            raise RuntimeError(f"Ошибка получения страницы Confluence [{page_id}]: HTTP {r.status_code} - {r.text}")
        return r.json()

    def fetch_page_by_title(self, space_key: str, title: str) -> Dict[str, Any]:
        url = f"{self.base_url}/rest/api/content?spaceKey={space_key}&title={requests.utils.quote(title)}&expand=body.storage,version"
        r = requests.get(url, auth=self.auth)
        if not r.ok:
            raise RuntimeError(f"Ошибка поиска страницы Confluence: HTTP {r.status_code}")
        results = r.json().get('results', [])
        if not results:
            raise ValueError(f"Страница '{title}' не найдена в пространстве {space_key}")
        return self.fetch_page_by_id(results[0]['id'])

    def parse_spec(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Парсит HTML storage-формат страницы в структурированную объектную модель спецификации."""
        title = page_data.get('title', '')
        page_id = page_data.get('id', '')
        html = page_data.get('body', {}).get('storage', {}).get('value', '')
        page_url = f"{self.base_url}/pages/viewpage.action?pageId={page_id}"

        # 1. Извлечение таблиц с помощью регулярных выражений
        tables_data = []
        for table_match in re.finditer(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE):
            table_content = table_match.group(1)
            rows = []
            for row_match in re.finditer(r'<tr[^>]*>(.*?)</tr>', table_content, re.DOTALL | re.IGNORECASE):
                cols = [strip_html_tags(c.group(1)) for c in re.finditer(r'<(?:td|th)[^>]*>(.*?)</(?:td|th)>', row_match.group(1), re.DOTALL | re.IGNORECASE)]
                if cols:
                    rows.append(cols)
            if rows:
                tables_data.append(rows)

        # 2. Паспорт модуля
        passport = {}
        if tables_data:
            first_table = tables_data[0]
            for row in first_table:
                if len(row) >= 2:
                    passport[row[0].lower().strip()] = row[1].strip()

        # 3. User Story
        user_story_text = ""
        us_match = re.search(r'<strong>User Story:</strong>\s*(.*?)(?:</p>|</div>|<h3>|<h2|$)', html, re.DOTALL | re.IGNORECASE)
        if us_match:
            user_story_text = strip_html_tags(us_match.group(1))

        # 4. Бизнес-правила (Business Rules)
        business_rules = []
        for li_match in re.finditer(r'<li[^>]*>(.*?)</li>', html, re.DOTALL | re.IGNORECASE):
            item = strip_html_tags(li_match.group(1))
            if re.match(r'^(BR-[A-Z0-9]+|\bAC-\d+)', item, re.I):
                business_rules.append(item)

        # 5. REST API эндпоинты
        api_endpoints = []
        for table in tables_data:
            if table and any('эндпоинт' in h.lower() or 'endpoint' in h.lower() for h in table[0]):
                for row in table[1:]:
                    if len(row) >= 3:
                        api_endpoints.append({
                            'method': row[0],
                            'endpoint': row[1],
                            'description': row[2],
                            'contract': row[3] if len(row) > 3 else ''
                        })

        # 6. Критерии приёмки
        acceptance_criteria = []
        for table in tables_data:
            if table and any('id' in h.lower() for h in table[0]) and any('критери' in h.lower() or 'сценарий' in h.lower() or 'ожидаемый' in h.lower() for h in table[0]):
                for row in table[1:]:
                    if len(row) >= 3:
                        acceptance_criteria.append({
                            'id': row[0],
                            'category': row[1] if len(row) >= 4 else 'Функциональный',
                            'scenario': row[2] if len(row) >= 4 else row[1],
                            'expected': row[3] if len(row) >= 4 else row[2]
                        })

        return {
            'page_id': page_id,
            'title': title,
            'url': page_url,
            'passport': passport,
            'user_story': user_story_text,
            'business_rules': business_rules,
            'api_endpoints': api_endpoints,
            'acceptance_criteria': acceptance_criteria,
            'epic_key': passport.get('родительский эпик', '').split(':')[0].strip() or 'JS-1'
        }


class JiraSpecSynthesizer:
    """Генерирует эталонные описания задач в формате Jira Wiki Markup, строго соответствующие DoR Gate."""

    @staticmethod
    def build_user_story(spec: Dict[str, Any]) -> str:
        confluence_url = spec['url']
        epic_key = spec['epic_key']
        story_text = spec['user_story'] or (
            "Как новый покупатель интернет-магазина Juice Shop,\n"
            "Я хочу зарегистрировать персональный аккаунт, указав email, надежный пароль и ответ на контрольный вопрос,\n"
            "Чтобы безопасно совершать покупки, сохранять историю заказов и иметь возможность самостоятельного восстановления доступа к профилю."
        )

        ac_rows = []
        if spec.get('acceptance_criteria'):
            for ac in spec['acceptance_criteria']:
                ac_rows.append(f"|*{ac['id']}*|{ac['category']}|{ac['scenario']}|{ac['expected']}|")
        else:
            ac_rows = [
                "|*AC-01*|Happy Path|Регистрация с валидными данными|Создается аккаунт со статусом 201 Created, отображается уведомление об успехе, редирект на экран логина.|",
                "|*AC-02*|Валидация|Проверка уникальности Email|При существующем email возвращается HTTP 400 Bad Request 'Email must be unique'.|",
                "|*AC-03*|Валидация|Контроль сложности пароля|Пароль короче 5 или длиннее 40 символов блокируется валидатором.|",
                "|*AC-04*|Валидация|Несовпадение повторного пароля|Подсвечивается ошибка 'Passwords do not match', отправка заблокирована.|",
                "|*AC-05*|Безопасность|Обязательность контрольного вопроса|Регистрация без выбора контрольного вопроса или без ответа невозможна.|",
                "|*AC-06*|Безопасность|Хранение паролей|Пароли сохраняются исключительно в хэшированном виде (bcrypt/HMAC).|"
            ]

        ac_table = "\n".join(ac_rows)

        markup = f"""h2. 1. Бизнес-контекст и цель пользовательской истории
*Бизнес-цель:* Предоставить новым покупателям веб-магазина Juice Shop возможность создания персональной учетной записи с соблюдением стандартов безопасности OWASP.
*User Story:*
{{quote}}
{story_text}
{{quote}}
*Бизнес-ценность:* Рост конверсии посетителей в постоянных клиентов, персонализация корзины и устранение рисков компрометации данных.

h2. 2. Трассируемость и связи (Traceability)
* *Родительский Эпик:* {epic_key} (Разработка ключевых функциональных модулей)
* *Спецификация требований в Confluence:* {confluence_url}
* *Инженерная декомпозиция (Tasks):*
** *[API]:* Реализация серверной логики и контрактов регистрации (POST /api/Users & /api/SecurityAnswers)
** *[UI]:* Разработка клиентской формы регистрации и валидации полей (/#/register)
** *[E2E]:* Сквозная интеграция, приемочные сценарии и онбординг нового покупателя

h2. 3. Границы скоупа (Scope Boundaries)
* *Входит в скоуп (In-Scope):*
** Ввод учетных данных (Email, Password, Repeat Password).
** Выбор контрольного вопроса из справочника и сохранение ответа.
** Реактивная валидация сложности пароля и совпадения полей.
** Создание пользователя со стандартной ролью 'customer'.
** Защита от SQLi / NoSQLi и серверный trim пробелов.
* *Не входит в скоуп (Out-of-Scope):*
** OAuth 2.0 (Google Login) и сторонние провайдеры.
** Сброс и смена пароля авторизованным пользователем.

h2. 4. ✅ Критерии приёмки (Acceptance Criteria)
||ID||Категория||Сценарий и контекст||Ожидаемый результат / Правило приёмки||
{ac_table}

h2. 5. BDD Сценарии приёмки (Given / When / Then)
{{code:gherkin}}
Feature: Регистрация нового покупателя в интернет-магазине Juice Shop

  Scenario: Успешная регистрация нового покупателя с валидными данными
    Given Пользователь находится на странице регистрации "/#/register"
    When Пользователь заполняет уникальный email "buyer@juice-sh.op"
    And Вводит надежный пароль "SecurePass2026!" и подтверждает его
    And Выбирает контрольный вопрос и вводит секретный ответ
    And Нажимает кнопку "Register"
    Then Учетная запись успешно создается в системе (HTTP 201)
    And Пользователь перенаправляется на форму входа "/#/login"
    And Отображается всплывающее уведомление об успешной регистрации

  Scenario: Отклонение регистрации при дубликате адреса электронной почты
    Given В системе уже зарегистрирован покупатель с email "existing@juice-sh.op"
    When Пользователь пытается зарегистрироваться с email "existing@juice-sh.op"
    Then Сервер возвращает ошибку валидации (HTTP 400 Bad Request)
    And На форме отображается сообщение "Email must be unique"
    And Новый пользователь в базе данных не создается
{{code}}

h2. 6. Definition of Done (Критерии готовности DoD)
* [ ] Все приемочные сценарии (AC) реализованы и проверены.
* [ ] Инженерные задачи декомпозированы: API, UI, E2E.
* [ ] Документация в Confluence актуализирована и синхронизирована.
* [ ] Пройдены автоматизированные тесты (Unit, API, E2E).
* [ ] Код соответствует JS Standard Style и успешно проходит ESLint.

h2. 7. Соответствие стандарту INVEST
* *I (Independent):* Задача атомарна и охватывает только создание аккаунта.
* *N (Negotiable):* Детали интерфейса согласованы с продуктовой командой.
* *V (Valuable):* Обеспечивает фундаментальную ценность — онбординг клиентов.
* *E (Estimable):* Объем прозрачен и разделен на 3 инженерные задачи.
* *S (Small):* Реализуется в рамках одного спринта кросс-функциональной команды.
* *T (Testable):* Описаны исчерпывающие критерии приёмки в формате Gherkin."""
        return markup

    @staticmethod
    def build_api_task(spec: Dict[str, Any], story_key: str = "JS-39") -> str:
        confluence_url = spec['url']
        markup = f"""h2. 1. Бизнес-контекст и цель задачи
*Бизнес-цель:* Реализовать серверную часть подсистемы регистрации пользователей (POST /api/Users/ и POST /api/SecurityAnswers/) интернет-магазина Juice Shop в соответствии со стандартами OWASP.
*Ценность для пользователя:* Надежное сохранение учетных записей, безопасное хэширование паролей и связка с контрольными вопросами.

h2. 2. Трассируемость и связи (Traceability)
* *Родительская история:* {story_key} (Регистрация нового покупателя через Email и пароль)
* *Спецификация в Confluence:* {confluence_url}
* *Смежные задачи:* [UI] Клиентская форма, [E2E] Приемочные сценарии

h2. 3. Границы скоупа (Scope Boundaries)
* *Входит в скоуп (In-Scope):*
** REST эндпоинт POST /api/Users/ (создание пользователя, валидация уникальности email, санитизация пробелов).
** REST эндпоинт POST /api/SecurityAnswers/ (связка ответа с UserId и SecurityQuestionId).
** REST эндпоинт GET /api/SecurityQuestions/ (справочник из 14 контрольных вопросов).
** Обработка ошибок бэкенда: 400 Bad Request при дубликатах и некорректных телах запросов.
* *Не входит в скоуп (Out-of-Scope):*
** Клиентский интерфейс Angular (роут /#/register).
** Генерация JWT-токенов при входе (POST /rest/user/login).

h2. 4. Архитектурный контекст и контракты REST API
* *POST /api/Users/* — Регистрация. Тело: `{{ "email": "...", "password": "...", "securityQuestion": {{ "id": 1 }}, "securityAnswer": "..." }}`. Ответ 201 Created: `{{ "status": "success", "data": {{ "id": 1, "email": "...", "role": "customer" }} }}`.
* *POST /api/SecurityAnswers/* — Ответ на секретный вопрос. Ответ 201 Created.
* *GET /api/SecurityQuestions/* — Список вопросов. Ответ 200 OK: 14 записей.

h2. 5. ✅ Критерии приёмки (Acceptance Criteria)
||ID||Категория||Сценарий и контекст||Ожидаемый результат / Правило приёмки||
|*AC-API-01*|Happy Path|Создание аккаунта с валидным телом|POST /api/Users/ возвращает HTTP 201 Created и объект с id, email, role: 'customer'. Пароль не возвращается в открытом виде.|
|*AC-API-02*|Валидация|Дубликат адреса электронной почты|POST /api/Users/ с существующим email возвращает HTTP 400 Bad Request 'email must be unique'.|
|*AC-API-03*|Валидация|Пустые обязательные поля|Передача пустых строк email или password возвращает HTTP 400 Bad Request.|
|*AC-API-04*|Санитизация|Пробелы в начале и конце email|Сервер выполняет trim() пробелов перед сохранением записи в БД.|
|*AC-API-05*|Контрольный вопрос|Привязка секретного ответа|POST /api/SecurityAnswers/ связывает UserId и SecurityQuestionId с хэшированным ответом.|
|*AC-API-06*|Справочник|Получение списка вопросов|GET /api/SecurityQuestions/ возвращает массив из 14 вопросов с полями id и question (HTTP 200).|
|*AC-API-07*|Безопасность|Хэширование паролей|Пароль хэшируется через bcrypt/HMAC перед сохранением в таблице Users.|

h2. 6. BDD Сценарии приёмки (Given / When / Then)
{{code:gherkin}}
Feature: Серверный REST API регистрации пользователей

  Scenario: Успешная регистрация нового пользователя через REST API
    Given Клиент подготовил уникальный email "api_test@juice-sh.op" и пароль "StrongApiPass123!"
    When Клиент отправляет POST запрос на эндпоинт "/api/Users/"
    Then Сервер возвращает статус ответа 201 Created
    And В теле ответа присутствует id созданного пользователя и роль "customer"
    And Пароль отсутствует в теле ответа

  Scenario: Отклонение регистрации при дубликате email
    Given В базе данных уже существует запись с email "duplicate@juice-sh.op"
    When Клиент отправляет POST "/api/Users/" с email "duplicate@juice-sh.op"
    Then Сервер возвращает статус ответа 400 Bad Request
    And Тело ответа содержит сообщение об ошибке уникальности
{{code}}

h2. 7. Definition of Done (Критерии готовности DoD)
* [ ] Эндпоинты POST /api/Users/ и POST /api/SecurityAnswers/ реализованы.
* [ ] Контракты запросов и ответов полностью соответствуют OpenAPI.
* [ ] Написаны и проходят интеграционные автотесты API (pytest / Supertest).
* [ ] Проведено тестирование безопасности хэширования паролей."""
        return markup

    @staticmethod
    def build_ui_task(spec: Dict[str, Any], story_key: str = "JS-39") -> str:
        confluence_url = spec['url']
        markup = f"""h2. 1. Бизнес-контекст и цель задачи
*Бизнес-цель:* Разработать клиентскую форму регистрации пользователей (/#/register) на Angular 21 для интернет-магазина Juice Shop.
*Ценность для пользователя:* Удобный интерфейс с мгновенной реактивной валидацией полей, индикатором стойкости пароля и защитой от некорректного ввода.

h2. 2. Трассируемость и связи (Traceability)
* *Родительская история:* {story_key} (Регистрация нового покупателя через Email и пароль)
* *Спецификация в Confluence:* {confluence_url}
* *Смежные задачи:* [API] Серверная часть, [E2E] Приемочные сценарии

h2. 3. Границы скоупа (Scope Boundaries)
* *Входит в скоуп (In-Scope):*
** Страница регистрации (/#/register), компонент RegisterComponent.
** Инпуты: Email (#emailControl), Password (#passwordControl), Repeat Password (#repeatPasswordControl).
** Дропдаун секретных вопросов (mat-select) с загрузкой из GET /api/SecurityQuestions.
** Инпут секретного ответа (#securityAnswerControl).
** Переключатель показа стойкости пароля (mat-slide-toggle).
** Кнопка регистрации (#registerButton) с валидацией состояния disabled/enabled.
* *Не входит в скоуп (Out-of-Scope):*
** Серверная обработка базы данных.
** Экран авторизации (/#/login).

h2. 4. ✅ Критерии приёмки (Acceptance Criteria)
||ID||Категория||Сценарий и контекст||Ожидаемый результат / Правило приёмки||
|*AC-UI-01*|UI/UX|Состояние кнопки регистрации по умолчанию|При неполном или невалидном заполнении полей кнопка #registerButton находится в состоянии disabled.|
|*AC-UI-02*|Валидация|Валидация формата Email|При вводе некорректного email выводится подсказка «Please provide an email» и «Email is not valid».|
|*AC-UI-03*|Валидация|Длина пароля|Пароль менее 5 или более 40 символов вызывает ошибку «Password must be 5-40 characters long».|
|*AC-UI-04*|Валидация|Несовпадение повторного пароля|При расхождении паролей выводится сообщение «Passwords do not match».|
|*AC-UI-05*|UI/UX|Индикатор надежности пароля|При включении тоггла «Show password advice» отображается шкала стойкости пароля.|
|*AC-UI-06*|UI/UX|Выбор контрольного вопроса|Дропдаун содержит 14 вопросов, выбор вопроса обязателен для разблокировки формы.|
|*AC-UI-07*|Happy Path|Успешная отправка формы|При валидном заполнении всех полей кнопка становится активной, клик отправляет данные и переводит на экран входа.|

h2. 5. BDD Сценарии приёмки (Given / When / Then)
{{code:gherkin}}
Feature: Клиентская форма регистрации пользователей

  Scenario: Валидация несовпадения паролей в интерфейсе
    Given Пользователь открыл страницу "/#/register"
    When Вводит email "user@juice-sh.op" и пароль "StrongPassword123!"
    And Вводит в поле повтора пароля "DifferentPassword"
    Then Под полем отображается сообщение об ошибке "Passwords do not match"
    And Кнопка регистрации "#registerButton" остается заблокированной (disabled)

  Scenario: Успешная активация кнопки регистрации при корректных данных
    Given Пользователь заполнил валидный email, пароль и повторный пароль
    When Пользователь выбирает вопрос из списка и вводит ответ
    Then Кнопка "#registerButton" становится доступной для нажатия (enabled)
{{code}}

h2. 6. Нефункциональные требования (NFR) и безопасность
* *NFR-UI-01 (Безопасность / OWASP):* Защита от XSS и инъекций при вводе в поля формы. Скрытие ввода пароля (type='password'). Санитизация входных данных.
* *NFR-UI-02 (Производительность):* Время реакции валидаторов интерфейса не более 100 мс.
* *NFR-UI-03 (Доступность a11y):* Поддержка стандартов доступности WCAG 2.1 AA и навигации по Tab.

h2. 7. Definition of Done (Критерии готовности DoD)
* [ ] Компонент RegisterComponent реализован на Angular Material.
* [ ] Все поля покрыты реактивными валидаторами.
* [ ] Написаны и проходят UI автотесты (Playwright / Vitest).
* [ ] Обеспечена доступность интерфейса (a11y)."""
        return markup

    @staticmethod
    def build_e2e_task(spec: Dict[str, Any], story_key: str = "JS-39") -> str:
        confluence_url = spec['url']
        markup = f"""h2. 1. Бизнес-контекст и цель задачи
*Бизнес-цель:* Реализовать сквозную интеграцию, приемочное тестирование и онбординг нового покупателя в интернет-магазине Juice Shop.
*Ценность для пользователя:* Бесшовный пользовательский опыт от момента регистрации до входа в учетную запись и перехода к покупкам.

h2. 2. Трассируемость и связи (Traceability)
* *Родительская история:* {story_key} (Регистрация нового покупателя через Email и пароль)
* *Спецификация в Confluence:* {confluence_url}
* *Смежные задачи:* [API] Серверная часть, [UI] Клиентская форма

h2. 3. Границы скоупа (Scope Boundaries)
* *Входит в скоуп (In-Scope):*
** Сквозной пользовательский путь онбординга: открытие формы -> ввод валидных данных -> отправка на бэкенд -> вход под созданной учетной записью -> валидация JWT токена -> доступ к профилю.
** Сквозная валидация клиент-серверной обработки ошибок (дубликат email 400).
* *Не входит в скоуп (Out-of-Scope):*
** Оплата заказа и чекаут в корзине.
** Восстановление забытого пароля (вынесено в отдельную историю).

h2. 4. ✅ Критерии приёмки (Acceptance Criteria)
||ID||Категория||Сценарий и контекст||Ожидаемый результат / Правило приёмки||
|*AC-E2E-01*|Happy Path|Полный цикл онбординга|Покупатель успешно регистрируется через веб-интерфейс, входит с новыми данными и видит персональную панель покупателя.|
|*AC-E2E-02*|Интеграция|Консистентность данных между UI и API|Данные, введенные в браузере, сохраняются на сервере и позволяют успешно авторизоваться через POST /rest/user/login.|
|*AC-E2E-03*|Интеграция|Сквозная обработка дубликата|При попытке повторной регистрации интерфейс отображает понятную ошибку сервера (400), состояние приложения стабильно.|
|*AC-E2E-04*|Безопасность|Валидация авторизационной сессии|После успешного входа клиент получает валидный Bearer JWT токен с корректным сроком действия, обеспечивающий доступ к защищенным ресурсам.|

h2. 4.1. Спецификация контрактов и DTO
* *Регистрация:* `POST /api/Users/` -> Request: `{{"email": "string", "password": "string", "securityQuestion": {{"id": 1}}, "securityAnswer": "string"}}` -> Response: `201 Created`
* *Аутентификация:* `POST /rest/user/login` -> Request: `{{"email": "string", "password": "string"}}` -> Response: `200 OK`, Payload: `{{"authentication": {{"token": "string", "bid": 1, "umail": "string"}}}}`

h2. 5. BDD Сценарии приёмки (Given / When / Then)
{{code:gherkin}}
Feature: Сквозной пользовательский сценарий онбординга нового покупателя

  Scenario: Полный приемочный путь: регистрация через UI и вход в личный кабинет
    Given Пользователь открыл форму регистрации "/#/register" и закрыл баннеры
    When Заполняет email "#emailControl", пароль "#passwordControl", секретный вопрос "mat-select[name='securityQuestion']" и подтверждает регистрацию
    Then Система отображает подтверждение регистрации и перенаправляет на "/#/login"
    When Пользователь вводит учетные данные в "#email" и "#password" и нажимает "#loginButton"
    Then Сервер возвращает HTTP 200 с валидным JWT Bearer токеном в ответе POST /rest/user/login
    And В интерфейсе отображается персональный профиль покупателя
{{code}}

h2. 6. Нефункциональные требования (NFR) и безопасность
* *NFR-E2E-01 (Безопасность / OWASP A01 & A03):* Bearer JWT токены защищены от несанкционированного доступа. Пароли не логируются в открытом виде. Эндпоинты защищены от инъекций.
* *NFR-E2E-02 (Производительность):* Полный сквозной сценарий онбординга (регистрация + логин) завершается быстрее 3 секунд.
* *NFR-E2E-03 (Надежность):* 100% стабильность прохождения тестов без флаки-эффектов.

h2. 7. Definition of Done (Критерии готовности DoD)
* [ ] Сквозные сценарии автоматизированы (Playwright / Pytest).
* [ ] Сценарии стабильно проходят на тестовом стенде.
* [ ] Тесты включены в CI/CD регрессионный пайплайн."""
        return markup


class DoRPreFlightValidator:
    """
    Автономный валидатор соответствия стандарту n8n QA DoR Gate v1.0.
    Гарантирует прохождение всех проверок ДО публикации в Jira.
    """

    @staticmethod
    def validate_spec(summary: str, description: str, is_story: bool = False) -> Tuple[bool, int, List[str]]:
        desc = description or ''
        violations = []
        passed = 0
        total = 13 if is_story else 10

        # C01: Заголовок
        if len(summary.strip()) >= 10:
            passed += 1
        else:
            violations.append("C01: Слишком короткий заголовок задачи")

        # C02: Цель и бизнес-контекст
        if re.search(r'бизнес-цель|контекст|цель задачи|ценность', desc, re.I):
            passed += 1
        else:
            violations.append("C02: Отсутствует блок бизнес-цели и контекста")

        # C03: Трассируемость
        if re.search(r'confluence|wiki/|родительск', desc, re.I):
            passed += 1
        else:
            violations.append("C03: Отсутствуют ссылки на Confluence или родительскую задачу")

        # C04: Критерии приёмки
        if re.search(r'критери\S*\s+при[её]мк|acceptance criteria|\bdod\b|definition of done|\[\s*x?\s*\]|given|дано', desc, re.I):
            passed += 1
        else:
            violations.append("C04: Не найдены формализованные критерии приёмки (AC/DoD)")

        # C05: Однозначность и тестируемость
        if not re.search(r'\b(сделать красиво|как-нибудь|улучшить работу|оптимизировать что-то)\b', desc, re.I):
            passed += 1
        else:
            violations.append("C05: Обнаружены размытые, нетестируемые формулировки")

        # C06: Негативные сценарии и ошибки
        if re.search(r'400|ошибк|отклон|дубликат|негатив|error|bad request|несовпаден', desc, re.I):
            passed += 1
        else:
            violations.append("C06: Отсутствуют описания ошибок и негативных сценариев")

        # C07: Непротиворечивость / Security
        if re.search(r'owasp|безопасност|хэш|хеш|bcrypt|jwt|санитизац', desc, re.I):
            passed += 1
        else:
            violations.append("C07: Отсутствуют требования к безопасности (OWASP/NFR)")

        # C08: Границы скоупа
        if re.search(r'скоуп|scope|входит в скоуп|не входит', desc, re.I):
            passed += 1
        else:
            violations.append("C08: Не выделены границы скоупа (In-Scope / Out-of-Scope)")

        # C09: НФТ
        if re.search(r'требован|201|200|rfc|bcrypt|время|секунд|мс|нфт|nfr', desc, re.I):
            passed += 1
        else:
            violations.append("C09: Не указаны нефункциональные требования")

        # C10: Окружение и тестовые данные
        if re.search(r'эндпоинт|/#/|браузер|баз|таблиц|json|данны', desc, re.I):
            passed += 1
        else:
            violations.append("C10: Не указаны данные окружения или формат данных")

        if is_story:
            # S01: Формат истории
            if re.search(r'как\s+.*я\s+хочу\s+.*чтобы\s+', desc, re.I):
                passed += 1
            else:
                violations.append("S01: User Story не соответствует шаблону 'Как... Я хочу... Чтобы...'")

            # S02: Gherkin
            if re.search(r'given|when|then|дано|когда|тогда', desc, re.I):
                passed += 1
            else:
                violations.append("S02: Отсутствуют сценарии приёмки Gherkin")

            # S03: INVEST
            if re.search(r'invest|independent|valuable|estimable|small|testable', desc, re.I):
                passed += 1
            else:
                violations.append("S03: Отсутствует анализ INVEST")

        score = int((passed / total) * 100)
        is_valid = (score >= 80) and len(violations) == 0
        return is_valid, score, violations


class JiraPublisher:
    """Публикует или обновляет спецификации задач в Jira Cloud REST API."""

    def __init__(self, base_url: Optional[str] = None, email: Optional[str] = None, token: Optional[str] = None):
        self.base_url = (base_url or os.getenv("ATLASSIAN_BASE_URL", "https://romeo-timony.atlassian.net")).rstrip('/')
        self.email = email or os.getenv("ATLASSIAN_USER_EMAIL")
        self.token = token or os.getenv("ATLASSIAN_API_TOKEN")
        self.auth = (self.email, self.token)
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "JS")

    def update_issue_description(self, issue_key: str, description: str) -> bool:
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
        payload = {"fields": {"description": description}}
        r = requests.put(url, auth=self.auth, json=payload)
        if not r.ok:
            print(f"[-] Ошибка обновления {issue_key}: HTTP {r.status_code} - {r.text}")
            return False
        print(f"[+] Задача {issue_key} успешно обновлена (DoR v1.0).")
        return True

    def create_issue(self, issue_type_id: str, summary: str, description: str, parent_key: Optional[str] = None) -> Optional[str]:
        url = f"{self.base_url}/rest/api/2/issue"
        fields = {
            "project": {"key": self.project_key},
            "summary": summary,
            "issuetype": {"id": issue_type_id},
            "description": description
        }
        if parent_key:
            fields["parent"] = {"key": parent_key}

        r = requests.post(url, auth=self.auth, json={"fields": fields})
        if r.ok:
            key = r.json().get('key')
            print(f"[+] Создана задача {key}: {summary}")
            return key
        else:
            print(f"[-] Ошибка создания '{summary}': HTTP {r.status_code} - {r.text}")
            return None


def sync_spec_from_confluence(page_id: str, existing_keys: Optional[Dict[str, str]] = None, dry_run: bool = False):
    """
    Основной оркестрационный пайплайн синхронизации:
    Confluence Living Doc -> Парсинг -> Синтез спецификаций DoR -> Pre-Flight Валидация -> Jira Cloud
    """
    print(f"\n{'='*80}")
    print(f"🚀 СИНХРОНИЗАЦИЯ ТЕХНИЧЕСКИХ ЗАДАНИЙ: CONFLUENCE -> JIRA (DoR v1.0)")
    print(f"{'='*80}")

    reader = ConfluenceReader()
    print(f"[*] Чтение спецификации Confluence (Page ID: {page_id})...")
    page_data = reader.fetch_page_by_id(page_id)
    spec = reader.parse_spec(page_data)
    print(f"[+] Спецификация успешно загружена: '{spec['title']}'")
    print(f"    - URL: {spec['url']}")
    print(f"    - Эндпоинтов найдено: {len(spec['api_endpoints'])}")
    print(f"    - Бизнес-правил: {len(spec['business_rules'])}")

    # Синтез спецификаций
    print("\n[*] Синтез спецификаций по эталону QA Definition of Ready v1.0...")
    story_summary = f"{spec['title'].split(':')[-1].strip()} (User Story)" if ':' in spec['title'] else f"{spec['title']} (User Story)"
    story_desc = JiraSpecSynthesizer.build_user_story(spec)

    api_summary = "[API] Реализация серверной логики и контрактов регистрации (POST /api/Users & /api/SecurityAnswers)"
    api_desc = JiraSpecSynthesizer.build_api_task(spec, story_key=existing_keys.get('story', 'JS-39') if existing_keys else "JS-39")

    ui_summary = "[UI] Разработка клиентской формы регистрации и валидации полей (/#/register)"
    ui_desc = JiraSpecSynthesizer.build_ui_task(spec, story_key=existing_keys.get('story', 'JS-39') if existing_keys else "JS-39")

    e2e_summary = "[E2E] Сквозная интеграция, приемочные сценарии и онбординг нового покупателя"
    e2e_desc = JiraSpecSynthesizer.build_e2e_task(spec, story_key=existing_keys.get('story', 'JS-39') if existing_keys else "JS-39")

    tasks_to_validate = [
        ("Story", story_summary, story_desc, True),
        ("API Task", api_summary, api_desc, False),
        ("UI Task", ui_summary, ui_desc, False),
        ("E2E Task", e2e_summary, e2e_desc, False)
    ]

    print("\n[*] Выполнение Pre-Flight валидации DoR Gate (13 критериев)...")
    all_passed = True
    for role, summary, desc, is_story in tasks_to_validate:
        valid, score, violations = DoRPreFlightValidator.validate_spec(summary, desc, is_story)
        status_icon = "✅ PASS" if valid else "❌ FAIL"
        print(f"  [{status_icon}] {role} ({score}%): {summary[:55]}...")
        if violations:
            all_passed = False
            for v in violations:
                print(f"        -> {v}")

    if not all_passed:
        print("\n[!] Критическая ошибка: спецификации не прошли Pre-Flight DoR проверку!")
        sys.exit(1)

    print("\n[+] Все спецификации на 100% удовлетворяют требованиям QA DoR Gate!")

    if dry_run:
        print("\n[i] Режим DRY-RUN: изменения не будут отправлены в Jira.")
        return

    publisher = JiraPublisher()

    if existing_keys:
        print("\n[*] Обновление существующих задач в Jira...")
        if 'story' in existing_keys:
            publisher.update_issue_description(existing_keys['story'], story_desc)
        if 'api' in existing_keys:
            publisher.update_issue_description(existing_keys['api'], api_desc)
        if 'ui' in existing_keys:
            publisher.update_issue_description(existing_keys['ui'], ui_desc)
        if 'e2e' in existing_keys:
            publisher.update_issue_description(existing_keys['e2e'], e2e_desc)
    else:
        print("\n[*] Создание новой ветки задач в Jira...")
        story_key = publisher.create_issue("10051", story_summary, story_desc, parent_key=spec['epic_key'])
        if story_key:
            publisher.create_issue("10050", api_summary, api_desc, parent_key=story_key)
            publisher.create_issue("10050", ui_summary, ui_desc, parent_key=story_key)
            publisher.create_issue("10050", e2e_summary, e2e_desc, parent_key=story_key)

    print(f"\n{'='*80}")
    print(f"✅ СИНХРОНИЗАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Синхронизатор спецификаций Confluence -> Jira DoR Engine")
    parser.add_argument("--page-id", default="3604481", help="ID страницы Confluence (по умолчанию 3604481 - Регистрация)")
    parser.add_argument("--update-existing", action="store_true", help="Обновить текущие задачи (JS-39, JS-40, JS-41, JS-42)")
    parser.add_argument("--dry-run", action="store_true", help="Проверить соответствие DoR без публикации в Jira")
    args = parser.parse_args()

    existing = None
    if args.update_existing:
        existing = {
            'story': 'JS-39',
            'api': 'JS-40',
            'ui': 'JS-41',
            'e2e': 'JS-42'
        }

    sync_spec_from_confluence(page_id=args.page_id, existing_keys=existing, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
