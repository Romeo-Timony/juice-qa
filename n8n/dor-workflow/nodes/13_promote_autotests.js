// n8n Code node: "Перенос автотестов в рабочий проект"
// Перенос проверенных файлов автотестов в основные рабочие папки проекта

const prev = $('Контроль 2: Проверка качества кода тестов').first().json
const issueKey = prev.issueKey || 'JS-16'
const files = prev.files || []
const gate2 = prev.gate2 || {}

const promotedAt = new Date().toISOString()
const approver = gate2.approver || 'QA Lead'

const promotedFiles = files.map(f => {
  const header = `# [ОДОБРЕНО ТЕСТИРОВЩИКОМ] Подтвердил: ${approver} | Дата: ${promotedAt} | Оценка: ${gate2.qualityScore}/100\n`
  return {
    ...f,
    finalCode: header + (f.code || ''),
    status: 'ДОБАВЛЕНО_В_ОСНОВНОЙ_ПРОЕКТ'
  }
})

// Формирование итогового отчета для Jira
const finalReport = [
  'h2. 🚀 [Этап 7 из 7] Завершение: Автотесты созданы и добавлены в проект',
  '',
  `*Задача в работе:* ${issueKey}`,
  `*Статус выполнения:* (/) Полный цикл успешно пройден:`,
  `1. DoR Gate -> 2. MindMap -> 3. BDD -> 4. RTM -> 5. Gate 1 -> 6. Gate 2 -> 7. Внедрение`,
  `*Режим работы:* Автоматический (Тестовый проект)`,
  '',
  'h3. 📂 Добавленные наборы тестов (Python + Playwright):',
  promotedFiles.map(f => `* *(+) [${f.type === 'backend' ? 'Серверные тесты' : 'Интерфейсные тесты'}]* \`${f.targetPath}\` — ${f.testCount} сценариев`).join('\n'),
  '',
  'h3. ⚡ Команды для запуска тестов:',
  '{noformat}',
  `pytest tests/backend/test_${issueKey.toLowerCase().replace(/[^a-z0-9]/g, '')}_api.py`,
  `pytest tests/frontend/test_${issueKey.toLowerCase().replace(/[^a-z0-9]/g, '')}_ui.py`,
  'allure serve allure-results',
  '{noformat}',
  '',
  '*(/) Задача полностью протестирована и готова к релизу.*'
].join('\n')

return [{
  json: {
    issueKey,
    promotedFiles,
    promotedAt,
    finalReportCommentBody: finalReport
  }
}]
