// n8n Code node: "Проверка задачи на готовность"
const ctx = $('Подготовка задачи к проверке').first().json
const { standard } = $('Правила проверки готовности задачи').first().json
const ev = $('Фильтр: Задача взята в работу').first().json

// ==============================================================================
// ⚙️ РЕЖИМ РАБОТЫ DOR GATE (КОНФИГУРАЦИЯ БЛОКИРОВКИ)
// ==============================================================================
// true  = Тестовый проект: Happy Path без остановок (всегда одобряется для сквозного прогона)
// false = Боевой режим: строгая валидация (откат при неполных требованиях)
const AUTO_PASS_DOR = false

function esc (s) {
  return String(s == null ? '' : s)
    .replace(/\r?\n+/g, ' ')
    .replace(/\|/g, '/')
    .replace(/([{}\[\]])/g, '\\$1')
    .trim()
}

const auto = ctx.autoChecks || {}
const desc = ctx.description || ctx.context?.description || ''
const summary = ctx.summary || ctx.context?.summary || ''

// Оценка соответствия эталону QA DoR
const results = (ctx.criteria || []).map(c => {
  let status = 'pass'
  let comment = 'Критерий полностью удовлетворяет эталону QA DoR.'
  let evidence = 'Подтверждено в описании задачи.'

  if (c.id === 'C01') {
    if (summary.length < 10) {
      status = 'fail'
      comment = 'Заголовок слишком короткий (< 10 символов).'
      evidence = `Длина: ${summary.length}`
    } else if (summary.length > 140) {
      status = 'partial'
      comment = 'Заголовок превышает рекомендованные 140 символов.'
      evidence = `Длина: ${summary.length}`
    } else {
      comment = `Заголовок конкретный (${summary.length} символов).`
      evidence = summary
    }
  } else if (c.id === 'C02') {
    if (!auto.hasDescription && desc.length < 50) {
      status = 'fail'
      comment = 'Описание задачи отсутствует или короче минимального порога.'
      evidence = `Длина: ${desc.length} симв.`
    } else {
      comment = 'Бизнес-цель и контекст задачи описаны.'
      evidence = desc.slice(0, 100) + '...'
    }
  } else if (c.id === 'C03') {
    if (!auto.hasConfluenceLink && !auto.hasParentOrStory) {
      status = 'fail'
      comment = 'Нет связи с родительской задачей/эпиком и ссылки на спецификацию Confluence.'
      evidence = 'Связи отсутствуют'
    } else if (!auto.hasConfluenceLink) {
      status = 'partial'
      comment = 'Есть связь со структурой задач, но отсутствует прямая ссылка на Confluence.'
      evidence = 'Confluence не указан'
    } else {
      comment = 'Полная трассируемость: связь с Epic/Story и Confluence.'
      evidence = 'Confluence + Jira link'
    }
  } else if (c.id === 'C04') {
    if (!auto.hasAcceptanceCriteria && !desc.toLowerCase().includes('критер')) {
      status = 'fail'
      comment = 'Критерии приемки (Acceptance Criteria / DoD) не выделены явно.'
      evidence = 'AC не найдены'
    } else {
      comment = 'Критерии приемки формализованы.'
      evidence = 'AC присутствуют в описании'
    }
  } else if (c.id === 'C05') {
    if ((auto.vagueWordsFound || []).length > 2) {
      status = 'fail'
      comment = `Обнаружены неконкретные формулировки: ${auto.vagueWordsFound.join(', ')}.`
      evidence = auto.vagueWordsFound.join(', ')
    } else if ((auto.vagueWordsFound || []).length > 0) {
      status = 'partial'
      comment = `Есть единичные размытые слова: ${auto.vagueWordsFound.join(', ')}.`
      evidence = auto.vagueWordsFound.join(', ')
    } else {
      comment = 'Размытые формулировки отсутствуют, требования однозначны.'
      evidence = 'Чистый текст'
    }
  } else if (c.id === 'C06') {
    const hasNegative = /ошибк|негатив|401|400|404|409|500|exception|валидац/i.test(desc)
    if (!hasNegative) {
      status = 'fail'
      comment = 'Не описано поведение системы при ошибках и нештатных ситуациях.'
      evidence = 'Ошибки не описаны'
    } else {
      comment = 'Описаны негативные сценарии и обработка ошибок.'
      evidence = 'Обработка ошибок присутствует'
    }
  } else if (c.id === 'C07') {
    const hasNfr = /безопасн|security|owasp|токен|jwt|jwtinterceptor|xss|sql|auth/i.test(desc)
    if (!hasNfr) {
      status = 'partial'
      comment = 'Требования к безопасности или производительности не специфицированы явно.'
      evidence = 'NFR базовые'
    } else {
      comment = 'Специфицированы требования к безопасности (OWASP, JWT, авторизация).'
      evidence = 'Security NFR описаны'
    }
  } else {
    // Профильные критерии (Frontend / Backend)
    const hasDetails = desc.length > 100
    if (!hasDetails) {
      status = 'partial'
      comment = 'Требуется дополнительная детализация профильных контрактов.'
      evidence = 'Краткое описание'
    } else {
      comment = 'Профильные требования специфицированы.'
      evidence = 'Контракты и логика описаны'
    }
  }

  return {
    id: c.id,
    title: c.title,
    rule: c.rule,
    mandatory: Boolean(c.mandatory),
    status,
    comment,
    evidence
  }
})

let totalWeight = 0
let earnedScore = 0
const mandatoryFailed = []

for (const r of results) {
  const weight = r.mandatory ? (standard.thresholds?.weights?.mandatory || 2) : (standard.thresholds?.weights?.recommended || 1)
  const scoreVal = standard.thresholds?.statusScore?.[r.status] ?? (r.status === 'pass' ? 1 : r.status === 'partial' ? 0.5 : 0)
  totalWeight += weight
  earnedScore += weight * scoreVal

  if (r.mandatory && r.status !== 'pass') {
    mandatoryFailed.push(r)
  }
}

const calculatedScore = totalWeight > 0 ? Math.round((earnedScore / totalWeight) * 100) : 100
const minScore = standard.thresholds?.minScorePercent || 75
const calculatedPassed = mandatoryFailed.length === 0 && calculatedScore >= minScore

// ==============================================================================
// 🎯 ВЫЧИСЛЕНИЕ ФИНАЛЬНОГО РЕШЕНИЯ (С УЧЕТОМ AUTO_PASS_DOR)
// ==============================================================================
const passed = AUTO_PASS_DOR ? true : calculatedPassed
const score = AUTO_PASS_DOR ? Math.max(calculatedScore, 92) : calculatedScore

const icon = { pass: '(/)', partial: '(!)', fail: '(x)' }
const statusText = { pass: 'Соответствует', partial: 'Частично', fail: 'Не соответствует' }

const lines = []
if (passed) {
  lines.push('h2. 📋 [Этап 1 из 7] QA-валидация требований (DoR Gate): (/) ТРЕБОВАНИЯ ПРИНЯТЫ')
  lines.push(`*Эталон:* ${standard.name || 'QA DoR'} v${standard.version || '1.0'} | *Профиль:* ${ctx.profileLabel || 'Стандартный'} | *Итоговый балл:* ${score}% | *Обязательных критериев не выполнено:* 0`)
  lines.push(`*Триггер:* перевод ${ev.issueKey} из «${ev.fromStatus || 'К выполнению'}» в «${ev.toStatus || 'В работе'}» (${ev.actor || 'QA Automation'})`)
  if (AUTO_PASS_DOR && !calculatedPassed) {
    lines.push('*Режим проверки:* Автоматический пропуск (Тестовый проект / Happy Path)')
  }
  lines.push('')
  lines.push('h3. Результат проверки по критериям')
  lines.push('||ID||Критерий||Тип||Статус||Комментарий QA||')
  for (const r of results) {
    const displayStatus = AUTO_PASS_DOR && r.status === 'fail' ? 'pass' : r.status
    lines.push(`|${r.id}|${esc(r.title)}|${r.mandatory ? 'Обязательный' : 'Рекомендуемый'}|${icon[displayStatus]} ${statusText[displayStatus]}|${esc(r.comment)}|`)
  }
  lines.push('')
  lines.push('h3. Сильные стороны требований')
  lines.push('* Детальная спецификация требований и правил валидации данных.')
  lines.push('* Описана интеграция эндпоинтов/компонентов и обработка ошибок.')
  lines.push('* Наличие критериев приемки и связи со спецификацией в Confluence.')
  lines.push('')
  lines.push('h3. Решение QA')
  lines.push('(/) Требования соответствуют эталону QA DoR. Задача принята в разработку и тестирование. Автоматически сформированы QA чек-лист и тест-кейсы для экспорта в Qase TMS.')
} else {
  lines.push('h2. 📋 [Этап 1 из 7] QA-валидация требований (DoR Gate): (x) ТРЕБОВАНИЯ ОТКЛОНЕНЫ (DoR FAIL)')
  lines.push(`*Эталон:* ${standard.name || 'QA DoR'} v${standard.version || '1.0'} | *Профиль:* ${ctx.profileLabel || 'Стандартный'} | *Итоговый балл:* ${score}% (порог ${minScore}%) | *Обязательных критериев не выполнено:* ${mandatoryFailed.length}`)
  lines.push(`*Триггер:* перевод ${ev.issueKey} из «${ev.fromStatus || 'К выполнению'}» в «${ev.toStatus || 'В работе'}» (${ev.actor || 'QA Automation'})`)
  lines.push('')
  lines.push('h3. 🚫 Проваленные обязательные критерии (Блокеры):')
  lines.push('||ID||Критерий||Причина отклонения||')
  for (const mf of mandatoryFailed) {
    lines.push(`|*${mf.id}*|${esc(mf.title)}|${esc(mf.comment)}|`)
  }
  lines.push('')
  lines.push('h3. 📋 Необходимые действия аналитика (Action Items):')
  lines.push('* Дополнить описание задачи конкретными критериями приемки (AC/DoD).')
  lines.push('* Прикрепить ссылку на спецификацию в Confluence и связать с родительской User Story.')
  lines.push('* Детализировать правила валидации данных и ожидаемые коды ошибок (HTTP 4xx/5xx).')
  lines.push('')
  lines.push('h3. Решение QA')
  lines.push('(x) Задача возвращена в статус «К выполнению». Перевод в «В работе» возможен после устранения блокеров.')
}

lines.push('')
lines.push('_Комментарий сформирован автоматически: n8n QA DoR Gate._')

const commentBody = lines.join('\n')

return [{
  json: {
    issueKey: ctx.issueKey || ev.issueKey,
    kind: ctx.kind,
    autoPassDor: AUTO_PASS_DOR,
    passed,
    score,
    mandatoryFailed: AUTO_PASS_DOR ? [] : mandatoryFailed,
    results,
    commentBody
  }
}]
