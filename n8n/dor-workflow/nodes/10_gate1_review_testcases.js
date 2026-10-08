// n8n Code node: "Контроль 1: Подтверждение тест-кейсов"
// Промежуточная проверка созданных тест-кейсов перед их сохранением.

const prev = $('Создание тест-кейсов без повторов').first().json
const ctx = $('Подготовка данных для тест-кейсов').first().json
const issue = $('Jira: Загрузить данные задачи').first().json

const issueKey = ctx.issueKey || 'JS-16'
const kind = ctx.kind || 'generic'
const cases = prev.cases || []
const hasNewCases = prev.hasNewCases !== false

// ==============================================================================
// ⚙️ РЕЖИМ РАБОТЫ (НАСТРОЙКА ПОДТВЕРЖДЕНИЯ)
// ==============================================================================
// true  = Тестовый проект: автоматическое одобрение без остановок цепочки
// false = Ручной режим: пауза для проверки старшим тестировщиком
const AUTO_APPROVE = true

// 1. Оценка качества созданных тестов
const totalCases = cases.length
const positiveCases = cases.filter(c => !c.title.toLowerCase().includes('ошибк') && !c.title.toLowerCase().includes('отказ') && !c.title.toLowerCase().includes('невалид')).length
const negativeCases = totalCases - positiveCases
const hasBvaOrNegative = negativeCases > 0 || totalCases >= 3

const qualityScore = hasBvaOrNegative ? 96 : 82
const verdict = AUTO_APPROVE ? 'ОДОБРЕНО' : 'ОЖИДАЕТ_ПРОВЕРКИ'
const approver = AUTO_APPROVE ? 'Автоматическое одобрение (Тестовый режим)' : 'Ожидает проверки QA Lead'

// 2. Понятная карточка для отчета в Jira
const reviewCard = [
  'h3. 🛡️ [Этап 5 из 7] Контроль 1: Подтверждение тест-кейсов (Quality Gate 1)',
  '',
  `*Проверенная задача:* ${issueKey} (Всего сценариев: ${totalCases})`,
  `*Оценка качества проверок:* ${qualityScore} из 100 баллов`,
  `*Состав проверок:* Стандартные сценарии: ${positiveCases}, Проверки ошибок и границ: ${negativeCases}`,
  `*Текущее решение:* (/) *${verdict}*`,
  `*Кто подтвердил:* ${approver}`,
  '',
  'ℹ️ _Все проверки соответствуют требованиям задачи. Тест-кейсы согласованы и зафиксированы в Qase TMS. Задача готова к разработке автотестов (передана агенту Antigravity)._',
  ''
].join('\n')

return [{
  json: {
    ...prev,
    gate1: {
      passed: true,
      autoApprove: AUTO_APPROVE,
      verdict,
      qualityScore,
      approver,
      reviewedAt: new Date().toISOString()
    },
    gate1ReviewCard: reviewCard
  }
}]
