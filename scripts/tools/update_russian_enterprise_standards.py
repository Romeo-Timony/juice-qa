"""
Скрипт полной синхронизации n8n воркфлоу с русскими корпоративными стандартами:
1. Интеграция вывода LLM Judge (Gemini) в ноду 'Проверка задачи на готовность' с порогом 80%.
2. Переименование и оформление всех 11 стикеров на доступном, понятном русском языке:
   - Исключение непонятных терминов 'Tier 1 / Tier 2', 'Seam 1 / Seam 2'
   - Замена на 'Контур 1 (Облачная оркестрация n8n)', 'Контур 2 (Локальный запуск SDET в Python)'
   - Четкие обозначения: 'Контрольная точка 1..6' вместо 'Seams'
3. Загрузка обновленного воркфлоу в n8n через REST API.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKFLOW_FILE = BASE_DIR / "n8n" / "current_main_workflow.json"
BACKUP_FILE = BASE_DIR / "n8n" / "backups" / "Dv1WydaTMC1lxR0E_Juice_Shop.json"

N8N_URL = os.getenv("N8N_URL", "http://201.34.147.33:5678").rstrip("/")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")
WORKFLOW_ID = "Dv1WydaTMC1lxR0E"

# 1. Новый проверочный код ноды DoR Gate с приемом данных от LLM Judge
NEW_DOR_CODE = r'''// n8n Code node: "Проверка задачи на готовность"
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

// ------------------------------------------------------------------------------
// 1. Оценка соответствия эталону QA DoR (Контрактные проверки)
// ------------------------------------------------------------------------------
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
    const hasNegative = /ошибк|негатив|401|400|404|409|500|exception|валидац|пуст|граничн|инъекц/i.test(desc)
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

// ------------------------------------------------------------------------------
// 2. Сбор вердикта нейросетевого судьи (LLM Judge на базе Gemini)
// ------------------------------------------------------------------------------
let llmJudgeVerdict = null
let llmScore = null
let llmPassed = null
let llmSummary = ''
let llmMissing = []
let llmActionItems = []

try {
  const llmItem = $('LLM Judge: Оценка готовности (DoR Gate)').first()
  if (llmItem && llmItem.json) {
    const rawText = llmItem.json.text || llmItem.json.response || (typeof llmItem.json === 'string' ? llmItem.json : JSON.stringify(llmItem.json))
    const jsonMatch = rawText.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      llmJudgeVerdict = JSON.parse(jsonMatch[0])
      llmScore = typeof llmJudgeVerdict.score === 'number' ? llmJudgeVerdict.score : null
      llmPassed = llmJudgeVerdict.dorPassed === true || String(llmJudgeVerdict.verdict || '').toUpperCase() === 'APPROVED' || String(llmJudgeVerdict.verdict || '').toUpperCase() === 'PASS'
      llmSummary = String(llmJudgeVerdict.summary || '')
      llmMissing = Array.isArray(llmJudgeVerdict.missingCriteria) ? llmJudgeVerdict.missingCriteria : []
      llmActionItems = Array.isArray(llmJudgeVerdict.actionItems) ? llmJudgeVerdict.actionItems : []
    }
  }
} catch (e) {
  // Защитный механизм: при сбое LLM опираемся на детерминированные проверки контракта
}

// ------------------------------------------------------------------------------
// 3. Валидация входных контрактов INVEST (Контрольная точка 1: DoR Gate)
// ------------------------------------------------------------------------------
const contractViolations = []
const effectiveIssueKey = ctx.issueKey || ev.issueKey

if (!effectiveIssueKey || !/^[A-Z][A-Z0-9]+-\d+$/.test(effectiveIssueKey)) {
  contractViolations.push('Невалидный или отсутствующий ID задачи (issueKey): ' + effectiveIssueKey)
}
if (!summary || typeof summary !== 'string' || summary.trim().length === 0) {
  contractViolations.push('Отсутствует или не является строкой заголовок задачи (summary)')
}

const evaluatedIds = new Set(results.map(r => r.id))
const investMap = {
  I: ['C03'],
  N: ['C07'],
  V: ['C02'],
  E: ['C05'],
  S: ['C01', 'C08'],
  T: ['C04', 'C06']
}
for (const [dim, ids] of Object.entries(investMap)) {
  const covered = ids.some(id => evaluatedIds.has(id))
  if (!covered) {
    contractViolations.push(`INVEST '${dim}' не подтверждён: нет оценки критериев ${ids.join(', ')}`)
  }
}

const contractValid = contractViolations.length === 0
const schemaComplianceRate = contractValid ? 1.0 : 0.0

// Единый корпоративный порог допуска требований (80%)
const minScore = 80

// Интегральная оценка: 40% вес детерминированных правил + 60% вес вердикта AI-судьи
const integratedScore = llmScore !== null
  ? Math.round((calculatedScore * 0.4) + (llmScore * 0.6))
  : calculatedScore

const userOverride = desc.includes('[DOR_OVERRIDE_APPROVED]') || summary.includes('[DOR_OVERRIDE_APPROVED]')

const calculatedPassed = contractValid && mandatoryFailed.length === 0 && calculatedScore >= 70 && integratedScore >= minScore && (llmScore !== null ? llmScore >= 70 : true)
const passed = contractValid && ((AUTO_PASS_DOR || userOverride) ? true : calculatedPassed)
const score = (AUTO_PASS_DOR || userOverride) ? Math.max(integratedScore, 92) : integratedScore

const icon = { pass: '(/)', partial: '(!)', fail: '(x)' }
const statusText = { pass: 'Соответствует', partial: 'Частично', fail: 'Не соответствует' }

const lines = []
if (!contractValid) {
  lines.push('h2. ⛔ Контрольная точка 1: Нарушен входной контракт требований задачи (DoR Gate)')
  lines.push(`*Задача:* ${effectiveIssueKey} | *Соответствие схеме:* 0% (требуется 100%)`)
  lines.push('')
  lines.push('h3. 🚫 Нарушения схемы контракта:')
  lines.push('{noformat}')
  for (const v of contractViolations) {
    lines.push(`• ${v}`)
  }
  lines.push('{noformat}')
  lines.push('')
  lines.push('_Пайплайн приостановлен до устранения несоответствий контракта (метка qa-paused)._')
} else if (passed) {
  lines.push('h2. 📋 [Этап 1 из 8] Проверка готовности требований (DoR Gate): (/) ТРЕБОВАНИЯ ПРИНЯТЫ')
  lines.push(`*Стандарт:* ${standard.name || 'QA DoR'} v${standard.version || '1.0'} | *Профиль:* ${ctx.profileLabel || 'Стандартный'} | *Итоговый балл:* ${score}% (порог ${minScore}%)`)
  lines.push(`*Входной контроль INVEST:* 100% подтверждено | *Обязательных блокеров:* 0`)
  if (llmScore !== null) {
    lines.push(`*Оценка нейросетевого судьи (Gemini):* ${llmScore}% (${llmPassed ? 'Одобрено' : 'Условно'})`)
  }
  lines.push(`*Триггер:* перевод ${ev.issueKey} из «${ev.fromStatus || 'К выполнению'}» в «${ev.toStatus || 'В работе'}» (${ev.actor || 'QA Automation'})`)
  if (AUTO_PASS_DOR && !calculatedPassed) {
    lines.push('*Режим проверки:* Автоматический пропуск (Тестовый проект / Happy Path)')
  } else if (userOverride && !calculatedPassed) {
    lines.push('*Режим проверки:* Ручное переопределение QA Lead (DOR_OVERRIDE_APPROVED)')
  }
  lines.push('')
  lines.push('h3. Результат проверки по критериям DoR')
  lines.push('||ID||Критерий||Тип||Статус||Комментарий QA||')
  for (const r of results) {
    const displayStatus = AUTO_PASS_DOR && r.status === 'fail' ? 'pass' : r.status
    lines.push(`|${r.id}|${esc(r.title)}|${r.mandatory ? 'Обязательный' : 'Рекомендуемый'}|${icon[displayStatus]} ${statusText[displayStatus]}|${esc(r.comment)}|`)
  }
  if (llmSummary) {
    lines.push('')
    lines.push('h3. 🧠 Заключение нейросетевого судьи (LLM Judge)')
    lines.push(`*Резюме:* ${esc(llmSummary)}`)
  }
  lines.push('')
  lines.push('h3. Решение QA')
  lines.push('(/) Требования соответствуют корпоративному стандарту DoR. Задача допущена к тестированию. Автоматически формируются чек-лист и тест-кейсы для базы Qase TMS.')
} else {
  lines.push('h2. 📋 [Этап 1 из 8] Проверка готовности требований (DoR Gate): (x) ТРЕБОВАНИЯ ОТКЛОНЕНЫ (DoR FAIL)')
  lines.push(`*Стандарт:* ${standard.name || 'QA DoR'} v${standard.version || '1.0'} | *Профиль:* ${ctx.profileLabel || 'Стандартный'} | *Итоговый балл:* ${score}% (порог ${minScore}%)`)
  lines.push(`*Обязательных критериев не выполнено:* ${mandatoryFailed.length}`)
  if (llmScore !== null) {
    lines.push(`*Оценка нейросетевого судьи (Gemini):* ${llmScore}% (${llmPassed ? 'Одобрено' : 'Отклонено'})`)
  }
  lines.push(`*Триггер:* перевод ${ev.issueKey} из «${ev.fromStatus || 'К выполнению'}» в «${ev.toStatus || 'В работе'}» (${ev.actor || 'QA Automation'})`)
  lines.push('')
  lines.push('h3. Результат проверки по критериям DoR')
  lines.push('||ID||Критерий||Тип||Статус||Комментарий QA||')
  for (const r of results) {
    lines.push(`|${r.id}|${esc(r.title)}|${r.mandatory ? 'Обязательный' : 'Рекомендуемый'}|${icon[r.status]} ${statusText[r.status]}|${esc(r.comment)}|`)
  }
  if (mandatoryFailed.length > 0) {
    lines.push('')
    lines.push('h3. 🚫 Проваленные обязательные критерии (Блокеры):')
    lines.push('||ID||Критерий||Причина отклонения||')
    for (const mf of mandatoryFailed) {
      lines.push(`|*${mf.id}*|${esc(mf.title)}|${esc(mf.comment)}|`)
    }
  }
  if (llmMissing.length > 0) {
    lines.push('')
    lines.push('h3. 🧠 Замечания нейросетевого судьи:')
    for (const item of llmMissing) {
      lines.push(`• ${esc(item)}`)
    }
  }
  lines.push('')
  lines.push('h3. 📋 Необходимые действия аналитика (План доработки):')
  if (llmActionItems.length > 0) {
    for (const action of llmActionItems) {
      lines.push(`• ${esc(action)}`)
    }
  } else {
    lines.push('• Дополнить описание задачи конкретными критериями приемки (AC/DoD).')
    lines.push('• Прикрепить ссылку на спецификацию в Confluence и связать с родительской User Story.')
    lines.push('• Детализировать правила валидации данных и ожидаемые коды ошибок (HTTP 4xx/5xx).')
  }
  lines.push('')
  lines.push('h3. Решение QA')
  lines.push('(x) Задача возвращена в статус «К выполнению». Перевод в «В работе» возможен после устранения блокеров.')
}

lines.push('')
lines.push('_Отчет сформирован автоматически: конвейер n8n QA DoR Gate._')

const commentBody = lines.join('\n')

const existingComments = ($('Jira: Загрузить данные задачи').first().json.fields?.comment?.comments) || []
const stage1 = existingComments.find(c => c.body && c.body.includes('[Этап 1 из'))
const commentMethod = stage1 ? 'PUT' : 'POST'
const commentUrl = stage1
  ? `${ev.config.jiraBase}/rest/api/2/issue/${effectiveIssueKey}/comment/${stage1.id}`
  : `${ev.config.jiraBase}/rest/api/2/issue/${effectiveIssueKey}/comment`

const targetLabel = !contractValid ? 'qa-paused' : (passed ? 'qa-dor-passed' : 'qa-dor-failed')

return [{
  json: {
    issueKey: effectiveIssueKey,
    kind: ctx.kind,
    autoPassDor: AUTO_PASS_DOR,
    passed,
    contractValid,
    contractViolations,
    schemaComplianceRate,
    score,
    mandatoryFailed: AUTO_PASS_DOR ? [] : mandatoryFailed,
    llmScore,
    llmPassed,
    llmSummary,
    results,
    commentBody,
    commentMethod,
    commentUrl,
    targetLabel
  }
}]
'''

# 2. Обновленные стикеры на доступном русском языке без англицизмов
STICKY_CONTENTS = {
    "sticky-block-1": (
        "## 📥 Блок 1: Входной шлюз задач (Приём событий Jira Cloud)\n\n"
        "**🎯 Назначение:**\n"
        "Точка входа всего конвейера. Мгновенный перехват событий создания или изменения задач в Jira Cloud. "
        "Фильтрует события, определяет перевод задачи в работу и запускает процесс обеспечения качества.\n\n"
        "**📋 Ноды в блоке:**\n"
        "• `Jira: Перехват обновления задачи` — вебхук прямого приема событий от Jira\n"
        "• `Execute Workflow Trigger` — входная точка для ручного или программного вызова\n"
        "• `Фильтр: Задача взята в работу` — фильтрация события перехода в статус «В работе»\n\n"
        "**⚙️ Архитектурный контур:**\n"
        "Контур 1 (Облачная оркестрация n8n): моментальный прием и маршрутизация событий.\n\n"
        "**💾 Хранилище / БД / Таблицы:**\n"
        "• PostgreSQL: `qa_pipeline_events` (событие `PIPELINE_STARTED`)\n"
        "• PostgreSQL: `qaops_idempotency` (защита от повторных срабатываний)\n\n"
        "**🔗 Прямые ссылки:**\n"
        "• [🔗 Доска задач Jira (Проект JS)](https://romeo-timony.atlassian.net/jira/software/projects/JS/boards)\n"
        "• [🔗 История запусков n8n](http://201.34.147.33:5678/executions)\n\n"
        "**💡 Инструкция для инженера:**\n"
        "Чтобы запустить автотестирование по задаче, переведите тикет в статус **«В работе»**."
    ),
    "sticky-block-2": (
        "## 🏥 Блок 2: Предстартовая диагностика всех 7 сервисов инфраструктуры\n\n"
        "**🎯 Назначение (Защитный контур высокой готовности):**\n"
        "Перед тем как тратить токены нейросети и менять статусы тикетов, система опрашивает ВСЕ 7 внешних и внутренних сервисов. "
        "Если хотя бы одна служба недоступна, запуск блокируется с мгновенным оповещением команды.\n\n"
        "**⚙️ Проверяемые службы и сервисы:**\n"
        "1. `Jira Cloud REST API` — авторизация и доступность проекта `JS`\n"
        "2. `Qase TMS API` — доступность базы тест-кейсов и валидность токена\n"
        "3. `Telegram Bot API` — статус реального бота **@QApower_bot**\n"
        "4. `Langfuse Cloud` — сервер сбора трейсов и метрик качества\n"
        "5. `Google Gemini LLM` — доступность нейросетевой модели\n"
        "6. `GitHub Actions API` — статус репозитория и раннеров\n"
        "7. `SQL Data Tables / Event Store` — доступность рабочих таблиц базы данных\n\n"
        "**📋 Ноды в блоке:**\n"
        "• 7 параллельно-последовательных диагностических HTTP-проверок\n"
        "• `Stage 0: Валидация готовности ВСЕЙ инфраструктуры` — расчет SLA и вердикт\n"
        "• `Условие: Все службы и агенты готовы к работе?` — защитный шлюз\n"
        "• `Telegram: 🚨 Отказ запуска` — пуш-уведомление через **@QApower_bot**\n\n"
        "**💾 Хранилище / БД / Таблицы:**\n"
        "• SQL Таблица: `QA Pipeline Errors` (ID: `eCPXK5QUBpIxYyEc`)\n"
        "• Модуль здоровья: `qaops/health.py`\n\n"
        "**🔗 Прямые ссылки на мониторинг:**\n"
        "• [🔗 Статус Jira REST API](https://romeo-timony.atlassian.net/rest/api/2/myself)\n"
        "• [🔗 Статус Qase TMS API](https://api.qase.io/v1/project/JS)\n"
        "• [🔗 Реальный Telegram бот @QApower_bot](https://t.me/QApower_bot)\n"
        "• [🔗 Мониторинг Langfuse Cloud](https://cloud.langfuse.com)\n"
        "• [🔗 Мониторинг GitHub Actions](https://github.com/juice-shop/juice-shop/actions)\n"
        "• [🔗 Таблицы n8n Data Tables](http://201.34.147.33:5678/data-tables)\n\n"
        "**💡 Инструкция при сбое:**\n"
        "При получении алерта запустите `run_health_check.bat` для детальной локализации сбоя."
    ),
    "sticky-block-3": (
        "## 📋 Блок 3: Этап 1 — Проверка готовности требований к тестированию (DoR Gate & AI-судья)\n\n"
        "**🎯 Назначение:**\n"
        "Автоматический аудит качества пользовательской истории по стандарту Definition of Ready (DoR). "
        "Включает две ступени проверки: строгий контракт INVEST и семантическую оценку независимым AI-судьей (Google Gemini).\n\n"
        "**⚙️ Архитектурные контрольные точки:**\n"
        "• **Контур 1 (Облачный экспресс-анализ):** Проверка полноты AC, формализация эндпоинтов, кодов ошибок (C06) и ролей.\n"
        "• **Контрольная точка 1 (Входной контракт DoR):** Валидация схемы INVEST по 6 измерениям (порог допуска >= 80%).\n\n"
        "**📋 Ноды в блоке:**\n"
        "• `Jira: Загрузить данные задачи` & `ссылки` — получение описания и спецификаций Confluence\n"
        "• `Правила проверки готовности задачи` — выгрузка корпоративных политик DoR\n"
        "• `LLM Judge: Оценка готовности (DoR Gate)` — запуск нейросетевого судьи Gemini с системным промптом\n"
        "• `Gemini Model: DoR Judge` — модель Google Gemini\n"
        "• `Проверка задачи на готовность` — сведение контракта INVEST и вердикта AI-судьи (порог >= 80%)\n"
        "• `Условие: Требования задачи понятны?` — развилка ДОПУСК / ОТКЛОНЕНИЕ\n"
        "• `Jira: Отчет 1 — DoR Gate` & `Langfuse` — публикация отчета №1 в тикет и фиксация телеметрии\n\n"
        "**💾 Хранилище / БД / Таблицы:**\n"
        "• Jira Cloud Comments: публикация Отчета №1\n"
        "• Langfuse Traces: фиксация токенов и времени отклика нейросети\n"
        "• Промпт: `prompts/dor_evaluation/v2.0_enterprise.md`\n\n"
        "**🔗 Прямые ссылки на инструменты:**\n"
        "• [🔗 Бэклог задач Jira (Проект JS)](https://romeo-timony.atlassian.net/jira/software/projects/JS/boards)\n"
        "• [🔗 Трейсы в Langfuse Cloud](https://cloud.langfuse.com)\n"
        "• [📄 Промпт DoR v2.0 Enterprise](file:///d:/Desktop/Juice_shop/qa-automation/prompts/dor_evaluation/v2.0_enterprise.md)\n\n"
        "**💡 Инструкция для инженера:**\n"
        "При успешном DoR задача переходит к Этапу 2. При обнаружении блокеров (DoR < 80%) поток направляется в Блок 4 (Эскалация)."
    ),
    "sticky-block-4": (
        "## ❌ Блок 4: Возврат задачи аналитику при неполных требованиях (Эскалация)\n\n"
        "**🎯 Назначение:**\n"
        "Обработка задач с дефектами аналитики. Публикует структурированный список замечаний в Jira, переводит задачу обратно в «К выполнению» "
        "(To Do / ID: 10045) или ставит на паузу (`qa-paused`), и оповещает команду через Telegram.\n\n"
        "**⚙️ Входные данные:**\n"
        "Отрицательный вердикт от ноды `Условие: Требования задачи понятны?` (FALSE).\n\n"
        "**📋 Ноды в блоке:**\n"
        "• `Jira: Отправить замечания к задаче` — публикация списка замечаний и рекомендаций в тикет\n"
        "• `Условие: Пауза из-за контракта или возврат?` — выбор стратегии (пауза или возврат в To Do)\n"
        "• `Jira: Поставить метку qa-paused` — маркировка ожидания бэкенд-контракта\n"
        "• `Jira: Вернуть задачу на доработку` — смена статуса в «К выполнению»\n"
        "• `Jira: Поставить метку Требует доработки` — выставление метки `qa-dor-failed`\n"
        "• `Telegram: Алерт об отклонении DoR` — уведомление Product Owner и лида через **@QApower_bot**\n\n"
        "**💾 Хранилище / БД / Таблицы:**\n"
        "• Jira Cloud Transitions & Labels\n"
        "• PostgreSQL: `qa_pipeline_events` (событие `DOR_REJECTED`)\n\n"
        "**🔗 Прямые ссылки на инструменты:**\n"
        "• [🔗 Задачи, требующие доработки (Jira JQL)](https://romeo-timony.atlassian.net/issues/?jql=project%3DJS%20AND%20labels%3Dqa-dor-failed)\n"
        "• [🔗 Канал алертов в Telegram (@QApower_bot)](https://t.me/QApower_bot)\n\n"
        "**💡 Инструкция для инженера:**\n"
        "Для разблокировки задачи аналитик/разработчик дополняет описание тикета или оставляет комментарий `@qa-bot [ДОПОЛНЕНИЕ] ...`. "
        "Демон автоматически подхватит правку."
    ),
    "sticky-block-5": (
        "## 🧠 Блок 5: Этап 2 — Интеллект-карта и декомпозиция проверок\n\n"
        "**🎯 Назначение:**\n"
        "Системная декомпозиция требований на слои тестирования: позитивные сценарии (Happy Path), негативные проверки, "
        "граничные значения, роли безопасности (Admin, Customer, Guest) и проверка API-контрактов. "
        "Формирует наглядную карту проверок и публикует Отчет №2 в тикет Jira.\n\n"
        "**📋 Ноды в блоке:**\n"
        "• `Подготовка данных для чек-листа` — структурирование требований\n"
        "• `Создание карты проверок` — построение дерева проверок по методологии тест-дизайна\n"
        "• `Jira: Отчет 2 — Чек-лист проверок` — публикация Отчета №2 в тикет\n\n"
        "**💾 Хранилище / БД / Таблицы:**\n"
        "• Таблица: `QA Test Cases` в n8n Data Tables\n"
        "• PostgreSQL: `qa_pipeline_events` (событие `MINDMAP_GENERATED`)\n\n"
        "**🔗 Прямые ссылки на инструменты:**\n"
        "• [🔗 Таблица тестов в n8n Data Tables](http://201.34.147.33:5678/data-tables)\n"
        "• [🔗 Доска задач Jira (Проект JS)](https://romeo-timony.atlassian.net/jira/software/projects/JS/boards)\n\n"
        "**💡 Инструкция для инженера:**\n"
        "Ознакомьтесь с картой проверок в Отчете №2 тикета перед переходом к утверждению тест-кейсов."
    ),
    "sticky-block-6": (
        "## 🧪 Блок 6: Этапы 3 и 4 — Синхронизация с базой тестов Qase TMS и BDD тест-дизайн\n\n"
        "**🎯 Назначение:**\n"
        "Двусторонняя синхронизация тест-кейсов с системой управления тестированием Qase TMS (проект `JS`). "
        "Генерация BDD-тестов (Given-When-Then), интеллектуальное исключение дубликатов (Deduplication) "
        "и построение матрицы прослеживаемости требований (RTM).\n\n"
        "**⚙️ Архитектурные контрольные точки:**\n"
        "• **Контур 1 (Облако n8n):** Экспорт тест-кейсов в Qase TMS, проверка уникальности, генерация матрицы RTM.\n"
        "• **Контур 2 (Локальный SDET-контур):** Включается при генерации кода тестов (Контрольная точка 2: "
        "глубокий аудит обоснованности кейсов через DeepEval G-Eval с порогом Groundedness >= 90%).\n\n"
        "**📋 Ноды в блоке:**\n"
        "• `Подготовка данных для тест-кейсов` & `Создание тест-кейсов без повторов` — дедупликация\n"
        "• `Qase: Загрузить существующие тесты` — чтение актуального репозитория Qase\n"
        "• `LLM Judge: Аудит тест-дизайна (Design Gate)` — аудит структуры BDD через Gemini\n"
        "• `Qase: Создать новые тесты в базе` — запись проверок в Qase TMS\n"
        "• `Jira: Отчет 3 — Реестр тест-кейсов (BDD)` & `Jira: Отчет 4 — Матрица RTM` — отчеты №3 и №4 в Jira\n"
        "• `Анализ рассинхрона Qase (Drift Detector)` — детекция дрейфа тестов\n\n"
        "**💾 Хранилище / БД / Таблицы:**\n"
        "• Qase TMS: проект `JS`\n"
        "• n8n Data Tables: `QA Test Cases`\n"
        "• PostgreSQL: `qa_pipeline_events` (событие `TEST_CASES_SYNCED`)\n\n"
        "**🔗 Прямые ссылки на инструменты:**\n"
        "• [🔗 Репозиторий тестов Qase TMS (Проект JS)](https://app.qase.io/project/JS)\n"
        "• [🔗 Бэклог задач Jira (Проект JS)](https://romeo-timony.atlassian.net/jira/software/projects/JS/boards)\n\n"
        "**💡 Инструкция для инженера:**\n"
        "Все сгенерированные кейсы автоматически привязываются к тикету Jira прямой веб-ссылкой."
    ),
    "sticky-block-7": (
        "## 🛡️ Блок 7: Этап 5 — Первое согласование инженером (Контроль тест-дизайна)\n\n"
        "**🎯 Назначение:**\n"
        "Первый защитный рубеж с участием человека (Human-in-the-Loop Gate 1). "
        "Конвейер переводит тикет в статус согласования, отправляет карточку в Telegram лиду QA "
        "и переходит в режим ожидания (Wait Node). Разработка кода автотестов не начнется без явного подтверждения инженера.\n\n"
        "**📋 Ноды в блоке:**\n"
        "• `Jira: Статус — На согласовании у QA` — смена статуса в Jira Cloud\n"
        "• `Telegram: Карточка согласования (Gate 1)` — интерактивное уведомление через **@QApower_bot**\n"
        "• `Ожидание решения QA-инженера (Gate 1)` — нода n8n Wait Node (режим ожидания вебхука)\n\n"
        "**⚙️ Архитектурный контур:**\n"
        "Контур 1 (Облачная оркестрация): безопасная пауза конвейера без потребления вычислительных ресурсов.\n\n"
        "**💾 Хранилище / БД / Таблицы:**\n"
        "• PostgreSQL: `qa_pipeline_state` (статус `hitl_gate1_status = 'WAITING'`)\n"
        "• Таблица: `QA Pipeline Tasks` в n8n Data Tables\n\n"
        "**🔗 Прямые ссылки на инструменты:**\n"
        "• [🔗 Канал согласований в Telegram (@QApower_bot)](https://t.me/QApower_bot)\n"
        "• [🔗 Очередь задач на согласовании в Jira](https://romeo-timony.atlassian.net/jira/software/projects/JS/boards)\n\n"
        "**💡 Инструкция по согласованию:**\n"
        "Инженер проверяет тесты в Qase и пишет комментарий **`ОК`** в Jira. "
        "Демон `qa_agent_daemon.py` перехватит согласование и возобновит работу воркфлоу."
    ),
    "sticky-block-8": (
        "## ⚙️ Блок 8: Этапы 6 и 7 — Автоматическая генерация кода тестов и аудит качества\n\n"
        "**🎯 Назначение:**\n"
        "Генерация промышленного кода автотестов на Python (Pytest + Requests + Playwright), "
        "строгий аудит синтаксиса, прогон статического анализатора и второе согласование старшим инженером (Gate 2).\n\n"
        "**⚙️ Архитектурные контрольные точки (Контур 2 — Локальный SDET в Python):**\n"
        "• **Контрольная точка 3 (Статический аудит кода):** Проверка AST-дерева, линтинг Ruff (правила E9, F63, F7, F82), изолированный запуск `pytest --collect-only`.\n"
        "• **Контрольная точка 5 (Согласование Senior AQA):** Публикация в Jira полного пакета доказательств (Evidence Pack) со ссылками на код в Git.\n\n"
        "**📋 Ноды в блоке:**\n"
        "• `Jira: Отчет 5 — Код автотестов готов` — публикация ссылки на ветку в Git\n"
        "• `Jira: Отчет 6 — Аудит кода тестов (Ruff + AST)` — публикация отчета статического анализа\n"
        "• `Telegram: Карточка согласования кода (Gate 2)` — отправка карточки кода в **@QApower_bot**\n"
        "• `Ожидание решения Senior AQA (Gate 2)` — нода n8n Wait Node (ожидание аппрува кода)\n\n"
        "**💾 Хранилище / БД / Таблицы:**\n"
        "• PostgreSQL: `qa_pipeline_state` (`hitl_gate2_status = 'WAITING'`)\n"
        "• Каталог кода: `tests/review/`\n\n"
        "**🔗 Прямые ссылки на инструменты:**\n"
        "• [🔗 Канал согласований в Telegram (@QApower_bot)](https://t.me/QApower_bot)\n"
        "• [🔗 Репозиторий кода автотестов на GitHub](https://github.com/juice-shop/juice-shop)\n\n"
        "**💡 Инструкция по согласованию:**\n"
        "Senior AQA проводит ревью сгенерированного кода и отправляет комментарий **`ОК`** в Jira."
    ),
    "sticky-block-9": (
        "## 🐙 Блок 9: Запуск автоматических тестов в конвейере GitHub Actions\n\n"
        "**🎯 Назначение:**\n"
        "После утверждения кода Senior AQA воркфлоу отправляет команду на запуск реального конвейера CI/CD в GitHub Actions "
        "через событие `repository_dispatch`. Выполняет слияние ветки и запускает тесты в чистых Docker-контейнерах.\n\n"
        "**📋 Ноды в блоке:**\n"
        "• `GitHub: Запуск тестов в CI/CD` — HTTP POST вызов API GitHub Actions с payload задачи\n"
        "• `Jira: Добавить ссылку на запуск GitHub` — прикрепление ссылки на Run в тикет\n"
        "• `Telegram: Уведомление о старте CI/CD` — оповещение о запуске прогона через **@QApower_bot**\n\n"
        "**⚙️ Архитектурный контур:**\n"
        "Контур 1 (Облачная оркестрация n8n): связывает событие согласования в Jira с облачным раннером GitHub Actions.\n\n"
        "**💾 Хранилище / БД / Таблицы:**\n"
        "• PostgreSQL: `qa_pipeline_events` (событие `CI_RUN_DISPATCHED`)\n"
        "• GitHub API: `POST /repos/juice-shop/juice-shop/dispatches`\n\n"
        "**🔗 Прямые ссылки на инструменты:**\n"
        "• [🔗 Конвейеры GitHub Actions](https://github.com/juice-shop/juice-shop/actions)\n"
        "• [🔗 Канал уведомлений в Telegram (@QApower_bot)](https://t.me/QApower_bot)\n\n"
        "**💡 Инструкция для инженера:**\n"
        "Статус выполнения раннера можно отслеживать в реальном времени по ссылке в тикете Jira."
    ),
    "sticky-block-10": (
        "## 📊 Блок 10: Этап 8 — Результаты прогона автотестов и отчетность Allure Report\n\n"
        "**🎯 Назначение:**\n"
        "Финал жизненного цикла задачи. Прием результатов тестирования из GitHub Actions, формирование Отчета №7 в Jira Cloud, "
        "публикация интерактивного Allure Report с логами и видеозаписями падений, автоматический перевод задачи в статус «Готово» (Done).\n\n"
        "**📋 Ноды в блоке:**\n"
        "• `Приём результатов из GitHub Actions` — вебхук приема итогов тестового прогона\n"
        "• `Jira: Отчет 7 — Результаты прогона и Allure` — публикация сводки прогона в тикет\n"
        "• `Jira: Перевод задачи в Готово` — смена статуса тикета в Done (ID: 10047)\n"
        "• `Telegram: Победный алерт о релизе` — победное уведомление команды через **@QApower_bot**\n\n"
        "**💾 Хранилище / БД / Таблицы:**\n"
        "• Allure Report: HTML-отчет с таймлайном и трассировками\n"
        "• PostgreSQL: `qa_pipeline_state` (`current_stage = 'DONE'`, `status = 'COMPLETED'`)\n"
        "• Таблица: `QA Pipeline Tasks` в n8n Data Tables\n\n"
        "**🔗 Прямые ссылки на инструменты:**\n"
        "• [🔗 Интерактивный Allure Report](https://juice-shop.github.io/allure-report/)\n"
        "• [🔗 Завершенные задачи в Jira (Проект JS)](https://romeo-timony.atlassian.net/jira/software/projects/JS/boards)\n"
        "• [🔗 Канал релизов в Telegram (@QApower_bot)](https://t.me/QApower_bot)\n\n"
        "**💡 Инструкция для инженера:**\n"
        "При 100% успехе автотестов задача закрывается автоматически без ручных манипуляций."
    ),
    "sticky-error-fork": (
        "## 🚨 Перехватчик системных сбоев: Автономная регистрация ошибок в базе данных\n\n"
        "**🎯 Назначение (Нулевая слепая зона при отказах):**\n"
        "Глобальный перехватчик любых непредвиденных сбоев воркфлоу (Error Workflow Trigger). "
        "При падении любой ноды перехватывает контекст сбоя, формирует диагностическую карточку, "
        "сохраняет запись об ошибке в SQL-базу данных и моментально отправляет алерт в Telegram.\n\n"
        "**📋 Ноды в блоке:**\n"
        "• `Error Trigger: Перехват системных сбоев` — глобальный перехват аварий n8n\n"
        "• `Форматирование карточки сбоя` — извлечение имени упавшей ноды, сообщения и стека ошибки\n"
        "• `SQL: Запись сбоя в таблицу QA Pipeline Errors` — сохранение сбоя в постоянную базу данных\n"
        "• `Telegram: Алерт о сбое (@QApower_bot)` — экстренное пуш-уведомление через **@QApower_bot**\n\n"
        "**💾 Хранилище / БД / Таблицы:**\n"
        "• SQL Таблица: `QA Pipeline Errors` (ID: `eCPXK5QUBpIxYyEc` в n8n Data Tables)\n"
        "• PostgreSQL: `схема qaops_db в PostgreSQL` (таблица `qa_pipeline_errors`)\n"
        "• PostgreSQL: таблица `qa_pipeline_errors` в корпоративной схеме\n\n"
        "**🔗 Прямые ссылки на мониторинг:**\n"
        "• [🔗 Таблица журнала ошибок QA Pipeline Errors](http://201.34.147.33:5678/data-tables)\n"
        "• [🔗 Канал экстренных алертов в Telegram (@QApower_bot)](https://t.me/QApower_bot)\n"
        "• [🔗 Журнал сбоев n8n Executions](http://201.34.147.33:5678/executions)\n\n"
        "**💡 Инструкция для инженера:**\n"
        "Каждая ошибка сохраняется с уникальным ID, именем задачи и подробным стеком для быстрого расследования."
    )
}

def main():
    print("🚀 Старт обновления n8n воркфлоу под русские корпоративные стандарты...")
    
    with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
        wf = json.load(f)
        
    updated_nodes = 0
    updated_stickies = 0
    
    for node in wf.get("nodes", []):
        # 1. Обновление ноды "Проверка задачи на готовность"
        if node.get("name") == "Проверка задачи на готовность":
            node["parameters"]["jsCode"] = NEW_DOR_CODE
            node["notes"] = "⚖️ Контрольная точка 1: Совмещенная оценка контракта INVEST и вердикта AI-судьи (DoR Gate, порог 80%)."
            updated_nodes += 1
            print("  ✅ Обновлен код ноды 'Проверка задачи на готовность' (интеграция LLM Judge + порог 80%)")
            
        # 2. Обновление стикеров
        sticky_id = node.get("id")
        if sticky_id in STICKY_CONTENTS:
            node["parameters"]["content"] = STICKY_CONTENTS[sticky_id]
            updated_stickies += 1
            print(f"  📝 Обновлен стикер '{node.get('name')}' ({sticky_id})")

    print(f"\n📊 Итог модификаций: {updated_nodes} нод изменено, {updated_stickies} стикеров обновлено.")
    
    # Сохраняем локальные файлы
    with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)
    print(f"💾 Файлы сохранены: {WORKFLOW_FILE.name} и {BACKUP_FILE.name}")
    
    # 3. Отправка обновленного воркфлоу в n8n через REST API
    headers = {
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": wf.get("name", "Juice Shop"),
        "nodes": wf.get("nodes", []),
        "connections": wf.get("connections", {}),
        "settings": wf.get("settings", {}),
        "staticData": wf.get("staticData", None)
    }
    
    url = f"{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}"
    print(f"\n🌐 Отправка воркфлоу в n8n Cloud ({url})...")
    resp = requests.put(url, headers=headers, json=payload, timeout=30)
    
    if resp.status_code == 200:
        print("🎉 Воркфлоу успешно обновлен и опубликован в n8n Cloud!")
    else:
        print(f"❌ Ошибка отправки в n8n: HTTP {resp.status_code}")
        print(resp.text[:500])
        sys.exit(1)

if __name__ == "__main__":
    main()
