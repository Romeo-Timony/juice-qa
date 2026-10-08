# n8n Orchestration Architecture (QA Automation)

В n8n автоматизация тестирования разделена на два независимых, слабосвязанных контура (Micro-Pipelines):

1. **[dor-workflow/](./dor-workflow/) — Контур 1: DoR Gate & Test Design**
   * **Триггер**: Перевод задачи в Jira в статус «В работе» (`status = 10046`).
   * **Зона ответственности**: Валидация требований по Definition of Ready, генерация MindMap, синхронизация BDD тест-кейсов с Qase TMS, создание сабтаски автоматизации.
   * **Результат**: Тест-кейсы зарегистрированы в Qase с признаком `to-be-automated: 1`, метка `qa-dor-passed` в Jira.

2. **[autotest-workflow/](./autotest-workflow/) — Контур 2: Auto-Test Scaffolding & Execution**
   * **Триггер**: Перевод задачи в статус «Ready for QA» / «In QA» (или прямой вызов из Контура 1).
   * **Зона ответственности**: Загрузка `to-be-automated` кейсов из Qase TMS, скаффолдинг тестов (`tests/backend/test_{issueKey}_*.py` и `tests/frontend/test_{issueKey}_*.py`), запуск `pytest`, сбор Allure артефактов (скриншоты и видео), публикация Test Run в Qase TMS.
   * **Результат**: Прогон тестов, закрытие DoD (Definition of Done), публикация отчета Allure в Jira.
