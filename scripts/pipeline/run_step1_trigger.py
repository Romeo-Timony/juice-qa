import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

sys.path.append(str(BASE_DIR / "scripts" / "pipeline"))
from task_lifecycle import transition_task, trigger_n8n_dor_gate, get_jira_issues, STATUS_TODO_ID, STATUS_IN_PROGRESS_ID, get_issue

# Определяем задачу динамически из аргументов или из бэклога
issue_key = sys.argv[1] if len(sys.argv) > 1 else None

if not issue_key:
    # Ищем первую подходящую подзадачу в «К выполнению»
    issues = get_jira_issues()
    candidates = [
        i["key"] for i in issues 
        if str(i.get("fields", {}).get("status", {}).get("id")) == STATUS_TODO_ID
        and i["key"] not in ("JS-1",) # исключаем эпик
    ]
    if not candidates:
        print("❌ Не найдено задач в статусе «К выполнению».")
        sys.exit(1)
    issue_key = candidates[0]
    print(f"🎯 Динамически выбрана следующая задача из бэклога: {issue_key}")

issue_data = get_issue(issue_key)
status_id = str(issue_data.get("fields", {}).get("status", {}).get("id"))
status_name = issue_data.get("fields", {}).get("status", {}).get("name")
summary = issue_data.get("fields", {}).get("summary")

print(f"\n========================================================")
print(f"🚀 ЗАПУСК ЗАДАЧИ В РАБОТУ: {issue_key}")
print(f"   Заголовок: {summary}")
print(f"   Текущий статус: {status_name} (ID: {status_id})")
print(f"========================================================")

if status_id != STATUS_IN_PROGRESS_ID:
    print(f"\n--- [ШАГ 1] Динамический перевод {issue_key} в статус «В работе» ---")
    success = transition_task(issue_key, target_status_id=STATUS_IN_PROGRESS_ID)
    if not success:
        print("❌ Ошибка перевода задачи. Прерывание.")
        sys.exit(1)
else:
    print(f"\n--- [ШАГ 1] Задача уже в статусе «В работе» ---")

print(f"\n--- [ШАГ 2] Отправка события в n8n DoR Gate Webhook ---")
trigger_n8n_dor_gate(issue_key)
print(f"✅ Задача {issue_key} успешно инициирована!")
