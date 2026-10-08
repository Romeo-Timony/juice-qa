const fs = require('fs')
const path = require('path')
const crypto = require('crypto')

const NODES_DIR = path.join(__dirname, 'nodes')
const WEBHOOK_PATH = 'jira-dor-gate'
const WORKFLOW_NAME = 'Juice Shop'

const code = file => fs.readFileSync(path.join(NODES_DIR, file), 'utf8')

function buildWorkflow ({ jiraCred, geminiCred, qaseCred, webhookToken, geminiModel, qaseCode = 'JS' }) {
  const jiraCreds = { jiraSoftwareCloudApi: jiraCred }
  const qaseCreds = { httpHeaderAuth: qaseCred }
  const FILTER = "$('Фильтр: Задача взята в работу').first().json"
  const issueUrl = suffix => `={{ ${FILTER}.config.jiraBase + '/rest/api/2/issue/' + ${FILTER}.issueKey + '${suffix}' }}`

  const codeNode = (name, file, position, replacements = {}) => {
    let jsCode = code(file)
    for (const [k, v] of Object.entries(replacements)) jsCode = jsCode.split(k).join(v)
    return { parameters: { jsCode }, name, type: 'n8n-nodes-base.code', typeVersion: 2, position }
  }

  const jira = (name, method, url, position, jsonBody) => ({
    parameters: {
      method,
      url,
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'jiraSoftwareCloudApi',
      ...(jsonBody ? { sendBody: true, specifyBody: 'json', jsonBody } : {}),
      options: {}
    },
    name,
    type: 'n8n-nodes-base.httpRequest',
    typeVersion: 4.2,
    position,
    credentials: jiraCreds,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 3000
  })

  const stickyNote = (name, content, position, width, height, color = 1) => ({
    parameters: { content, width, height, color },
    name,
    type: 'n8n-nodes-base.stickyNote',
    typeVersion: 1,
    position
  })

  const commentBody = '={{ JSON.stringify({ body: $json.commentBody }) }}'
  const casesReportBody = "={{ JSON.stringify({ body: $('Создание тест-кейсов без повторов').first().json.casesReport }) }}"
  const rtmCommentBody = "={{ JSON.stringify({ body: $('Создание тест-кейсов без повторов').first().json.rtmCommentBody }) }}"
  const gate1CardBody = "={{ JSON.stringify({ body: $('Контроль 1: Подтверждение тест-кейсов').first().json.gate1ReviewCard }) }}"
  const pollJql = encodeURIComponent('project = JS AND status = 10046 AND (labels is EMPTY OR labels not in (qa-dor-passed, qa-dor-failed, qa-dor-error))')

  const nodes = [
    // =========================================================================
    // 📌 НАГЛЯДНЫЕ СТИКЕРЫ (ОПИСАНИЕ ЭТАПОВ ДЛЯ ВСЕЙ КОМАНДЫ)
    // =========================================================================
    stickyNote(
      'Стикер: Приём задач',
      `## 📥 1. Приём задач из Jira
**Что здесь происходит:**
Система отслеживает задачи, которые команда взяла в работу.
* **Основной способ:** Мгновенное получение события от Jira при переводе задачи в статус «В работе».
* **Запасной способ:** Проверка Jira каждую минуту на случай сбоев сети, чтобы ни одна задача не потерялась.`,
      [-260, 40], 430, 420, 6 // Синий
    ),

    stickyNote(
      'Стикер: Проверка готовности (DoR)',
      `## 📋 2. Проверка готовности задачи (DoR) [Этап 1]
**Что здесь происходит:**
Проверяем, достаточно ли информации в задаче для начала работы.
* Загружаем описание, критерии приёмки и ссылки из Jira.
* Сверяем с 10 обязательными правилами (понятность сценария, ожидаемый результат, формат данных, безопасность).
* Публикуем **[Этап 1 из 7] QA-валидация требований (DoR Gate)**.
* Если данных мало — автоматически возвращаем задачу автору на уточнение.`,
      [190, 40], 1750, 420, 1 // Желтый
    ),

    stickyNote(
      'Стикер: Возврат задачи',
      `## ❌ 3. Возврат задачи при неполных требованиях
**Что здесь происходит:**
Защита команды от работы вслепую при неполных требованиях.
* Пишем в задачу подробный комментарий: чего именно не хватает и что нужно дописать.
* Автоматически возвращаем задачу в статус «К выполнению» (Transition ID: 11).
* Ставим понятную метку \`qa-dor-failed\`, чтобы статус был виден на доске.`,
      [1750, 470], 640, 260, 5 // Красный
    ),

    stickyNote(
      'Стикер: Интеллект-карта проверок',
      `## 🧠 4. Интеллект-карта проверок [Этап 2]
**Что здесь происходит:**
Искусственный интеллект проектирует многоуровневое дерево проверок.
* Формирует декомпозицию бизнес-сценариев, граничных значений и состояний UI/API.
* Публикует **[Этап 2 из 7] Интеллект-карта проверок (QA MindMap)** в Jira.`,
      [1970, 40], 640, 420, 4 // Фиолетовый
    ),

    stickyNote(
      'Стикер: Тест-кейсы и RTM',
      `## 🧪 5. Реестр тест-кейсов & Матрица RTM [Этапы 3 и 4]
**Что здесь происходит:**
Создание сценариев в базе Qase TMS и матрицы покрытия.
* Сверяется с существующими тестами в базе Qase, чтобы не создавать дубликаты.
* Публикует **[Этап 3 из 7] Реестр тест-кейсов (BDD)** в Jira.
* Публикует **[Этап 4 из 7] Матрица трассируемости требований (RTM)** в Jira.`,
      [2630, 40], 1300, 420, 4 // Фиолетовый
    ),

    stickyNote(
      'Стикер: Контроль 1',
      `## 🛡️ 6. Контроль 1: Подтверждение тест-кейсов [Этап 5]
**Что здесь происходит:**
Промежуточная проверка придуманных тестов перед сохранением в базу.
* Проверяем полноту: наличие основных и ошибочных сценариев.
* Публикует **[Этап 5 из 7] Контроль 1: Подтверждение тест-кейсов (Quality Gate 1)**.
* **В тестовом проекте:** Тесты подтверждаются автоматически без остановок.`,
      [3950, 40], 640, 420, 7 // Бирюзовый
    ),

    stickyNote(
      'Стикер: Сохранение и передача',
      `## 📦 7. Сохранение в Qase & Передача на автоматизацию
**Что здесь происходит:**
Фиксация тестов в единой базе тестирования и передача в разработку.
* Новые тесты автоматически создаются в системе Qase TMS (bulk API).
* В задачу Jira добавляется прямая ссылка на созданный набор тестов.
* Ставятся метки \`qa-dor-passed\` и \`qa-ready-for-autotests\`.
* Пайплайн n8n завершает Фазу 1. Далее Antigravity генерирует автотесты (Этапы 6 и 7).`,
      [4610, 40], 850, 420, 2 // Зеленый
    ),

    // =========================================================================
    // ⚙️ НОВЫЕ СТИКЕРЫ (ДЛЯ ЭТАПОВ 6, 7 И GITHUB ACTIONS)
    // =========================================================================

    stickyNote(
      'Стикер: Контроль 2 (Gate 2)',
      `## 🛡️ 8. Контроль 2: Генерация и проверка кода [Этап 6]
**Что здесь происходит:**
Автоматическая кодогенерация на Python/Playwright.
* Скрипт генерирует код автотестов.
* ИИ проверяет качество кода (Quality Gate 2).
* В случае успеха пропускает дальше, при ошибке — отклоняет.`,
      [5480, 40], 1080, 420, 3 // Синий
    ),

    stickyNote(
      'Стикер: Внедрение автотестов',
      `## 🚀 9. Внедрение автотестов [Этап 7]
**Что здесь происходит:**
Завершение работы пайплайна генерации.
* Утвержденный код переносится в рабочую папку проекта.
* Публикует финальный отчет о внедрении **[Этап 7 из 7]**.
* Сохраняет файлы на диск (для push'а в Git).`,
      [6600, 40], 600, 420, 5 // Розовый/Красный
    ),

    stickyNote(
      'Стикер: GitHub Actions Результаты',
      `## 🐙 10. Результаты прогона в GitHub Actions [Этап 8]
**Что здесь происходит:**
Прием отчета о результатах выполнения автотестов в CI/CD (GitHub).
* Слушает вебхук от пайплайна GitHub Actions.
* Извлекает статус и ссылку на Allure-отчет.
* Публикует итоговый вердикт с результатами тестов напрямую в Jira.`,
      [7240, 40], 700, 420, 6 // Желтый/Оранжевый
    ),

    // =========================================================================
    // ⚙️ ОСНОВНАЯ ЕДИНАЯ ЛИНИЯ НОД (БЕЗ ОТРЫВОВ И ЗАВИСШИХ ЭЛЕМЕНТОВ)
    // =========================================================================

    // 1. Приём задач
    {
      parameters: { httpMethod: 'POST', path: WEBHOOK_PATH, responseMode: 'onReceived', options: {} },
      name: 'Jira: Перехват обновления задачи',
      type: 'n8n-nodes-base.webhook',
      typeVersion: 2,
      position: [0, 180],
      webhookId: crypto.randomUUID()
    },
    {
      parameters: {},
      name: 'Execute Workflow Trigger',
      type: 'n8n-nodes-base.executeWorkflowTrigger',
      typeVersion: 1,
      position: [0, 320]
    },

    // 2. Проверка готовности (DoR)
    codeNode('Фильтр: Задача взята в работу', '01_filter_event.js', [240, 260], {
      __WEBHOOK_TOKEN__: webhookToken,
      __GEMINI_MODEL__: geminiModel
    }),
    jira('Jira: Загрузить данные задачи', 'GET', issueUrl('?fields=summary,description,issuetype,parent,labels,priority,issuelinks,subtasks,reporter,assignee,status'), [460, 260]),
    { ...jira('Jira: Загрузить ссылки задачи', 'GET', issueUrl('/remotelink'), [680, 260]), alwaysOutputData: true },
    codeNode('Правила проверки готовности задачи', '02_dor_standard.js', [900, 260]),
    codeNode('Подготовка задачи к проверке', '03_build_validation_prompt.js', [1120, 260]),
    codeNode('Проверка задачи на готовность', '04_evaluate_verdict.js', [1340, 260]),

    // Ветвление: Готова ли задача?
    {
      parameters: {
        conditions: {
          options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
          conditions: [
            {
              id: 'cond_passed',
              leftValue: '={{ $json.passed }}',
              rightValue: true,
              operator: { type: 'boolean', operation: 'equals' }
            }
          ],
          combinator: 'and'
        }
      },
      name: 'Условие: Требования задачи понятны?',
      type: 'n8n-nodes-base.if',
      typeVersion: 2,
      position: [1560, 260]
    },

    // 3. Ветка возврата (Fail Path)
    jira('Jira: Отправить замечания к задаче', 'POST', issueUrl('/comment'), [1800, 520], commentBody),
    jira('Jira: Вернуть задачу на доработку', 'POST', issueUrl('/transitions'), [2020, 520],
      '={{ JSON.stringify({ transition: { id: "11" } }) }}'),
    jira('Jira: Поставить метку Требует доработки', 'PUT', issueUrl(''), [2240, 520],
      '={{ JSON.stringify({ update: { labels: [{ add: "qa-dor-failed" }, { remove: "qa-dor-passed" }] } }) }}'),

    // 4. Ветка создания проверок (Pass Path)
    jira('Jira: Отчет 1 — Задача готова к работе (DoR Gate)', 'POST', issueUrl('/comment'), [1800, 260], commentBody),
    codeNode('Подготовка данных для чек-листа', '05_build_checklist_prompt.js', [2020, 260]),
    codeNode('Создание карты проверок', '06_format_checklist.js', [2240, 260]),
    jira('Jira: Отчет 2 — Интеллект-карта проверок', 'POST', issueUrl('/comment'), [2460, 260], commentBody),
    codeNode('Подготовка данных для тест-кейсов', '07_build_testcases_prompt.js', [2680, 260]),
    {
      parameters: {
        method: 'GET',
        url: `https://api.qase.io/v1/suite/${qaseCode}?limit=100`,
        authentication: 'predefinedCredentialType',
        nodeCredentialType: 'httpHeaderAuth',
        options: {}
      },
      name: 'Qase: Загрузить список папок',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 4.2,
      position: [2900, 260],
      credentials: qaseCreds
    },
    {
      parameters: {
        method: 'GET',
        url: `https://api.qase.io/v1/case/${qaseCode}?limit=100`,
        authentication: 'predefinedCredentialType',
        nodeCredentialType: 'httpHeaderAuth',
        options: {}
      },
      name: 'Qase: Загрузить существующие тесты',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 4.2,
      position: [3120, 260],
      credentials: qaseCreds
    },
    codeNode('Создание тест-кейсов без повторов', '08_format_testcases.js', [3340, 260]),
    jira('Jira: Отчет 3 — Реестр тест-кейсов (BDD)', 'POST', issueUrl('/comment'), [3560, 260], casesReportBody),
    jira('Jira: Отчет 4 — Матрица трассируемости (RTM)', 'POST', issueUrl('/comment'), [3780, 260], rtmCommentBody),

    // 5. Контроль 1: Подтверждение тест-кейсов
    codeNode('Контроль 1: Подтверждение тест-кейсов', '10_gate1_review_testcases.js', [4000, 260]),
    jira('Jira: Карточка подтверждения тестов (Gate 1)', 'POST', issueUrl('/comment'), [4220, 260], gate1CardBody),
    {
      parameters: {
        conditions: {
          options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
          conditions: [
            {
              id: 'cond_gate1_passed',
              leftValue: "={{ $('Контроль 1: Подтверждение тест-кейсов').first().json.gate1.passed }}",
              rightValue: true,
              operator: { type: 'boolean', operation: 'equals' }
            }
          ],
          combinator: 'and'
        }
      },
      name: 'Условие: Тест-кейсы подтверждены?',
      type: 'n8n-nodes-base.if',
      typeVersion: 2,
      position: [4440, 260]
    },

    // Контроль 1: Ветка отклонения
    jira('Jira: Сообщение об отклонении тестов', 'POST', issueUrl('/comment'), [4440, 520],
      '={{ JSON.stringify({ body: "h3. ❌ [Этап 5 из 7] [Контроль 1] Тест-кейсы отклонены на доработку" }) }}'),

    // 6. Сохранение в базу тестов Qase & Передача на автоматизацию
    {
      parameters: {
        conditions: {
          options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
          conditions: [
            {
              id: 'cond_new_cases',
              leftValue: "={{ $('Создание тест-кейсов без повторов').first().json.hasNewCases }}",
              rightValue: true,
              operator: { type: 'boolean', operation: 'equals' }
            }
          ],
          combinator: 'and'
        }
      },
      name: 'Условие: Есть новые тесты для добавления?',
      type: 'n8n-nodes-base.if',
      typeVersion: 2,
      position: [4660, 260]
    },
    {
      parameters: {
        method: 'POST',
        url: `https://api.qase.io/v1/case/${qaseCode}/bulk`,
        authentication: 'predefinedCredentialType',
        nodeCredentialType: 'httpHeaderAuth',
        sendBody: true,
        specifyBody: 'json',
        jsonBody: "={{ JSON.stringify({ cases: $('Создание тест-кейсов без повторов').first().json.qaseCases }) }}",
        options: {}
      },
      name: 'Qase: Создать новые тесты в базе',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 4.2,
      position: [4880, 260],
      credentials: qaseCreds
    },
    jira('Jira: Прикрепить ссылку на тесты в Qase', 'POST', issueUrl('/remotelink'), [5100, 260],
      `={{ JSON.stringify({
        globalId: 'qase-project-' + '${qaseCode}' + '-' + ${FILTER}.issueKey,
        application: { type: 'com.qase.tms', name: 'Qase TMS' },
        relationship: 'tested by',
        object: {
          url: 'https://app.qase.io/project/' + '${qaseCode}',
          title: 'Qase TMS: Тест-кейсы задачи ' + ${FILTER}.issueKey,
          summary: 'Пошаговые сценарии тестирования в системе Qase TMS (проект ${qaseCode})',
          icon: { url16x16: 'https://app.qase.io/favicon.ico', title: 'Qase TMS' }
        }
      }) }}`),
    jira('Jira: Поставить метку Готово к разработке', 'PUT', issueUrl(''), [5320, 260],
      '={{ JSON.stringify({ update: { labels: [{ add: "qa-dor-passed" }, { add: "qa-ready-for-autotests" }, { remove: "qa-dor-failed" }] } }) }}'),

    // 7. Создание и внедрение автотестов
    codeNode('Создание файлов автотестов на Python', '11_scaffold_autotests.js', [5540, 260]),
    jira('Jira: Отчет 5 — Код сгенерирован', 'POST', issueUrl('/comment'), [5760, 260],
      '={{ JSON.stringify({ body: "h3. ⏳ [Этап 6 из 7] Автотесты сгенерированы. Ожидание проверки кода (Gate 2)..." }) }}'),
    codeNode('Контроль 2: Проверка качества кода тестов', '12_gate2_review_autotests.js', [5980, 260]),
    jira('Jira: Карточка проверки кода (Gate 2)', 'POST', issueUrl('/comment'), [6200, 260],
      "={{ JSON.stringify({ body: $('Контроль 2: Проверка качества кода тестов').first().json.autotestCommentBody }) }}"),
    {
      parameters: {
        conditions: {
          options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
          conditions: [
            {
              id: 'cond_gate2_passed',
              leftValue: "={{ $('Контроль 2: Проверка качества кода тестов').first().json.gate2.passed }}",
              rightValue: true,
              operator: { type: 'boolean', operation: 'equals' }
            }
          ],
          combinator: 'and'
        }
      },
      name: 'Условие: Код тестов подтвержден?',
      type: 'n8n-nodes-base.if',
      typeVersion: 2,
      position: [6420, 260]
    },
    jira('Jira: Отказ по качеству кода', 'POST', issueUrl('/comment'), [6420, 520],
      '={{ JSON.stringify({ body: "h3. ❌ [Этап 6 из 7] Код автотестов отклонен (Gate 2)." }) }}'),

    codeNode('Перенос автотестов в рабочий проект', '13_promote_autotests.js', [6640, 260]),
    jira('Jira: Финальный отчет о внедрении автотестов', 'POST', issueUrl('/comment'), [6860, 260],
      "={{ JSON.stringify({ body: $('Перенос автотестов в рабочий проект').first().json.finalReportCommentBody }) }}"),
    
    // Нода для записи сгенерированных файлов на диск (использует fs)
    codeNode('Сохранение файлов на диск', '14_write_files.js', [7080, 260]),

    // =========================================================================
    // 8. ПРИЕМ ОТЧЕТОВ ИЗ GITHUB ACTIONS (ОЖИДАНИЕ)
    // =========================================================================
    {
      parameters: {
        resume: 'webhook',
        webhookSuffix: 'github-actions-report',
        options: {}
      },
      name: 'Wait: Ожидание результатов GitHub Actions',
      type: 'n8n-nodes-base.wait',
      typeVersion: 1,
      position: [7300, 260],
      webhookId: crypto.randomUUID()
    },
    {
      parameters: {
        keepOnlySet: false,
        values: {
          string: [
            { name: 'issueKey', value: '={{ $json.body.issueKey }}' },
            { name: 'status', value: '={{ $json.body.status }}' },
            { name: 'runUrl', value: '={{ $json.body.runUrl }}' },
            { name: 'allureSummary', value: '={{ $json.body.allureSummary }}' }
          ]
        },
        options: {}
      },
      name: 'Парсинг отчета Allure',
      type: 'n8n-nodes-base.set',
      typeVersion: 1,
      position: [7520, 260]
    },
    {
      parameters: {
        resource: 'issue',
        operation: 'addComment',
        issueIdOrKey: '={{ $json.issueKey }}',
        body: `={{
          "h2. 📊 [Этап 8 из 8] Отчет о прохождении автотестов (GitHub Actions)\\n\\n" +
          "*Статус:* " + ($json.status === "success" ? "(/) УСПЕШНО" : "(x) ОШИБКА") + "\\n" +
          "*Сводка Allure:* " + $json.allureSummary + "\\n\\n" +
          "[🔗 Посмотреть полный лог в GitHub|" + $json.runUrl + "]"
        }}`
      },
      name: 'Jira: Опубликовать отчет Allure',
      type: 'n8n-nodes-base.jira',
      typeVersion: 1,
      position: [7740, 260],
      credentials: { jiraSoftwareCloudApi: { id: process.env.N8N_JIRA_CRED_ID || 'xnrgpIhThDJMtfMb', name: 'Jira Cloud (romeo-timony)' } }
    }
  ]

  const link = (...targets) => ({ main: targets.map(t => (t ? [].concat(t).map(node => ({ node, type: 'main', index: 0 })) : [])) })
  const connections = {
    'Jira: Перехват обновления задачи': link('Фильтр: Задача взята в работу'),
    'Execute Workflow Trigger': link('Фильтр: Задача взята в работу'),
    'Фильтр: Задача взята в работу': link('Jira: Загрузить данные задачи'),
    'Jira: Загрузить данные задачи': link('Jira: Загрузить ссылки задачи'),
    'Jira: Загрузить ссылки задачи': link('Правила проверки готовности задачи'),
    'Правила проверки готовности задачи': link('Подготовка задачи к проверке'),
    'Подготовка задачи к проверке': link('Проверка задачи на готовность'),
    'Проверка задачи на готовность': link('Условие: Требования задачи понятны?'),

    'Условие: Требования задачи понятны?': link(
      'Jira: Отчет 1 — Задача готова к работе (DoR Gate)',
      'Jira: Отправить замечания к задаче'
    ),
    'Jira: Отправить замечания к задаче': link('Jira: Вернуть задачу на доработку'),
    'Jira: Вернуть задачу на доработку': link('Jira: Поставить метку Требует доработки'),

    'Jira: Отчет 1 — Задача готова к работе (DoR Gate)': link('Подготовка данных для чек-листа'),
    'Подготовка данных для чек-листа': link('Создание карты проверок'),
    'Создание карты проверок': link('Jira: Отчет 2 — Интеллект-карта проверок'),
    'Jira: Отчет 2 — Интеллект-карта проверок': link('Подготовка данных для тест-кейсов'),
    'Подготовка данных для тест-кейсов': link('Qase: Загрузить список папок'),
    'Qase: Загрузить список папок': link('Qase: Загрузить существующие тесты'),
    'Qase: Загрузить существующие тесты': link('Создание тест-кейсов без повторов'),
    'Создание тест-кейсов без повторов': link('Jira: Отчет 3 — Реестр тест-кейсов (BDD)'),
    'Jira: Отчет 3 — Реестр тест-кейсов (BDD)': link('Jira: Отчет 4 — Матрица трассируемости (RTM)'),
    'Jira: Отчет 4 — Матрица трассируемости (RTM)': link('Контроль 1: Подтверждение тест-кейсов'),
    'Контроль 1: Подтверждение тест-кейсов': link('Jira: Карточка подтверждения тестов (Gate 1)'),
    'Jira: Карточка подтверждения тестов (Gate 1)': link('Условие: Тест-кейсы подтверждены?'),

    'Условие: Тест-кейсы подтверждены?': link(
      'Условие: Есть новые тесты для добавления?',
      'Jira: Сообщение об отклонении тестов'
    ),
    'Условие: Есть новые тесты для добавления?': link(
      'Qase: Создать новые тесты в базе',
      'Jira: Прикрепить ссылку на тесты в Qase'
    ),
    'Qase: Создать новые тесты в базе': link('Jira: Прикрепить ссылку на тесты в Qase'),
    'Jira: Прикрепить ссылку на тесты в Qase': link('Jira: Поставить метку Готово к разработке'),
    
    // Новые связи для автотестов
    'Jira: Поставить метку Готово к разработке': link('Создание файлов автотестов на Python'),
    'Создание файлов автотестов на Python': link('Jira: Отчет 5 — Код сгенерирован'),
    'Jira: Отчет 5 — Код сгенерирован': link('Контроль 2: Проверка качества кода тестов'),
    'Контроль 2: Проверка качества кода тестов': link('Jira: Карточка проверки кода (Gate 2)'),
    'Jira: Карточка проверки кода (Gate 2)': link('Условие: Код тестов подтвержден?'),
    
    'Условие: Код тестов подтвержден?': link(
      'Перенос автотестов в рабочий проект',
      'Jira: Отказ по качеству кода'
    ),
    
    'Перенос автотестов в рабочий проект': link('Jira: Финальный отчет о внедрении автотестов'),
    'Jira: Финальный отчет о внедрении автотестов': link('Сохранение файлов на диск'),
    
    // Подключения цепочки GitHub Actions
    'Сохранение файлов на диск': link('Wait: Ожидание результатов GitHub Actions'),
    'Wait: Ожидание результатов GitHub Actions': link('Парсинг отчета Allure'),
    'Парсинг отчета Allure': link('Jira: Опубликовать отчет Allure')
  }

  return { name: WORKFLOW_NAME, nodes, connections, settings: { executionOrder: 'v1', saveDataSuccessExecution: 'all' } }
}

module.exports = { buildWorkflow, WEBHOOK_PATH, WORKFLOW_NAME }
