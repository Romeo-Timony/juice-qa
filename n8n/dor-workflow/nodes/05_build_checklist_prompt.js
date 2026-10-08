// n8n Code node: "Подготовка данных для чек-листа"
const ctx = $('Подготовка задачи к проверке').first().json
let verdict = {}
try { verdict = $('Проверка задачи на готовность').first().json } catch (e) {}
const issue = $('Jira: Загрузить данные задачи').first().json
const { standard } = $('Правила проверки готовности задачи').first().json

const f = issue.fields || {}
const kind = ctx.kind
const prefix = { frontend: 'FE', backend: 'BE', task: 'E2E', story: 'AC', generic: 'QA' }[kind]
const baseline = standard.checklistBaseline[kind] || standard.checklistBaseline.generic
const focus = {
  frontend: 'Чек-лист для FRONTEND-задачи: проверки UI, форм, клиентской логики, интеграции с API со стороны клиента, кроссбраузерности, адаптивности, доступности и клиентской безопасности.',
  backend: 'Чек-лист для BACKEND-задачи: проверки REST API, контрактов, валидации, бизнес-логики, авторизации, БД, безопасности (OWASP API Top 10), производительности и логирования.',
  task: 'Чек-лист для технической задачи: сквозные E2E-проверки интеграции Frontend и Backend.',
  story: 'Чек-лист приемочного тестирования User Story по ее критериям приемки.',
  generic: 'Общий QA чек-лист задачи.'
}[kind]

const systemPrompt = [
  'Ты — Senior QA Engineer (ISTQB Advanced). Составляешь практичный QA чек-лист по лучшим практикам тест-дизайна:',
  'классы эквивалентности, граничные значения, таблицы решений, переходы состояний, позитивные/негативные сценарии, безопасность (OWASP), доступность (WCAG 2.1 AA).',
  'Каждый пункт — одна атомарная проверка, сформулированная как проверяемое утверждение ("Проверить, что ..."), с конкретными значениями из требований.',
  'Не дублируй пункты. Привязывай проверки к конкретным полям, эндпоинтам, компонентам и критериям приемки задачи.',
  'Отвечай строго на русском языке и строго в JSON.'
].join('\n')

const userPrompt = [
  focus,
  `Используй идентификаторы вида CL-${prefix}-01, CL-${prefix}-02 ... (сквозная нумерация).`,
  'Обязательные разделы (можно добавить свои, если требуется задачей):',
  ...baseline.map(b => `- ${b}`),
  '',
  'Приоритеты: P1 — критично (блокирует релиз), P2 — важно, P3 — желательно.',
  'Тип проверки (type): positive | negative | boundary | security | ui | a11y | performance | integration.',
  'Объем: 25-45 пунктов суммарно.',
  '',
  'Формат JSON: {"sections":[{"category":"...","items":[{"id":"CL-' + prefix + '-01","check":"...","priority":"P1","type":"positive"}]}],"risks":["..."],"testData":["..."]}',
  '',
  `ЗАДАЧА ${ctx.issueKey}: ${f.summary}`,
  `Замечания QA-валидации (учти как риски): ${JSON.stringify(verdict.results.filter(r => r.status !== 'pass').map(r => r.id + ': ' + r.comment))}`,
  'ОПИСАНИЕ:',
  '"""',
  String(f.description || ''),
  '"""'
].join('\n')

return [{
  json: {
    issueKey: ctx.issueKey,
    kind,
    prefix,
    geminiRequest: {
      systemInstruction: { parts: [{ text: systemPrompt }] },
      contents: [{ role: 'user', parts: [{ text: userPrompt }] }],
      generationConfig: { temperature: 0.3, maxOutputTokens: 16384, responseMimeType: 'application/json' }
    }
  }
}]
