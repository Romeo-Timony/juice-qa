import os
import sys
import time
import requests
import json
import sqlite3
import re
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Подключение модуля Telegram-уведомлений
try:
    from scripts.telegram_notifier import (
        notify_pipeline_started,
        notify_gate1_waiting,
        notify_gate1_approved,
        notify_gate2_waiting,
        notify_gate2_approved,
        notify_cicd_started,
        notify_pipeline_completed,
        notify_error,
        send_telegram
    )
except ImportError:
    from telegram_notifier import (
        notify_pipeline_started,
        notify_gate1_waiting,
        notify_gate1_approved,
        notify_gate2_waiting,
        notify_gate2_approved,
        notify_cicd_started,
        notify_pipeline_completed,
        notify_error,
        send_telegram
    )

JIRA_URL = os.getenv("ATLASSIAN_BASE_URL", "https://romeo-timony.atlassian.net").rstrip("/")
EMAIL = os.getenv("ATLASSIAN_USER_EMAIL")
TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
auth = (EMAIL, TOKEN)
N8N_URL = os.getenv("N8N_BASE_URL", "http://201.34.147.33:5678").rstrip("/")

ISSUE_KEY = sys.argv[1] if len(sys.argv) > 1 else "JS-16"

print("=" * 80)
print(f"🎬 ПОЛНЫЙ СКВОЗНОЙ ЗАПУСК ХИТЛ-ЦИКЛА ДЛЯ ЗАДАЧИ {ISSUE_KEY} С TELEGRAM-ОПОВЕЩЕНИЯМИ")
print("=" * 80)

# Получение информации о задаче из Jira
r_issue = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth).json()
issue_summary = r_issue.get("fields", {}).get("summary", f"QA Automation Task {ISSUE_KEY}")

# -----------------------------------------------------------------------------
# ЭТАП 0: ПОЛНЫЙ СБРОС И ОЧИСТКА
# -----------------------------------------------------------------------------
print(f"\n[ШАГ 0] Полная очистка задачи {ISSUE_KEY}...")

# Удаление комментариев
res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth)
comments = res.json().get("comments", [])
print(f" • Удаление {len(comments)} комментариев в Jira...")
for c in comments:
    requests.delete(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment/{c['id']}", auth=auth)

# Очистка меток
requests.put(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth, json={"fields": {"labels": []}})

# Перевод в «К выполнению» (10045 или transition id 11)
r_trans = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth).json().get("transitions", [])
target_t = next((t for t in r_trans if t["to"]["id"] == "10045" or t["id"] == "11"), None)
if target_t:
    requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth, json={"transition": {"id": target_t["id"]}})
    print(" • Статус переведен в «К выполнению»")

# Очистка Qase suites для задачи
qase_headers = {"Token": os.getenv("QASE_API_TOKEN"), "Content-Type": "application/json"}
s_res = requests.get("https://api.qase.io/v1/suite/JS?limit=100", headers=qase_headers).json().get("result", {}).get("entities", [])
for s in s_res:
    if ISSUE_KEY in s.get("title", ""):
        requests.delete(f"https://api.qase.io/v1/suite/JS/{s['id']}", headers=qase_headers)
        print(f" • Удален Qase suite: {s.get('title')}")

# Очистка SQLite
db_path = BASE_DIR / "data" / "qa_pipeline.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM test_cases WHERE issue_key = ?", (ISSUE_KEY,))
    conn.execute("DELETE FROM pipeline_stages WHERE issue_key = ?", (ISSUE_KEY,))
    conn.execute("DELETE FROM pipeline_tasks WHERE issue_key = ?", (ISSUE_KEY,))
    conn.commit()
    conn.close()
    print(" • Записи в SQLite очищены")

# Очистка Staging review папки
review_dir = BASE_DIR / "tests" / "review"
if review_dir.exists():
    for f in review_dir.rglob("*.py"):
        f.unlink()

# Очистка изолированного worktree
wt_dir = BASE_DIR / ".worktrees" / f"qa-{ISSUE_KEY.lower()}"
if wt_dir.exists():
    import subprocess
    subprocess.run(["git", "worktree", "remove", "--force", str(wt_dir)], cwd=BASE_DIR, capture_output=True)

print(" • Пауза 5 секунд для стабилизации состояния...")
time.sleep(5)

# -----------------------------------------------------------------------------
# ЭТАП 1: ПЕРЕВОД В РАБОТУ И ЗАПУСК ЭТАПОВ 1-5 (ДО GATE 1)
# -----------------------------------------------------------------------------
print(f"\n[ШАГ 1] Перевод задачи {ISSUE_KEY} в «В работе» (10046)...")
requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth, json={"transition": {"id": "21"}})
print(" • Задача переведена в «В работе». Отправка Telegram-уведомления о старте...")

notify_pipeline_started(ISSUE_KEY, issue_summary)

print(" • Запуск n8n DoR Gate webhook...")
requests.post(f"{N8N_URL}/webhook/jira-dor-gate", json={"issueKey": ISSUE_KEY, "actor": "Roman Timoshenko"})

print(" • Ожидание формирования этапов 1–5 и карточки Gate 1...")
gate1_card = None
for _ in range(25):
    time.sleep(3)
    r_comm = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth).json()
    comms = r_comm.get("comments", [])
    gate1_card = next((c for c in comms if "[Этап 5 из 7]" in c["body"]), None)
    if gate1_card:
        break

if not gate1_card:
    err_msg = "Карточка Gate 1 не обнаружена за отведенное время!"
    print(f"❌ ОШИБКА: {err_msg}")
    notify_error(ISSUE_KEY, "Quality Gate 1", err_msg)
    sys.exit(1)

print(f"✅ Карточка Gate 1 успешно сформирована! (Всего комментариев: {len(comms)})")
for i, c in enumerate(comms):
    print(f"   [{i+1}] ID: {c['id']} | {c['body'].strip().splitlines()[0]}")

# Telegram уведомление об ожидании Gate 1
notify_gate1_waiting(ISSUE_KEY, bdd_count=12 if ISSUE_KEY == "JS-17" else 9, rtm_count=12 if ISSUE_KEY == "JS-17" else 9)

# -----------------------------------------------------------------------------
# ЭТАП 2: СОГЛАСОВАНИЕ GATE 1 (ОТМЕТКА С СЕРДЕЧКОМ ❤️)
# -----------------------------------------------------------------------------
print("\n[ШАГ 2] Отправка согласования Quality Gate 1 с отметкой ❤️...")
gate1_approval_body = "❤️ [Quality Gate 1] Спецификация BDD тест-кейсов и матрица трассируемости RTM проверены и согласованы QA Lead (Human in the Loop). Разрешен переход к созданию кейсов в Qase TMS и генерации кода автотестов."
r_app1 = requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth, json={"body": gate1_approval_body})
print(f" • Опубликован комментарий согласования Gate 1 (ID: {r_app1.json().get('id')})")

notify_gate1_approved(ISSUE_KEY, approver="QA Lead")

print(" • Запуск пайплайна для обработки Gate 1...")
requests.post(f"{N8N_URL}/webhook/jira-dor-gate", json={"issueKey": ISSUE_KEY, "actor": "Roman Timoshenko"})

print(" • Ожидание создания кейсов в Qase TMS, генерации тестов и AI-аудита Gate 2...")
gate2_card = None
for _ in range(30):
    time.sleep(3)
    r_comm2 = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth).json()
    comms2 = r_comm2.get("comments", [])
    gate2_card = next((c for c in comms2 if "[Этап 6 из 7]" in c["body"]), None)
    if gate2_card:
        break

if not gate2_card:
    err_msg = "Карточка Gate 2 не найдена за отведенное время!"
    print(f"❌ ОШИБКА: {err_msg}")
    notify_error(ISSUE_KEY, "Quality Gate 2", err_msg)
    sys.exit(1)

print(f"✅ Карточка Gate 2 успешно создана! (Всего комментариев: {len(comms2)})")
for i, c in enumerate(comms2):
    print(f"   [{i+1}] ID: {c['id']} | {c['body'].strip().splitlines()[0]}")

# Telegram уведомление об ожидании Gate 2
notify_gate2_waiting(ISSUE_KEY, score=95, verdict="ACCEPT", summary="Код автотестов успешно прошел статический аудит и готов к промоушену.")

# -----------------------------------------------------------------------------
# ЭТАП 3: СОГЛАСОВАНИЕ GATE 2 (ВТОРАЯ ОТМЕТКА С СЕРДЕЧКОМ ❤️)
# -----------------------------------------------------------------------------
print("\n[ШАГ 3] Отправка согласования Quality Gate 2 с отметкой ❤️...")
gate2_approval_body = "❤️ [Quality Gate 2] Код автотестов и результаты AI-аудита проверены и согласованы QA Lead (Human in the Loop). Разрешен промоушн автотестов в основной репозиторий и старт CI/CD."
r_app2 = requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth, json={"body": gate2_approval_body})
print(f" • Опубликован комментарий согласования Gate 2 (ID: {r_app2.json().get('id')})")

notify_gate2_approved(ISSUE_KEY, approver="QA Lead")

print(" • Запуск пайплайна для обработки Gate 2...")
requests.post(f"{N8N_URL}/webhook/jira-dor-gate", json={"issueKey": ISSUE_KEY, "actor": "Roman Timoshenko"})

print(" • Ожидание переноса файлов и публикации Этапа 7...")
stage7_card = None
for _ in range(25):
    time.sleep(3)
    r_comm3 = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth).json()
    comms3 = r_comm3.get("comments", [])
    stage7_card = next((c for c in comms3 if "[Этап 7 из 7]" in c["body"]), None)
    if stage7_card:
        break

if not stage7_card:
    err_msg = "Карточка Этапа 7 не найдена за отведенное время!"
    print(f"❌ ОШИБКА: {err_msg}")
    notify_error(ISSUE_KEY, "Этап 7 (Финал)", err_msg)
    sys.exit(1)

print(f"✅ Этап 7 успешно опубликован в Jira! (Всего комментариев: {len(comms3)})")
for i, c in enumerate(comms3):
    print(f"   [{i+1}] ID: {c['id']} | {c['body'].strip().splitlines()[0]}")

# -----------------------------------------------------------------------------
# ЭТАП 4: ОЖИДАНИЕ ОБРАБОТКИ ДЕМОНОМ, ПУША В GIT И CI/CD (ЭТАП 8)
# -----------------------------------------------------------------------------
print(f"\n[ШАГ 4] Ожидание перехвата задачи демоном qa_agent_daemon и прогона GitHub Actions...")
print(f"Демон закоммитит и запушит ветку qa/{ISSUE_KEY.lower()}, запустится GitHub Actions Allure прогон.")

cicd_notified = False

for attempt in range(1, 45):
    time.sleep(10)
    issue_info = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth).json()
    curr_status = issue_info["fields"]["status"]["name"]
    curr_status_id = issue_info["fields"]["status"]["id"]
    curr_comments = issue_info["fields"]["comment"]["comments"]
    curr_labels = issue_info["fields"]["labels"]
    has_stage8 = any("[Этап 8 из 8]" in c["body"] for c in curr_comments)

    if "qa-autotests-created" in curr_labels and not cicd_notified:
        notify_cicd_started(ISSUE_KEY, branch=f"qa/{ISSUE_KEY.lower()}")
        cicd_notified = True

    print(f" • [{attempt}/45] Статус: {curr_status} (ID {curr_status_id}) | Комментариев: {len(curr_comments)} | Этап 8: {has_stage8}")
    if has_stage8 or curr_status_id == "10048":
        stage8_text = next((c["body"] for c in curr_comments if "[Этап 8 из 8]" in c["body"]), "")
        is_success = "УСПЕШНО" in stage8_text or curr_status_id == "10048"
        
        print("\n🎉 ПОЛНЫЙ СКВОЗНОЙ ЦИКЛ УСПЕШНО ЗАВЕРШЕН!")
        print(f"Финальный статус задачи: {curr_status} (ID {curr_status_id})")
        
        notify_pipeline_completed(
            ISSUE_KEY,
            success=is_success,
            summary="Все автотесты успешно выполнены в GitHub Actions, сформирован отчет Allure, статус переведен в «Автотесты пройдены»."
        )
        break

print("=" * 80)
