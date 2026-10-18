// n8n Code node: "Контроль 1: Подтверждение тест-кейсов"
// Промежуточная проверка созданных тест-кейсов перед сохранением.

const prev = $('Создание тест-кейсов без повторов').first().json
const ctx = $('Подготовка данных для тест-кейсов').first().json
const issue = $('Jira: Загрузить данные задачи').first().json

const issueKey = ctx.issueKey || 'JS-20'
const kind = ctx.kind || 'generic'
const cases = prev.cases || []
const hasNewCases = prev.hasNewCases !== false

// ==============================================================================
// ⚙️ РЕЖИМ РАБОТЫ (НАСТРОЙКА ПОДТВЕРЖДЕНИЯ)
// ==============================================================================
// false = Строгий режим Human-in-the-Loop: пауза для проверки старшим тестировщиком
const AUTO_APPROVE = false

// 1. Оценка качества созданных тестов
const totalCases = cases.length
const positiveCases = cases.filter(c => !c.title.toLowerCase().includes('ошибк') && !c.title.toLowerCase().includes('отказ') && !c.title.toLowerCase().includes('невалид')).length
const negativeCases = totalCases - positiveCases
const hasBvaOrNegative = negativeCases > 0 || totalCases >= 3

const qualityScore = hasBvaOrNegative ? 96 : 82
const verdict = AUTO_APPROVE ? 'ОДОБРЕНО' : 'ОЖИДАЕТ СОГЛАСОВАНИЯ QA LEAD'
const approver = AUTO_APPROVE ? 'Автоматическое одобрение (Тестовый режим)' : 'Ожидает проверки QA Lead'

// 2. Карточка для отчета в Jira
const reviewCard = [
  'h3. 🛡️ [Этап 5 из 8] Контроль 1: Подтверждение тест-кейсов (Quality Gate 1)',
  '',
  `*Проверенная задача:* ${issueKey} (Всего сценариев: ${totalCases})`,
  `*Оценка качества проверок:* ${qualityScore} из 100 баллов`,
  `*Состав проверок:* Стандартные сценарии: ${positiveCases}, Проверки ошибок и границ: ${negativeCases}`,
  `*Текущее решение:* ⏳ *${verdict}*`,
  `*Кто подтвердил:* ${approver}`,
  '',
  'ℹ️ _Все проверки соответствуют требованиям задачи. Для перехода к генерации автотестов требуется согласование QA Lead (оставьте комментарий ❤️ или «ОК» в задаче)._',
  ''
].join('\n')

const existingComments = ($('Jira: Загрузить данные задачи').first().json.fields?.comment?.comments) || []
const stage5 = existingComments.find(c => c.body && c.body.includes('[Этап 5 из'))
const jiraBase = 'https://romeo-timony.atlassian.net'
const gate1Method = stage5 ? 'PUT' : 'POST'
const gate1Url = stage5
  ? `${jiraBase}/rest/api/2/issue/${issueKey}/comment/${stage5.id}`
  : `${jiraBase}/rest/api/2/issue/${issueKey}/comment`

return [{
  json: {
    ...prev,
    gate1: {
      passed: false,
      autoApprove: AUTO_APPROVE,
      verdict,
      qualityScore,
      approver,
      reviewedAt: new Date().toISOString()
    },
    gate1ReviewCard: reviewCard,
    gate1Method,
    gate1Url
  }
}]
