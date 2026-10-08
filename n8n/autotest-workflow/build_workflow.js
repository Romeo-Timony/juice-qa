const fs = require('fs')
const path = require('path')

const webhookUrl = '/webhook/github-actions-report'

const workflow = {
  name: 'n8n: Получение отчетов Allure из GitHub Actions',
  nodes: [
    {
      parameters: {
        httpMethod: 'POST',
        path: 'github-actions-report',
        responseMode: 'onReceived',
        options: {}
      },
      name: 'Webhook: Прием отчета из GitHub Actions',
      type: 'n8n-nodes-base.webhook',
      typeVersion: 1,
      position: [250, 300],
      webhookId: 'github-actions-allure-report'
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
      position: [450, 300]
    },
    {
      parameters: {
        resource: 'issue',
        operation: 'addComment',
        issueIdOrKey: '={{ $json.issueKey }}',
        body: `={{
          "h2. 📊 Отчет о прохождении автотестов (GitHub Actions)\\n\\n" +
          "*Статус:* " + ($json.status === "success" ? "(/) УСПЕШНО" : "(x) ОШИБКА") + "\\n" +
          "*Сводка Allure:* " + $json.allureSummary + "\\n\\n" +
          "[🔗 Посмотреть полный лог в GitHub|" + $json.runUrl + "]"
        }}`
      },
      name: 'Jira: Опубликовать отчет',
      type: 'n8n-nodes-base.jira',
      typeVersion: 1,
      position: [650, 300],
      credentials: {
        jiraSoftwareCloudApi: {
          id: process.env.N8N_JIRA_CRED_ID || 'xnrgpIhThDJMtfMb',
          name: 'Jira Cloud (romeo-timony)'
        }
      }
    }
  ],
  connections: {
    'Webhook: Прием отчета из GitHub Actions': {
      main: [
        [
          { node: 'Парсинг отчета Allure', type: 'main', index: 0 }
        ]
      ]
    },
    'Парсинг отчета Allure': {
      main: [
        [
          { node: 'Jira: Опубликовать отчет', type: 'main', index: 0 }
        ]
      ]
    }
  },
  settings: {
    executionOrder: 'v1'
  }
}

fs.writeFileSync(path.join(__dirname, 'autotest_workflow.json'), JSON.stringify(workflow, null, 2))
console.log('autotest_workflow.json successfully created!')
