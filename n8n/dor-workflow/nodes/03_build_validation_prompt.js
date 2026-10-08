// n8n Code node: "Подготовка задачи к проверке"
const ev = $('Фильтр: Задача взята в работу').first().json
const issue = $('Jira: Загрузить данные задачи').first().json
const remoteLinks = $('Jira: Загрузить ссылки задачи').all().map(i => i.json).filter(l => l && l.object)
const { standard } = $('Правила проверки готовности задачи').first().json

const f = issue.fields || {}
const summary = f.summary || ''
const description = String(f.description || '').trim()
const issueType = (f.issuetype || {}).name || 'Unknown'
const isSubtask = Boolean((f.issuetype || {}).subtask)

function classify () {
  if (isSubtask) {
    if (/^\s*\[\s*front/i.test(summary)) return 'frontend'
    if (/^\s*\[\s*back/i.test(summary)) return 'backend'
    const text = (summary + ' ' + description).toLowerCase()
    const fe = (text.match(/angular|frontend|компонент|экран|форм[аы]|ui\b|верстк/g) || []).length
    const be = (text.match(/backend|endpoint|эндпоинт|rest api|sequelize|модел[ьи]|express|контроллер/g) || []).length
    if (fe || be) return fe >= be ? 'frontend' : 'backend'
    return 'generic'
  }
  if (/story|истори/i.test(issueType)) return 'story'
  if (/task|задач/i.test(issueType)) return 'task'
  return 'generic'
}

const kind = classify()
const profile = standard.profiles[kind]
const criteria = [...standard.common, ...profile.criteria]

const lower = description.toLowerCase()
const remoteUrls = remoteLinks.map(l => l.object.url || '')
const autoChecks = {
  descriptionLength: description.length,
  hasDescription: description.length >= standard.thresholds.minDescriptionLength,
  summaryLength: summary.length,
  hasConfluenceLink: /atlassian\.net\/wiki|confluence/i.test(description) || remoteUrls.some(u => /\/wiki\//i.test(u)),
  hasParentOrStory: Boolean(f.parent) || (f.issuelinks || []).length > 0 || /\b[A-Z]+-\d+\b/.test(description),
  hasAcceptanceCriteria: /критери\S*\s+приемки|acceptance criteria|\bdod\b|definition of done|\[\s*x?\s*\]|given|дано/i.test(description),
  vagueWordsFound: standard.vagueWords.filter(w => {
    const escaped = w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const re = new RegExp('(?:^|[^а-яёa-z0-9])' + escaped + '(?:[^а-яёa-z0-9]|$)', 'i')
    return re.test(description)
  })
}

const context = {
  key: ev.issueKey,
  type: issueType,
  profile: profile.label,
  summary,
  parent: f.parent ? `${f.parent.key}: ${(f.parent.fields || {}).summary || ''}` : null,
  links: (f.issuelinks || []).map(l => {
    const other = l.outwardIssue || l.inwardIssue || {}
    return `${l.type ? l.type.name : 'link'} -> ${other.key || ''} ${(other.fields || {}).summary || ''}`
  }),
  remoteLinks: remoteLinks.map(l => `${l.object.title || ''} ${l.object.url || ''}`.trim()),
  labels: f.labels || [],
  priority: (f.priority || {}).name || null
}

const systemPrompt = [
  'Ты — Senior QA Engineer и эксперт по бизнес-анализу (BABOK, IEEE 29148, INVEST, ISTQB).',
  'Твоя задача — строго и объективно проверить требования Jira-задачи на соответствие эталону QA Definition of Ready.',
  'Правила оценки:',
  '- status = "pass": критерий выполнен (все ключевые требования присутствуют и проверяемы; минорные уточнения оформляются в discrepancies с severity="minor" и questions, не блокируя оценку "pass").',
  '- status = "partial": в критерии есть существенные пробелы, отсутствие обязательных данных или серьезные неточности.',
  '- status = "fail": критерий не выполнен или информация полностью отсутствует.',
  '- Не додумывай требования за аналитика: если информации нет в тексте задачи или связанных данных — это fail.',
  '- В evidence приводи короткую цитату из задачи, подтверждающую оценку (или "нет данных").',
  '- В comment объясняй конкретно, чего не хватает, со ссылкой на элементы задачи.',
  '- discrepancies: только конкретные, проверяемые несоответствия с ожидаемым результатом (что именно добавить/исправить).',
  '- questions: открытые вопросы к аналитику, без ответа на которые нельзя начать тестирование.',
  'Отвечай строго на русском языке и строго в JSON по заданной схеме.'
].join('\n')

const userPrompt = [
  `ЭТАЛОН: ${standard.name} v${standard.version}. Профиль задачи: ${profile.label}.`,
  'КРИТЕРИИ (оцени КАЖДЫЙ, используя его id):',
  ...criteria.map(c => `- ${c.id} [${c.mandatory ? 'ОБЯЗАТЕЛЬНЫЙ' : 'рекомендуемый'}] ${c.title}: ${c.rule}`),
  '',
  'АВТОМАТИЧЕСКИЕ ПРОВЕРКИ (факты, учитывай их):',
  JSON.stringify(autoChecks, null, 2),
  '',
  'КОНТЕКСТ ЗАДАЧИ:',
  JSON.stringify(context, null, 2),
  '',
  'ОПИСАНИЕ ЗАДАЧИ (Jira wiki markup):',
  '"""',
  description || '(описание отсутствует)',
  '"""'
].join('\n')

const responseSchema = {
  type: 'OBJECT',
  properties: {
    criteria: {
      type: 'ARRAY',
      items: {
        type: 'OBJECT',
        properties: {
          id: { type: 'STRING' },
          status: { type: 'STRING', enum: ['pass', 'partial', 'fail'] },
          evidence: { type: 'STRING' },
          comment: { type: 'STRING' }
        },
        required: ['id', 'status', 'comment']
      }
    },
    discrepancies: {
      type: 'ARRAY',
      items: {
        type: 'OBJECT',
        properties: {
          criterionId: { type: 'STRING' },
          severity: { type: 'STRING', enum: ['blocker', 'major', 'minor'] },
          problem: { type: 'STRING' },
          expectation: { type: 'STRING' }
        },
        required: ['criterionId', 'severity', 'problem', 'expectation']
      }
    },
    questions: { type: 'ARRAY', items: { type: 'STRING' } },
    strengths: { type: 'ARRAY', items: { type: 'STRING' } },
    summary: { type: 'STRING' }
  },
  required: ['criteria', 'discrepancies', 'questions', 'summary']
}

return [{
  json: {
    issueKey: ev.issueKey,
    kind,
    summary,
    description,
    context,
    profileLabel: profile.label,
    criteria,
    autoChecks,
    reporter: f.reporter ? { accountId: f.reporter.accountId, name: f.reporter.displayName } : null,
    geminiRequest: {
      systemInstruction: { parts: [{ text: systemPrompt }] },
      contents: [{ role: 'user', parts: [{ text: userPrompt }] }],
      generationConfig: {
        temperature: 0.1,
        maxOutputTokens: 16384,
        responseMimeType: 'application/json',
        responseSchema
      }
    }
  }
}]
