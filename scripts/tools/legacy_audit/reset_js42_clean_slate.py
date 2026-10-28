import os
import requests
import json
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

JIRA_URL = (os.getenv("ATLASSIAN_BASE_URL") or "https://romeo-timony.atlassian.net").rstrip("/")
JIRA_EMAIL = os.getenv("ATLASSIAN_USER_EMAIL")
JIRA_TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
JIRA_AUTH = (JIRA_EMAIL, JIRA_TOKEN)

QASE_TOKEN = os.getenv("QASE_API_TOKEN") or os.getenv("QASE_TOKEN")
QASE_PROJECT = os.getenv("QASE_PROJECT_CODE", "JS")
QASE_URL = os.getenv("QASE_API_URL", "https://api.qase.io/v1")
QASE_HEADERS = {"Token": QASE_TOKEN, "Accept": "application/json"}

N8N_URL = os.getenv("N8N_URL", "http://201.34.147.33:5678").rstrip("/")
N8N_KEY = os.getenv("N8N_API_KEY")
N8N_HEADERS = {"X-N8N-API-KEY": N8N_KEY}

ISSUE_KEY = "JS-42"

print(f"=== 1. ОЧИСТКА КОММЕНТАРИЕВ И МЕТОК JIRA ДЛЯ {ISSUE_KEY} ===")
issue_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=JIRA_AUTH)
if issue_res.ok:
    issue_data = issue_res.json()
    comments = issue_data.get("fields", {}).get("comment", {}).get("comments", [])
    print(f"Найдено комментариев: {len(comments)}")
    for c in comments:
        cid = c.get("id")
        del_res = requests.delete(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment/{cid}", auth=JIRA_AUTH)
        print(f"   Удален комментарий {cid}: {del_res.status_code}")

    # Очистка меток и сохранение исходного summary
    clean_summary = "[E2E] Сквозная интеграция, приемочные сценарии и онбординг нового покупателя"
    update_payload = {
        "fields": {
            "labels": [],
            "summary": clean_summary
        }
    }
    up_res = requests.put(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=JIRA_AUTH, json=update_payload)
    print(f"Обновление меток и summary: {up_res.status_code}")

print(f"\n=== 2. ОЧИСТКА КЕЙСОВ В QASE TMS ДЛЯ СЬЮТА 88 (E2E) ===")
res = requests.get(f"{QASE_URL}/case/{QASE_PROJECT}?suite_id=88&limit=100", headers=QASE_HEADERS)
if res.ok:
    cases = res.json().get("result", {}).get("entities", [])
    print(f"Найдено кейсов в Suite 88: {len(cases)}")
    for c in cases:
        case_id = c.get("id")
        del_case = requests.delete(f"{QASE_URL}/case/{QASE_PROJECT}/{case_id}", headers=QASE_HEADERS)
        print(f"   Удален тест-кейс #{case_id}: {del_case.status_code}")

print(f"\n=== 3. ОСТАНОВКА ОЖИДАЮЩИХ И ЗАПУЩЕННЫХ ВОРКФЛОУ В N8N ===")
res = requests.get(f"{N8N_URL}/api/v1/executions?limit=20", headers=N8N_HEADERS)
if res.ok:
    for ex in res.json().get("data", []):
        eid = ex.get("id")
        status = ex.get("status")
        wfid = ex.get("workflowId")
        if wfid == "Dv1WydaTMC1lxR0E" and status in ("waiting", "running"):
            stop_res = requests.post(f"{N8N_URL}/api/v1/executions/{eid}/stop", headers=N8N_HEADERS)
            print(f"   Остановлен execution {eid} ({status}): {stop_res.status_code}")

print(f"\n=== 4. ОЧИСТКА ЛОКАЛЬНЫХ АРТЕФАКТОВ И ТЕСТОВ {ISSUE_KEY} ===")
review_dir = BASE_DIR / "tests" / "review"
if review_dir.exists():
    for f in review_dir.glob("*"):
        if f.is_file() and f.name != ".gitkeep":
            f.unlink()
            print(f"   Удален артефакт ревью: {f.name}")
        elif f.is_dir():
            shutil.rmtree(f)
            print(f"   Удалена подпапка ревью: {f.name}")

for target_dir in [BASE_DIR / "tests" / "frontend", BASE_DIR / "tests" / "ui", BASE_DIR / "tests" / "backend", BASE_DIR / "tests" / "e2e"]:
    if target_dir.exists():
        for f in target_dir.glob("*js42*.py"):
            f.unlink()
            print(f"   Удален сгенерированный тест: {f}")

print(f"\n=== 5. ПЕРЕВОД {ISSUE_KEY} В ИСХОДНЫЙ СТАТУС 10045 (К выполнению) ===")
trans_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=JIRA_AUTH)
if trans_res.ok:
    transitions = trans_res.json().get("transitions", [])
    print(f"Доступные переходы:")
    for t in transitions:
        print(f"   ID: {t.get('id')} | Name: {t.get('name')} | To: {t.get('to', {}).get('name')} ({t.get('to', {}).get('id')})")
    
    # Находим transition в 10045 ("К выполнению" / "To Do")
    target_transition = None
    for t in transitions:
        if str(t.get("to", {}).get("id")) == "10045" or "к выполнению" in t.get("name", "").lower() or "to do" in t.get("name", "").lower():
            target_transition = t.get("id")
            break

    if target_transition:
        post_tr = requests.post(
            f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions",
            auth=JIRA_AUTH,
            json={"transition": {"id": target_transition}}
        )
        print(f"Переход в 10045 выполнен: {post_tr.status_code}")
    else:
        print("⚠️ Не найден прямой переход в 10045!")

# Итоговая верификация
verify_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=JIRA_AUTH)
if verify_res.ok:
    vf = verify_res.json().get("fields", {})
    st = vf.get("status", {})
    print(f"\n✅ {ISSUE_KEY} готов к эталонному старту: статус {st.get('name')} ({st.get('id')}), комментариев: {len(vf.get('comment', {}).get('comments', []))}, метки: {vf.get('labels')}")
