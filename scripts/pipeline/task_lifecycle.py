import os
import sys
import argparse
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

JIRA_URL = os.getenv("ATLASSIAN_BASE_URL", "https://romeo-timony.atlassian.net").rstrip("/")
EMAIL = os.getenv("ATLASSIAN_USER_EMAIL")
TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
AUTH = (EMAIL, TOKEN)
N8N_URL = (os.getenv("N8N_URL") or os.getenv("N8N_SERVER_URL") or "http://201.34.147.33:5678").rstrip("/")

STATUS_TODO_ID = "10045"
STATUS_IN_PROGRESS_ID = "10046"
STATUS_TESTS_PASSED_ID = "10048"


def get_jira_issues(project_key: str = "JS") -> List[Dict[str, Any]]:
    """Получает актуальный список задач проекта напрямую из Jira."""
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    jql = f"project = {project_key} ORDER BY key ASC"
    resp = requests.get(url, auth=AUTH, params={"jql": jql, "fields": "summary,status,labels,issuetype,assignee"}, timeout=15)
    resp.raise_for_status()
    return resp.json().get("issues", [])


def get_issue(issue_key: str) -> Dict[str, Any]:
    """Получает детальную информацию о конкретной задаче."""
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
    resp = requests.get(url, auth=AUTH, params={"fields": "summary,status,labels,description,comment"}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_available_transitions(issue_key: str) -> List[Dict[str, Any]]:
    """Динамически запрашивает доступные переходы (transitions) для задачи без хардкода ID."""
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
    resp = requests.get(url, auth=AUTH, timeout=15)
    resp.raise_for_status()
    return resp.json().get("transitions", [])


def find_transition_to_status(issue_key: str, target_status_id: str = STATUS_IN_PROGRESS_ID) -> Optional[Dict[str, Any]]:
    """Находит переход, ведущий в целевой статус (по ID или имени)."""
    transitions = get_available_transitions(issue_key)
    for t in transitions:
        to_status = t.get("to", {})
        if str(to_status.get("id")) == target_status_id:
            return t
        name_lower = to_status.get("name", "").lower()
        if target_status_id == STATUS_IN_PROGRESS_ID and ("работ" in name_lower or "progress" in name_lower):
            return t
        if target_status_id == STATUS_TESTS_PASSED_ID and ("пройден" in name_lower or "review" in name_lower or "done" in name_lower):
            return t
    return None


def transition_task(issue_key: str, target_status_id: str = STATUS_IN_PROGRESS_ID) -> bool:
    """Выполняет перевод задачи в требуемый статус с динамическим поиском transition ID."""
    transition = find_transition_to_status(issue_key, target_status_id)
    if not transition:
        avail = [f"{t.get('name')} -> {t.get('to', {}).get('name')} (id: {t.get('id')})" for t in get_available_transitions(issue_key)]
        print(f"❌ Для задачи {issue_key} не найден переход в целевой статус {target_status_id}.")
        print(f"   Доступные переходы: {avail}")
        return False

    trans_id = transition["id"]
    trans_name = transition["name"]
    to_name = transition.get("to", {}).get("name")
    print(f"🔄 Выполняем переход: {trans_name} (ID: {trans_id}) -> новый статус: {to_name}")

    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
    resp = requests.post(url, auth=AUTH, json={"transition": {"id": trans_id}}, timeout=15)
    if not resp.ok:
        print(f"❌ Ошибка перехода в Jira HTTP {resp.status_code}: {resp.text}")
        return False

    print(f"✅ Задача {issue_key} успешно переведена в статус «{to_name}»!")
    return True


def trigger_n8n_dor_gate(issue_key: str, actor: str = "Roman Timoshenko") -> bool:
    """Отправляет событие запуска пайплайна в n8n (как резервный канал к Jira Cloud Webhook)."""
    url = f"{N8N_URL}/webhook/jira-dor-gate"
    payload = {"issueKey": issue_key, "actor": actor}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"⚡ Сигнал в n8n webhook ({url}): HTTP {resp.status_code} {resp.text.strip()}")
        return resp.ok
    except Exception as e:
        print(f"⚠️ Ошибка вызова n8n webhook: {e}")
        return False


def cmd_list(args):
    """Показывает реальный статус всех задач в проекте."""
    issues = get_jira_issues()
    print("=" * 80)
    print(f"📋 АКТУАЛЬНЫЙ СПИСОК ЗАДАЧ JIRA (ПРОЕКТ JS) — {len(issues)} задач")
    print("=" * 80)
    for issue in issues:
        key = issue["key"]
        fields = issue["fields"]
        status_name = fields.get("status", {}).get("name", "Unknown")
        status_id = fields.get("status", {}).get("id", "")
        summary = fields.get("summary", "")
        labels = fields.get("labels", [])
        assignee = (fields.get("assignee") or {}).get("displayName", "Unassigned")
        
        status_marker = "⚪"
        if status_id == STATUS_TODO_ID:
            status_marker = "⏳ [К выполнению]"
        elif status_id == STATUS_IN_PROGRESS_ID:
            status_marker = "🚀 [В работе]"
        elif status_id == STATUS_TESTS_PASSED_ID:
            status_marker = "✅ [Автотесты пройдены]"
            
        print(f"{key:<8} | {status_marker:<24} | {assignee:<18} | {summary[:45]}")
    print("=" * 80)


def cmd_start(args):
    """Динамический запуск задачи в работу без хардкода."""
    target_key = args.issue_key
    
    if not target_key:
        # Автоматический поиск первой задачи в статусе «К выполнению»
        issues = get_jira_issues()
        todo_issues = [i for i in issues if str(i.get("fields", {}).get("status", {}).get("id")) == STATUS_TODO_ID]
        if not todo_issues:
            print("ℹ️ В проекте нет задач в статусе «К выполнению» (10045).")
            return
        target_key = todo_issues[0]["key"]
        print(f"🎯 Автоматически выбрана следующая задача из бэклога: {target_key}")

    # 1. Читаем реальное состояние задачи
    issue = get_issue(target_key)
    fields = issue["fields"]
    curr_status_name = fields.get("status", {}).get("name")
    curr_status_id = str(fields.get("status", {}).get("id"))
    summary = fields.get("summary")
    
    print(f"\n📌 Выбранная задача: {target_key}")
    print(f"   Заголовок: {summary}")
    print(f"   Текущий реальный статус: {curr_status_name} (ID: {curr_status_id})")

    # 2. Если задача уже «В работе»
    if curr_status_id == STATUS_IN_PROGRESS_ID:
        print(f"ℹ️ Задача {target_key} уже находится в статусе «{curr_status_name}». Отправляем вызов в n8n...")
        trigger_n8n_dor_gate(target_key)
    elif curr_status_id == STATUS_TODO_ID:
        # 3. Переводим задачу в «В работе» динамически
        success = transition_task(target_key, target_status_id=STATUS_IN_PROGRESS_ID)
        if not success:
            print("❌ Не удалось перевести задачу в статус «В работе». Прерывание.")
            return
        print("⚡ Переход в Jira выполнен -> Jira Cloud Webhook автоматически инициирует воркфлоу n8n через ngrok.")
    else:
        print(f"⚠️ Задача {target_key} в статусе {curr_status_name} (ID: {curr_status_id}). Переводим в «В работе»...")
        success = transition_task(target_key, target_status_id=STATUS_IN_PROGRESS_ID)
        if not success:
            return
        print("⚡ Переход в Jira выполнен -> Jira Cloud Webhook автоматически инициирует воркфлоу n8n через ngrok.")

    print(f"\n🚀 Задача {target_key} запущена в работу! Ожидание на Quality Gate 1.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Управление жизненным циклом задач Jira без хардкода")
    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # list
    subparsers.add_parser("list", help="Показать актуальное состояние задач в Jira")

    # start
    start_parser = subparsers.add_parser("start", help="Запустить задачу в работу (перевод в 10046 и триггер)")
    start_parser.add_argument("issue_key", nargs="?", default=None, help="Ключ задачи (например, JS-41). Если не указан — берется первая задача из «К выполнению»")

    args = parser.parse_args()
    if args.command == "list" or not args.command:
        cmd_list(args)
    elif args.command == "start":
        cmd_start(args)
