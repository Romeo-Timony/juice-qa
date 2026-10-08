// n8n Code node: "Подготовка данных для тест-кейсов"
const ctx = $('Подготовка задачи к проверке').first().json
const cl = $('Создание карты проверок').first().json
const issue = $('Jira: Загрузить данные задачи').first().json
const f = issue.fields || {}
const prefix = ctx.kind === 'backend' ? 'BE' : ctx.kind === 'frontend' ? 'FE' : 'QA'
const layer = ctx.kind === 'backend' ? 'api' : 'e2e'

const systemPrompt = [
  'Ты — Senior QA Automation Engineer. Пишешь тест-кейсы по стандарту BDD Gherkin (Given/When/Then) и Allure Steps (@allure.step) для последующей автоматизации и импорта в Qase TMS.',
  'Каждый тест-кейс оформляется как BDD сценарий:',
  '- В description включается полный текст сценария Gherkin с Allure-метаданными (@allure.epic, @allure.feature, @allure.story, @allure.severity).',
  '- Каждый шаг в steps оформляется как атомарный Allure Step с префиксами [Given], [When], [And], [Then].',
  '- Ожидаемый результат должен быть проверяемым (Assertion: статус-код, состояние UI, сообщение).',
  'Отвечай строго на русском языке и строго в JSON.'
].join('\n')

const userPrompt = [
  `Сгенерируй BDD Gherkin и Allure Steps тест-кейсы для ${ctx.profileLabel} ${ctx.issueKey}. Идентификаторы: TC-${prefix}-01, TC-${prefix}-02 ...`,
  'Требования к покрытию: все пункты чек-листа с приоритетом P1 и P2 должны быть покрыты хотя бы одним тест-кейсом (поле covers).',
  'Объем: 10-16 тест-кейсов, 3-7 шагов в каждом. Соотношение позитивных/негативных примерно 50/50, обязательно security-кейсы.',
  `Поле layer по умолчанию: "${layer}".`,
  'Допустимые значения:',
  '- severity: blocker | critical | major | normal | minor | trivial',
  '- priority: high | medium | low',
  '- type: functional | smoke | regression | security | usability | performance | acceptance | compatibility | integration',
  '- layer: e2e | api | unit',
  '- behavior: positive | negative | destructive',
  '- automation: to-be-automated | manual',
  '- regression_tier: fast | full | both',
  '',
  'ПРАВИЛА ТЕГИРОВАНИЯ РЕГРЕССА (КРИТИЧЕСКИ ВАЖНО):',
  '1. "fast-regression" (Быстрый регресс): назначается только для ключевых P1/Blocker/Critical проверок ядра системы (Smoke, основная авторизация, критический happy-path).',
  '2. "full-regression" (Обязательный полный регресс): назначается для ВСЕХ регрессионных тест-кейсов без исключения, включая негативные сценарии, граничные значения (BVA), вторичные проверки и обработку ошибок.',
  'Кейсы быстрого регресса обязаны содержать ОБА тега: ["fast-regression", "full-regression"].',
  'Остальные кейсы содержат тег: ["full-regression"].',
  'В шапке сценария Gherkin обязательно прописывать аннотации @fast-regression и/или @full-regression.',
  '',
  'ПРАВИЛА ПАРАМЕТРА АВТОМАТИЗАЦИИ (automation: "to-be-automated" | "manual") — ПИРАМИДА ТЕСТИРОВАНИЯ:',
  '- Для BACKEND-задач (API): 100% тест-кейсов получают automation = "to-be-automated" (высокая скорость, низкая стоимость поддержки API-тестов).',
  '- Для FRONTEND-задач (UI/E2E): automation = "to-be-automated" назначается ТОЛЬКО критическим сценариям (P1/Blocker Smoke, авторизация, ключевые бизнес-флоу, строгие валидации).',
  '  Вторичные UI-проверки, нативные диалоги загрузки файлов (OS file picker), вспомогательные проверки верстки получают automation = "manual" (минимизация хрупких UI E2E автотестов).',
  '',
  'Формат JSON: {"cases":[{"id":"TC-' + prefix + '-01","title":"[BDD] ...","description":"...","gherkin":"@allure...\\n@fast-regression\\n@full-regression\\nScenario Outline: ...\\n  Given ...\\n  When ...\\n  Then ...","preconditions":"...","postconditions":"...","severity":"critical","priority":"high","type":"functional","layer":"' + layer + '","behavior":"positive","automation":"to-be-automated","regression_tier":"both","tags":["bdd","gherkin","allure","fast-regression","full-regression"],"covers":["CL-..."],"steps":[{"action":"[Given/When/Then] ...","data":"...","expected_result":"..."}]}]}',
  '',
  `ЗАДАЧА: ${f.summary}`,
  'ОПИСАНИЕ:',
  '"""',
  String(f.description || ''),
  '"""',
  '',
  'ЧЕК-ЛИСТ QA:',
  ...(Array.isArray(cl.checklist) ? cl.checklist.map(i => `${i.id} [${i.priority}/${i.type}] ${i.check}`) : ['(структурированный чек-лист проверок)'])
].join('\n')

return [{
  json: {
    issueKey: ctx.issueKey,
    kind: ctx.kind,
    geminiRequest: {
      systemInstruction: { parts: [{ text: systemPrompt }] },
      contents: [{ role: 'user', parts: [{ text: userPrompt }] }],
      generationConfig: { temperature: 0.3, maxOutputTokens: 32768, responseMimeType: 'application/json' }
    }
  }
}]
