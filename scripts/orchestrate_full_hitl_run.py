import os
import sys
import time
import requests
import json
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

JIRA_URL = os.getenv("ATLASSIAN_BASE_URL", "https://romeo-timony.atlassian.net").rstrip("/")
EMAIL = os.getenv("ATLASSIAN_USER_EMAIL")
TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
auth = (EMAIL, TOKEN)
N8N_URL = os.getenv("N8N_BASE_URL", "http://201.34.147.33:5678").rstrip("/")
N8N_KEY = os.getenv("N8N_API_KEY")

ISSUE_KEY = "JS-17"

print("=" * 80)
print(f"🎬 ПОЛНЫЙ СКВОЗНОЙ ЗАПУСК ХИТЛ-ЦИКЛА ДЛЯ ЗАДАЧИ {ISSUE_KEY}")
print("=" * 80)

# -----------------------------------------------------------------------------
# ЭТАП 0: ПОЛНЫЙ СБРОС И ОЧИСТКА
# -----------------------------------------------------------------------------
print("\n[ШАГ 0] Полная очистка задачи JS-17...")

# Удаление комментариев
res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth)
comments = res.json().get("comments", [])
print(f" • Удаление {len(comments)} комментариев...")
for c in comments:
    requests.delete(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment/{c['id']}", auth=auth)

# Очистка меток
requests.put(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth, json={"fields": {"labels": []}})

# Перевод в «К выполнению» (10045)
r_trans = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth).json().get("transitions", [])
target_t = next((t for t in r_trans if t["to"]["id"] == "10045" or t["id"] == "11"), None)
if target_t:
    requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth, json={"transition": {"id": target_t["id"]}})

# Очистка Qase
qase_headers = {"Token": os.getenv("QASE_API_TOKEN"), "Content-Type": "application/json"}
s_res = requests.get(f"https://api.qase.io/v1/suite/JS?limit=100", headers=qase_headers).json().get("result", {}).get("entities", [])
for s in s_res:
    if ISSUE_KEY in s.get("title", ""):
        requests.delete(f"https://api.qase.io/v1/suite/JS/{s['id']}", headers=qase_headers)

# Очистка SQLite и Review
db_path = BASE_DIR / "data" / "qa_pipeline.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM test_cases WHERE issue_key = ?", (ISSUE_KEY,))
    conn.execute("DELETE FROM pipeline_stages WHERE issue_key = ?", (ISSUE_KEY,))
    conn.execute("DELETE FROM pipeline_tasks WHERE issue_key = ?", (ISSUE_KEY,))
    conn.commit()
    conn.close()

review_dir = BASE_DIR / "tests" / "review"
if review_dir.exists():
    for f in review_dir.rglob("*.py"):
        f.unlink()

print(" • Пауза 5 секунд для стабилизации состояния...")
time.sleep(5)

# -----------------------------------------------------------------------------
# ЭТАП 1: ПЕРЕВОД В РАБОТУ И ЗАПУСК ЭТАПОВ 1-5 (ДО GATE 1)
# -----------------------------------------------------------------------------
print("\n[ШАГ 1] Перевод задачи в «В работе» (10046)...")
requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth, json={"transition": {"id": "21"}})
print(" • Задача переведена в «В работе». Запуск n8n DoR Gate...")

requests.post(f"{N8N_URL}/webhook/jira-dor-gate", json={"issueKey": ISSUE_KEY, "actor": "Roman Timoshenko"})

print(" • Ожидание формирования этапов 1–5 (30 секунд)...")
time.sleep(30)

r_comm = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth).json()
comms = r_comm.get("comments", [])
print(f"📊 Текущее количество комментариев: {len(comms)}")
for i, c in enumerate(comms):
    print(f"   [{i+1}] ID: {c['id']} | {c['body'].strip().splitlines()[0]}")

gate1_card = next((c for c in comms if "[Этап 5 из 7]" in c["body"]), None)
if not gate1_card:
    print("❌ ОШИБКА: Карточка Gate 1 не обнаружена!")
    sys.exit(1)
print("✅ Карточка Gate 1 успешно сформирована и ожидает согласования.")

# -----------------------------------------------------------------------------
# ЭТАП 2: СОГЛАСОВАНИЕ GATE 1 (ОТМЕТКА С СЕРДЕЧКОМ ❤️)
# -----------------------------------------------------------------------------
print("\n[ШАГ 2] Отправка согласования Quality Gate 1 с отметкой ❤️...")
gate1_approval_body = "❤️ [Quality Gate 1] Спецификация BDD тест-кейсов и матрица трассируемости RTM проверены и согласованы QA Lead (Human in the Loop). Разрешен переход к созданию кейсов в Qase TMS и генерации кода автотестов."
r_app1 = requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth, json={"body": gate1_approval_body})
print(f" • Опубликован комментарий согласования Gate 1 (ID: {r_app1.json().get('id')})")

print(" • Запуск пайплайна для обработки Gate 1...")
requests.post(f"{N8N_URL}/webhook/jira-dor-gate", json={"issueKey": ISSUE_KEY, "actor": "Roman Timoshenko"})

print(" • Ожидание создания кейсов в Qase TMS, генерации тестов и AI-аудита Gate 2 (35 секунд)...")
time.sleep(35)

r_comm2 = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth).json()
comms2 = r_comm2.get("comments", [])
print(f"\n📊 Комментариев после согласования Gate 1: {len(comms2)}")
for i, c in enumerate(comms2):
    print(f"   [{i+1}] ID: {c['id']} | {c['body'].strip().splitlines()[0]}")

gate2_card = next((c for c in comms2 if "[Этап 6 из 7]" in c["body"]), None)
if not gate2_card:
    print("❌ ОШИБКА: Карточка Gate 2 не найдена!")
    sys.exit(1)
print("✅ Карточка Gate 2 успешно создана! Пайплайн остановился на остановке Quality Gate 2.")

# -----------------------------------------------------------------------------
# ЭТАП 3: СОГЛАСОВАНИЕ GATE 2 (ВТОРАЯ ОТМЕТКА С СЕРДЕЧКОМ ❤️)
# -----------------------------------------------------------------------------
print("\n[ШАГ 3] Отправка согласования Quality Gate 2 с отметкой ❤️...")
gate2_approval_body = "❤️ [Quality Gate 2] Код автотестов и результаты AI-аудита проверены и согласованы QA Lead (Human in the Loop). Разрешен промоушн автотестов в основной репозиторий и старт CI/CD."
r_app2 = requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth, json={"body": gate2_approval_body})
print(f" • Опубликован комментарий согласования Gate 2 (ID: {r_app2.json().get('id')})")

print(" • Запуск пайплайна для обработки Gate 2...")
requests.post(f"{N8N_URL}/webhook/jira-dor-gate", json={"issueKey": ISSUE_KEY, "actor": "Roman Timoshenko"})

print(" • Ожидание переноса файлов и публикации Этапа 7 (20 секунд)...")
time.sleep(20)

r_comm3 = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth).json()
comms3 = r_comm3.get("comments", [])
print(f"\n📊 Комментариев после согласования Gate 2: {len(comms3)}")
for i, c in enumerate(comms3):
    print(f"   [{i+1}] ID: {c['id']} | {c['body'].strip().splitlines()[0]}")

stage7_card = next((c for c in comms3 if "[Этап 7 из 7]" in c["body"]), None)
if not stage7_card:
    print("❌ ОШИБКА: Карточка Этапа 7 не найдена!")
    sys.exit(1)
print("✅ Этап 7 успешно опубликован в Jira!")

# -----------------------------------------------------------------------------
# ЭТАП 4: ОЖИДАНИЕ ОБРАБОТКИ ДЕМОНОМ, ПУША В GIT И CI/CD (ЭТАП 8)
# -----------------------------------------------------------------------------
print("\n[ШАГ 4] Ожидание перехвата задачи демоном qa_agent_daemon и прогона GitHub Actions...")
print("Демон закоммитит и запушит ветку qa/js-17, запустится GitHub Actions Allure прогон.")

for attempt in range(1, 25):
    print(f" • Проверка статуса в Jira (попытка {attempt}/24, ожидание 10 сек)...")
    time.sleep(10)
    issue_info = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth).json()
    curr_status = issue_info["fields"]["status"]["name"]
    curr_status_id = issue_info["fields"]["status"]["id"]
    curr_comments = issue_info["fields"]["comment"]["comments"]
    has_stage8 = any("[Этап 8 из 8]" in c["body"] for c in curr_comments)

    print(f"   Статус задачи: {curr_status} (ID {curr_status_id}) | Этап 8 опубликован: {has_stage8}")
    if has_stage8 or curr_status_id == "10048":
        print("\n🎉 ПОЛНЫЙ СКВОЗНОЙ ЦИКЛ УСПЕШНО ЗАВЕРШЕН!")
        print(f"Текущий статус задачи: {curr_status}")
        break

print("=" * 80)
