# PromptOps & Prompt Registry

Централизованный репозиторий и движок версионирования системных промптов для автономного QAOps-пайплайна.

---

## Архитектура и Структура Каталогов

Все промпты хранятся в формате чистых Markdown-файлов (`.md`), разделены по предметным областям (доменам) и строго версионируются:

```text
prompts/
├── registry.py                 # Программный фасад PromptRegistry
├── promptfooconfig.yaml        # Декларативная конфигурация регрессионного бенчмаркинга Promptfoo
├── README.md                   # Руководство по версионированию, откатам и оценке качества промптов
├── dor_evaluation/             # Домен 1: Оценка Definition of Ready (DoR Gate)
│   ├── v1.0_baseline.md        # Базовый промпт проверки INVEST
│   └── v2.0_enterprise.md      # Корпоративный промпт (INVEST + C06 контракты ошибок)
├── test_design_audit/          # Домен 2: Аудит тест-дизайна (Gate 1)
│   ├── v1.0_baseline.md        # Базовая проверка покрытия
│   └── v2.0_enterprise.md      # Расширенный ISTQB-аудит (персоны, BDD, корнер-кейсы)
├── code_review_audit/          # Домен 3: Код-ревью автотестов (Gate 2)
│   ├── v1.0_baseline.md        # Базовый синтаксический аудит
│   └── v2.0_enterprise.md      # Полный аудит (PEP8, Ruff, Allure, Pydantic, анти-flaky)
└── delta_requirements/         # Домен 4: Дельта-уточнение требований
    ├── v1.0_baseline.md        # Простое объединение текста
    └── v2.0_enterprise.md      # Семантический мердж и оценка влияния на TMS
```

---

## Управление Версиями (Prompt Versioning & Rollback)

По умолчанию пайплайн использует самую актуальную стабильную версию `v2.0_enterprise`.

### 1. Мгновенное переключение версии через переменные окружения (.env)
Любой промпт можно переключить на предыдущую версию или кастомную версию предприятия без изменения исходного кода Python:

```bash
# Откат оценки DoR на базовую версию v1.0
PROMPT_VERSION_DOR_EVALUATION=v1.0_baseline

# Откат код-ревью на базовую версию
PROMPT_VERSION_CODE_REVIEW_AUDIT=v1.0_baseline

# Использование специализированной версии для финтеха
PROMPT_VERSION_TEST_DESIGN_AUDIT=v2.1_fintech_strict
```

### 2. Программное использование в Python
```python
from prompts.registry import get_prompt, registry

# 1. Автоматический рендеринг активной версии с подстановкой переменных
prompt = get_prompt(
    "dor_evaluation",
    issue_key="JS-40",
    summary="Авторизация по паролю",
    context="Критерии приемки...",
)

# 2. Явный вызов конкретной версии (например, для A/B тестирования промптов)
v1_prompt = get_prompt("dor_evaluation", version="v1.0_baseline", context="...")

# 3. Получение списка доступных версий
versions = registry.list_versions("dor_evaluation")
# -> ['v1.0_baseline', 'v2.0_enterprise']
```

---

## Адаптация под другое предприятие

Чтобы адаптировать промпты под требования вашей компании (например, соответствие стандартам PCI-DSS, ISO 27001 или внутренним шаблонам):
1. Скопируйте существующий файл (например, `v2.0_enterprise.md`) в новый: `v2.1_mycompany.md`.
2. Отредактируйте специфичные для вашей компании критерии, скоринг или правила.
3. В файле `.env` укажите:
   ```bash
   PROMPT_VERSION_DOR_EVALUATION=v2.1_mycompany
   ```
4. Пайплайн автоматически подхватит новую версию без рестарта или рефакторинга компонентов.

---

## Регрессионный бенчмаркинг промптов (Promptfoo Integration)

Все 4 домена промптов охвачены автоматизированным регрессионным бенчмаркингом на базе [`prompts/promptfooconfig.yaml`](./promptfooconfig.yaml) и ранера [`qaops/promptfoo_runner.py`](../qaops/promptfoo_runner.py).

- Набор эталонных сценариев (Golden Dataset): включает реальные задачи `JS-40` (Backend API), `JS-41` (Frontend UI), `JS-42` (E2E Flow) и негативные ловушки (размытые ТЗ без контрактов ошибок, тест-кейсы без привязки к требованиям, автотесты с жестким `time.sleep(5)` и без декораторов Qase/Allure).
- Декларативные ассерты: проверяют валидность JSON-схем ответов (`is-json`), полноту подстановки контекста RAG (`contains-all`) и превосходство корпоративной версии `v2.0_enterprise` над базовой `v1.0_baseline` (`enterprise_delta > 0`).
- Запуск бенчмарка из Python или CLI:
  ```python
  from qaops.promptfoo_runner import run_promptfoo_benchmark

  report = run_promptfoo_benchmark()
  assert report["passed"] is True
  assert report["pass_rate"] == 1.0  # 8/8 эталонных сценариев пройдено
  ```
- Отчет сохраняется в `logs/promptfoo_benchmark_report.json` и включается в финальный индекс качества релиза (Release Quality Index) и карточку Evidence Pack в Jira.
