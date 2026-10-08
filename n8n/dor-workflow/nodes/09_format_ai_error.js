// n8n Code node: "Format AI error"
const ev = $('Filter: moved to In Progress').first().json
const err = $input.first().json.error || $input.first().json
const message = typeof err === 'string' ? err : (err.message || JSON.stringify(err)).slice(0, 500)

const commentBody = [
  'h2. (!) QA-валидация требований не выполнена',
  `Автоматическая проверка ${ev.issueKey} по эталону QA DoR не завершилась из-за технической ошибки AI-сервиса.`,
  `*Ошибка:* {noformat}${message}{noformat}`,
  'Статус задачи не изменен. Требуется ручная проверка QA или повторный перевод задачи в «В работе».',
  '_n8n QA DoR Gate_'
].join('\n')

return [{ json: { issueKey: ev.issueKey, commentBody } }]
