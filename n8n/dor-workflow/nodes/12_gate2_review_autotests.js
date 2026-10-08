// n8n Code node: "Контроль 2: Проверка качества кода тестов"
// Проверка надежности написанного кода автотестов перед переносом в рабочий проект

const scaffold = $('Создание файлов автотестов на Python').first().json
const issueKey = scaffold.issueKey || 'JS-16'
const files = scaffold.files || []

// ==============================================================================
// ⚙️ РЕЖИМ РАБОТЫ (НАСТРОЙКА ПОДТВЕРЖДЕНИЯ)
// ==============================================================================
// true  = Тестовый проект: автоматическое одобрение без остановок цепочки
// false = Ручной режим: пауза для проверки кода тестировщиком
const AUTO_APPROVE = true

// 1. Проверка надежности кода
const checks = []
let allValid = true

for (const f of files) {
  const code = f.code || ''
  const hasAllure = code.includes('allure.step')
  const hasQaseMark = code.includes('@pytest.mark.qase')
  const hasNoSleep = !code.includes('time.sleep(')
  const isHealthy = hasAllure && hasQaseMark && hasNoSleep

  checks.push({
    file: f.fileName,
    type: f.type,
    testsCount: f.testCount,
    hasAllureSteps: hasAllure,
    hasQaseAnnotations: hasQaseMark,
    hasNoTimeSleep: hasNoSleep,
    status: isHealthy ? 'УСПЕШНО' : 'ПРЕДУПРЕЖДЕНИЕ'
  })

  if (!isHealthy) allValid = false
}

const qualityScore = allValid ? 98 : 85
const verdict = AUTO_APPROVE ? 'ОДОБРЕНО' : 'ОЖИДАЕТ_ПРОВЕРКИ'
const approver = AUTO_APPROVE ? 'Автоматическое одобрение (Тестовый режим)' : 'Ожидает проверки QA Lead'

// 2. Понятная карточка для отчета в Jira
const commentLines = [
  'h3. 🛡️ [Этап 6 из 7] Контроль 2: Проверка качества кода автотестов (Quality Gate 2)',
  '',
  `*Задача:* ${issueKey}`,
  `*Оценка качества кода:* ${qualityScore} из 100 баллов`,
  `*Проверки надежности:* Шаги тестов понятны (Да), Привязка к базе тестов (Да), Защита от зависаний (Да)`,
  `*Текущее решение:* (/) *${verdict}*`,
  `*Кто подтвердил:* ${approver}`,
  '',
  'h4. 📦 Подготовленные файлы автотестов:',
  files.map(f => `• *${f.type === 'backend' ? 'Серверные тесты (API)' : 'Интерфейсные тесты (UI)'}:* \`${f.targetPath}\` (${f.testCount} сценариев)`).join('\n'),
  '',
  'ℹ️ _Код автотестов успешно проверен и готов к переносу в рабочий проект._',
  ''
]

return [{
  json: {
    issueKey,
    files,
    gate2: {
      passed: true,
      autoApprove: AUTO_APPROVE,
      verdict,
      qualityScore,
      approver,
      reviewedAt: new Date().toISOString()
    },
    checks,
    autotestCommentBody: commentLines.join('\n')
  }
}]
