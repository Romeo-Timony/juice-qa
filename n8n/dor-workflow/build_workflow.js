const fs = require('fs')
const path = require('path')
const crypto = require('crypto')

const NODES_DIR = path.join(__dirname, 'nodes')
const WEBHOOK_PATH = 'jira-dor-gate'
const WORKFLOW_NAME = 'Juice Shop'

const code = file => fs.readFileSync(path.join(NODES_DIR, file), 'utf8')

function buildWorkflow ({ jiraCred, geminiCred, qaseCred, webhookToken, geminiModel, qaseCode = 'JS', qaseToken = '' }) {
  const jiraCreds = { jiraSoftwareCloudApi: jiraCred }
  const qaseCreds = { httpHeaderAuth: qaseCred }
  const FILTER = "$('Фильтр: Задача взята в работу').item.json"
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

  const jiraDynamic = (name, position, methodExp, urlExp, bodyExp) => ({
    parameters: {
      method: methodExp,
      url: urlExp,
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'jiraSoftwareCloudApi',
      sendBody: true,
      specifyBody: 'json',
      jsonBody: bodyExp,
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
  const casesReportBody = "={{ JSON.stringify({ body: $('Создание тест-кейсов без повторов').item.json.casesReport }) }}"
  const rtmCommentBody = "={{ JSON.stringify({ body: $('Создание тест-кейсов без повторов').item.json.rtmCommentBody }) }}"
  const gate1CardBody = "={{ JSON.stringify({ body: $('Контроль 1: Подтверждение тест-кейсов').item.json.gate1ReviewCard }) }}"

  const nodes = [
    // =========================================================================
    // 📌 НАГЛЯДНЫЕ СТИКЕРЫ (ОПИСАНИЕ ЭТАПОВ)
    // =========================================================================
    stickyNote(
      'Стикер: Приём задач',
      `## 📥 1. Приём задач из Jira
**Что здесь происходит:**
Система отслеживает задачи, переведенные в статус «В работе».
* Мгновенный запуск по вебхуку Jira при смене статуса.`,
      [-260, 40], 430, 420, 6
    ),

    stickyNote(
      'Стикер: Проверка готовности (DoR)',
      `## 📋 2. Проверка готовности задачи (DoR) [Этап 1 из 8]
**Что здесь происходит:**
Проверяем, достаточно ли информации в задаче для начала работы.
* Загружаем описание, критерии приёмки и ссылки из Jira.
* Сверяем с 16 обязательными критериями (DoR).
* Публикуем **[Этап 1 из 8] QA-валидация требований (DoR Gate)**.
* При нехватке требований возвращаем задачу в «К выполнению».`,
      [190, 40], 1750, 420, 1
    ),

    stickyNote(
      'Стикер: Возврат задачи',
      `## ❌ 3. Возврат задачи при неполных требованиях
**Что здесь происходит:**
Защита команды от работы с неполными требованиями.
* Детальный комментарий с таблицей блокеров и рекомендаций.
* Возврат в «К выполнению» (Transition ID: 11), метка \`qa-dor-failed\`.`,
      [1750, 470], 640, 260, 5
    ),

    stickyNote(
      'Стикер: Интеллект-карта проверок',
      `## 🧠 4. Интеллект-карта проверок [Этап 2 из 8]
**Что здесь происходит:**
Проектирование многоуровневого дерева проверок.
* Публикует **[Этап 2 из 8] Интеллект-карта проверок (QA MindMap)** в Jira.`,
      [1970, 40], 640, 420, 4
    ),

    stickyNote(
      'Стикер: Тест-кейсы и RTM',
      `## 🧪 5. Реестр тест-кейсов & Матрица RTM [Этапы 3 и 4 из 8]
**Что здесь происходит:**
* Публикует **[Этап 3 из 8] Реестр тест-кейсов (BDD)**.
* Публикует **[Этап 4 из 8] Матрица трассируемости (RTM)**.
* Фиксирует кейсы в Qase TMS и прикрепляет ссылку.`,
      [2630, 40], 1300, 420, 4
    ),

    stickyNote(
      'Стикер: Контроль 1',
      `## 🛡️ 6. Контроль 1: Подтверждение тест-кейсов [Этап 5 из 8]
**Что здесь происходит:**
* Публикует **[Этап 5 из 8] Контроль 1 (Quality Gate 1)** со статусом ⏳ ОЖИДАЕТ СОГЛАСОВАНИЯ QA LEAD.
* **Строгий Human-in-the-Loop:** Пайплайн останавливается и ждет одобрения QA Lead в Jira!`,
      [3950, 40], 640, 420, 7
    ),

    stickyNote(
      'Стикер: GitHub Actions Результаты',
      `## 🐙 7. Результаты прогона в GitHub Actions [Этап 8 из 8]
**Что здесь происходит:**
Прием отчета о результатах выполнения автотестов в CI/CD (GitHub).
* Публикует итоговый вердикт с результатами тестов и ссылкой на Allure.`,
      [4700, 40], 700, 420, 6
    ),

    // =========================================================================
    // ⚙️ УЗЛЫ ПАЙПЛАЙНА
    // =========================================================================

    // 0. Прием событий Qase (Удаление тестов)
    {
      parameters: { httpMethod: 'POST', path: 'qase-events', responseMode: 'onReceived', options: {} },
      name: 'Webhook: События Qase TMS',
      type: 'n8n-nodes-base.webhook',
      typeVersion: 2,
      position: [0, 80],
      webhookId: crypto.randomUUID()
    },
    {
      parameters: {
        jsCode: `
          try {
            const cp = require('child_process');
            cp.execSync('python scripts/qase_lifecycle_sync.py --drift', { cwd: 'C:/Yandex.Disk/Рабочий стол/Juice_shop/qa-automation' });
          } catch(e) {}
          return [{ json: { success: true } }];
        `
      },
      name: 'Синхронизация удаленных тестов (Drift)',
      type: 'n8n-nodes-base.code',
      typeVersion: 2,
      position: [240, 80]
    },

    // 1. Приём задач из Jira
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
    jira('Jira: Загрузить данные задачи', 'GET', issueUrl('?fields=summary,description,issuetype,parent,labels,priority,issuelinks,subtasks,reporter,assignee,status,comment'), [460, 260]),
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

    // 3. Ветка возврата (Fail Path / Paused)
    jiraDynamic('Jira: Отправить замечания к задаче', [1800, 520],
      '={{ $json.commentMethod || "POST" }}',
      '={{ $json.commentUrl }}',
      commentBody),
    {
      parameters: {
        conditions: {
          options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
          conditions: [
            {
              id: 'cond_paused',
              leftValue: "={{ $('Проверка задачи на готовность').item.json.targetLabel }}",
              rightValue: 'qa-paused',
              operator: { type: 'string', operation: 'equals' }
            }
          ],
          combinator: 'and'
        }
      },
      name: 'Условие: Пауза из-за контракта или возврат?',
      type: 'n8n-nodes-base.if',
      typeVersion: 2,
      position: [2020, 520]
    },
    jira('Jira: Поставить метку qa-paused', 'PUT', issueUrl(''), [2240, 420],
      '={{ JSON.stringify({ update: { labels: [{ add: "qa-paused" }, { remove: "qa-dor-passed" }] } }) }}'),
    jira('Jira: Вернуть задачу на доработку', 'POST', issueUrl('/transitions'), [2240, 620],
      '={{ JSON.stringify({ transition: { id: "11" } }) }}'),
    jira('Jira: Поставить метку Требует доработки', 'PUT', issueUrl(''), [2460, 620],
      '={{ JSON.stringify({ update: { labels: [{ add: "qa-dor-failed" }, { remove: "qa-dor-passed" }] } }) }}'),

    // 4. Ветка создания проверок (Pass Path)
    jiraDynamic('Jira: Отчет 1 — Задача готова к работе (DoR Gate)', [1800, 260],
      '={{ $json.commentMethod || "POST" }}',
      '={{ $json.commentUrl }}',
      commentBody),
    codeNode('Подготовка данных для чек-листа', '05_build_checklist_prompt.js', [2020, 260]),
    codeNode('Создание карты проверок', '06_format_checklist.js', [2240, 260]),
    jiraDynamic('Jira: Отчет 2 — Интеллект-карта проверок', [2460, 260],
      '={{ $json.commentMethod || "POST" }}',
      '={{ $json.commentUrl }}',
      commentBody),
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
    codeNode('Создание тест-кейсов без повторов', '08_format_testcases.js', [3340, 260], {
      __QASE_TOKEN__: qaseToken,
      __QASE_CODE__: qaseCode
    }),
    jiraDynamic('Jira: Отчет 3 — Реестр тест-кейсов (BDD)', [3560, 260],
      '={{ $(\'Создание тест-кейсов без повторов\').item.json.casesMethod || "POST" }}',
      '={{ $(\'Создание тест-кейсов без повторов\').item.json.casesUrl }}',
      casesReportBody),
    jiraDynamic('Jira: Отчет 4 — Матрица трассируемости (RTM)', [3780, 260],
      '={{ $(\'Создание тест-кейсов без повторов\').item.json.rtmMethod || "POST" }}',
      '={{ $(\'Создание тест-кейсов без повторов\').item.json.rtmUrl }}',
      rtmCommentBody),

    // 5. Сохранение в базу тестов Qase
    {
      parameters: {
        conditions: {
          options: { caseSensitive: true, leftValue: '', typeValidation: 'strict' },
          conditions: [
            {
              id: 'cond_new_cases',
              leftValue: "={{ $('Создание тест-кейсов без повторов').item.json.hasNewCases }}",
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
      position: [4000, 260]
    },
    {
      parameters: {
        method: 'POST',
        url: `https://api.qase.io/v1/case/${qaseCode}/bulk`,
        authentication: 'predefinedCredentialType',
        nodeCredentialType: 'httpHeaderAuth',
        sendBody: true,
        specifyBody: 'json',
        jsonBody: "={{ JSON.stringify({ cases: $('Создание тест-кейсов без повторов').item.json.qaseCases }) }}",
        options: {}
      },
      name: 'Qase: Создать новые тесты в базе',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 4.2,
      position: [4220, 260],
      credentials: qaseCreds
    },
    jira('Jira: Прикрепить ссылку на тесты в Qase', 'POST', issueUrl('/remotelink'), [4440, 260],
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

    // 6. Контроль 1: Подтверждение тест-кейсов (Quality Gate 1 - Остановка для согласования)
    codeNode('Контроль 1: Подтверждение тест-кейсов', '10_gate1_review_testcases.js', [4660, 260]),
    jiraDynamic('Jira: Карточка подтверждения тестов (Gate 1)', [4880, 260],
      '={{ $(\'Контроль 1: Подтверждение тест-кейсов\').item.json.gate1Method || "POST" }}',
      '={{ $(\'Контроль 1: Подтверждение тест-кейсов\').item.json.gate1Url }}',
      gate1CardBody),

    // =========================================================================
    // 7. ПРИЕМ ОТЧЕТОВ ИЗ GITHUB ACTIONS (ЭТАП 8)
    // =========================================================================
    {
      parameters: {
        path: 'github-actions-report',
        httpMethod: 'POST',
        respondWith: 'json',
        responseBody: '{"success": true}',
        options: {}
      },
      name: 'Webhook: Прием отчетов GitHub Actions',
      type: 'n8n-nodes-base.webhook',
      typeVersion: 1,
      position: [5200, 260],
      webhookId: 'github-actions-report'
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
      position: [5420, 260]
    },
    jira('Jira: Опубликовать отчет Allure', 'POST', '={{ "https://romeo-timony.atlassian.net/rest/api/2/issue/" + $json.issueKey + "/comment" }}', [5640, 260],
      `={{ JSON.stringify({ body:
          "h2. 📊 [Этап 8 из 8] Отчет о прохождении автотестов (GitHub Actions)\\n\\n" +
          "*Статус:* " + ($json.status === "success" ? "(/) УСПЕШНО" : "(x) ОШИБКА") + "\\n" +
          "*Сводка Allure:* " + $json.allureSummary + "\\n\\n" +
          "[🔗 Посмотреть полный лог в GitHub|" + $json.runUrl + "]"
      }) }}`)
  ]

  const link = (...targets) => ({ main: targets.map(t => (t ? [].concat(t).map(node => ({ node, type: 'main', index: 0 })) : [])) })
  const connections = {
    'Webhook: События Qase TMS': link('Синхронизация удаленных тестов (Drift)'),
    
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
    'Jira: Отправить замечания к задаче': link('Условие: Пауза из-за контракта или возврат?'),
    'Условие: Пауза из-за контракта или возврат?': link(
      'Jira: Поставить метку qa-paused',
      'Jira: Вернуть задачу на доработку'
    ),
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
    'Jira: Отчет 4 — Матрица трассируемости (RTM)': link('Условие: Есть новые тесты для добавления?'),

    'Условие: Есть новые тесты для добавления?': link(
      'Qase: Создать новые тесты в базе',
      'Jira: Прикрепить ссылку на тесты в Qase'
    ),
    'Qase: Создать новые тесты в базе': link('Jira: Прикрепить ссылку на тесты в Qase'),
    'Jira: Прикрепить ссылку на тесты в Qase': link('Контроль 1: Подтверждение тест-кейсов'),
    'Контроль 1: Подтверждение тест-кейсов': link('Jira: Карточка подтверждения тестов (Gate 1)'),
    
    // Подключения цепочки GitHub Actions
    'Webhook: Прием отчетов GitHub Actions': link('Парсинг отчета Allure'),
    'Парсинг отчета Allure': link('Jira: Опубликовать отчет Allure')
  }

  return { name: WORKFLOW_NAME, nodes, connections, settings: { executionOrder: 'v1', saveDataSuccessExecution: 'all' } }
}

module.exports = { buildWorkflow, WEBHOOK_PATH, WORKFLOW_NAME }
