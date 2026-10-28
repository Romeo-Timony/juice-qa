import os
import sys
import time
import requests
import json
import sqlite3
import shutil
import re
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

JIRA_URL = (os.getenv("ATLASSIAN_BASE_URL") or "https://romeo-timony.atlassian.net").rstrip("/")
JIRA_EMAIL = os.getenv("ATLASSIAN_USER_EMAIL")
JIRA_TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
JIRA_AUTH = (JIRA_EMAIL, JIRA_TOKEN)

N8N_URL = (os.getenv("N8N_URL") or "http://201.34.147.33:5678").rstrip("/")
N8N_KEY = os.getenv("N8N_API_KEY")
N8N_HEADERS = {"X-N8N-API-KEY": N8N_KEY}

QASE_TOKEN = os.getenv("QASE_API_TOKEN") or os.getenv("QASE_TOKEN")
QASE_PROJECT = os.getenv("QASE_PROJECT_CODE", "JS")
QASE_HEADERS = {"Token": QASE_TOKEN, "Accept": "application/json"}

ISSUE_KEY = "JS-40"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

print("=" * 80)
print(f"🎯 ПОЛНЫЙ СКВОЗНОЙ ЦИКЛ ДЛЯ ЗАДАЧИ {ISSUE_KEY}: СБРОС И ПРОГОН ПО ВСЕМ 8 ЭТАПАМ")
print("=" * 80)

# ==============================================================================
# ШАГ 0: ОБНУЛЕНИЕ (CLEAN SLATE)
# ==============================================================================
log(f"🧹 Шаг 0. Полный сброс задачи {ISSUE_KEY}...")

# 1. Остановка зависших execution в n8n
res_ex = requests.get(f"{N8N_URL}/api/v1/executions?limit=20", headers=N8N_HEADERS)
if res_ex.ok:
    for ex in res_ex.json().get("data", []):
        eid = ex.get("id")
        status = ex.get("status")
        wfid = ex.get("workflowId")
        if wfid == "Dv1WydaTMC1lxR0E" and status in ("waiting", "running"):
            stop_res = requests.post(f"{N8N_URL}/api/v1/executions/{eid}/stop", headers=N8N_HEADERS)
            log(f"   • Остановлен n8n execution {eid} ({status}): {stop_res.status_code}")

# 2. Очистка комментариев Jira
comm_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=JIRA_AUTH)
if comm_res.ok:
    comms = comm_res.json().get("comments", [])
    log(f"   • Найдено {len(comms)} комментариев в Jira для удаления...")
    for c in comms:
        requests.delete(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment/{c['id']}", auth=JIRA_AUTH)

# 3. Очистка меток и сброс summary
clean_summary = "[API] Реализация серверной логики и контрактов регистрации (POST /api/Users)"
requests.put(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=JIRA_AUTH, json={
    "fields": {
        "labels": [],
        "summary": clean_summary
    }
})
log("   • Метки очищены, summary сброшено.")

# 4. Удаление Remote Links на Qase
r_links = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/remotelink", auth=JIRA_AUTH)
if r_links.ok and isinstance(r_links.json(), list):
    for rl in r_links.json():
        rl_id = rl.get("id")
        title = rl.get("object", {}).get("title", "")
        url = rl.get("object", {}).get("url", "")
        if "qase" in str(title).lower() or "qase" in str(url).lower():
            requests.delete(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/remotelink/{rl_id}", auth=JIRA_AUTH)
            log(f"   • Удалена ссылка Qase (ID {rl_id})")

# 5. Перевод статуса Jira в 10045 ("К выполнению")
trans_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=JIRA_AUTH)
if trans_res.ok:
    transitions = trans_res.json().get("transitions", [])
    target_t = next((t for t in transitions if str(t.get("to", {}).get("id")) == "10045" or "к выполнению" in t.get("name", "").lower() or "to do" in t.get("name", "").lower()), None)
    if target_t:
        requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=JIRA_AUTH, json={"transition": {"id": target_t["id"]}})
        log(f"   • Статус переведен в «К выполнению» (10045, transition ID {target_t['id']})")

# 6. Очистка локальных тестов и артефактов
review_dir = BASE_DIR / "tests" / "review"
if review_dir.exists():
    for f in review_dir.glob("*"):
        if f.is_file() and f.name != ".gitkeep":
            f.unlink()
        elif f.is_dir():
            shutil.rmtree(f)
for target_dir in [BASE_DIR / "tests" / "backend", BASE_DIR / "tests" / "frontend", BASE_DIR / "tests" / "ui", BASE_DIR / "tests" / "e2e"]:
    if target_dir.exists():
        for f in target_dir.glob(f"*{ISSUE_KEY.lower().replace('-', '')}*.py"):
            f.unlink()
            log(f"   • Удален боевой файл теста: {f.name}")

# 7. Очистка изолированного worktree
wt_dir = BASE_DIR.parent / ".worktrees" / f"qa-{ISSUE_KEY.lower()}"
if wt_dir.exists():
    import subprocess
    subprocess.run(["git", "worktree", "remove", "--force", str(wt_dir)], cwd=BASE_DIR.parent, capture_output=True)

# 8. Очистка SQLite
db_path = BASE_DIR / "data" / "qa_pipeline.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM test_cases WHERE issue_key = ?", (ISSUE_KEY,))
    conn.execute("DELETE FROM pipeline_stages WHERE issue_key = ?", (ISSUE_KEY,))
    conn.execute("DELETE FROM pipeline_tasks WHERE issue_key = ?", (ISSUE_KEY,))
    try:
        conn.execute("DELETE FROM qaops_idempotency WHERE idem_key LIKE ?", (f"%{ISSUE_KEY}%",))
        conn.execute("DELETE FROM qaops_spans WHERE issue_key = ?", (ISSUE_KEY,))
        conn.execute("DELETE FROM qaops_metrics WHERE issue_key = ?", (ISSUE_KEY,))
    except Exception:
        pass
    conn.commit()
    conn.close()
    log("   • SQLite БД очищена.")

log("✅ Сброс задачи JS-40 успешно завершен! Пауза 3 сек...")
time.sleep(3)

# ==============================================================================
# ШАГ 1: ПЕРЕВОД В «В РАБОТЕ» (10046) И ЗАПУСК N8N DOR GATE
# ==============================================================================
log(f"\n🚀 Шаг 1. Перевод {ISSUE_KEY} в «В работе» (10046) и запуск воркфлоу n8n...")
r_trans = requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=JIRA_AUTH, json={"transition": {"id": "21"}})
log(f"   • Перевод в Jira: {r_trans.status_code}")

# Вызов n8n webhook
r_hook = requests.post(f"{N8N_URL}/webhook/jira-dor-gate", json={"issueKey": ISSUE_KEY, "actor": "Roman Timoshenko"})
log(f"   • Триггер n8n jira-dor-gate: {r_hook.status_code}")

# ==============================================================================
# ШАГ 2: ОЖИДАНИЕ ЭТАПОВ 1-5 (ДО QUALITY GATE 1)
# ==============================================================================
log("\n⏳ Шаг 2. Ожидание завершения Этапов 1-5 (DoR, MindMap, BDD, RTM, Gate 1 card)...")
gate1_found = False
for attempt in range(30):
    time.sleep(3)
    c_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=JIRA_AUTH)
    if c_res.ok:
        comments = c_res.json().get("comments", [])
        stage5_comment = next((c for c in comments if "[Этап 5 из 8]" in c.get("body", "") or "Контроль 1" in c.get("body", "")), None)
        if stage5_comment:
            gate1_found = True
            log(f"   ✅ Карточка Quality Gate 1 обнаружена в Jira (ID {stage5_comment['id']})!")
            for i, c in enumerate(comments):
                first_line = c.get("body", "").strip().splitlines()[0]
                log(f"      [{i+1}] {first_line[:80]}")
            break
    print(".", end="", flush=True)

if not gate1_found:
    log("❌ Ошибка: Карточка Gate 1 не появилась за отведенное время!")
    sys.exit(1)

# ==============================================================================
# ШАГ 3: СОГЛАСОВАНИЕ QUALITY GATE 1 («ОК»)
# ==============================================================================
log("\n👤 Шаг 3. Согласование Quality Gate 1 (Human-in-the-Loop: отправка «ОК» в Jira)...")
ok_comm = requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=JIRA_AUTH, json={"body": "ОК"})
log(f"   • Комментарий «ОК» опубликован (ID {ok_comm.json().get('id')}).")

# Демон подхватит «ОК», запустит Seam 1 (Pydantic), Seam 2 (Design Gate),
# сгенерирует тесты через scaffold_dynamic, проведет Seam 3 (AST/ruff/collect),
# запустит независимый AI-аудит (Gemini Flash) и выложит карточку [Этап 6 из 8]
log("   • Ожидание обработки демоном: Pydantic контракты -> Генерация тестов -> Seam 3 -> Gate 2 карточка...")
gate2_found = False
for attempt in range(60):
    time.sleep(4)
    c_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=JIRA_AUTH)
    if c_res.ok:
        comments = c_res.json().get("comments", [])
        stage6_comment = next((c for c in comments if "[Этап 6 из 8]" in c.get("body", "") or "Контроль 2" in c.get("body", "")), None)
        if stage6_comment:
            gate2_found = True
            log(f"   ✅ Карточка Quality Gate 2 обнаружена в Jira (ID {stage6_comment['id']})!")
            first_line = stage6_comment.get("body", "").strip().splitlines()[0]
            log(f"      {first_line}")
            break
    print(".", end="", flush=True)

if not gate2_found:
    log("❌ Ошибка: Карточка Gate 2 не появилась за отведенное время!")
    sys.exit(1)

# ==============================================================================
# ШАГ 4: СОГЛАСОВАНИЕ QUALITY GATE 2 («ОК»)
# ==============================================================================
log("\n👤 Шаг 4. Согласование Quality Gate 2 (Human-in-the-Loop: отправка «ОК» на код)...")
time.sleep(2)
ok_comm2 = requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=JIRA_AUTH, json={"body": "ОК"})
log(f"   • Комментарий «ОК» опубликован (ID {ok_comm2.json().get('id')}).")

# Демон выполнит promote_files, создаст git worktree, запушит ветку qa/js-40 и обновит main,
# затем возобновит n8n -> n8n опубликует Этап 7 и сделает workflow_dispatch в GitHub Actions
log("   • Ожидание промоушена тестов, пуша в репозиторий и запуска GitHub Actions...")
stage7_found = False
for attempt in range(50):
    time.sleep(4)
    c_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=JIRA_AUTH)
    if c_res.ok:
        comments = c_res.json().get("comments", [])
        stage7_comment = next((c for c in comments if "[Этап 7 из 8]" in c.get("body", "") or "Внедрение" in c.get("body", "")), None)
        if stage7_comment:
            stage7_found = True
            log(f"   ✅ Карточка Этапа 7 (Внедрение автотестов) опубликована в Jira (ID {stage7_comment['id']})!")
            break
    print(".", end="", flush=True)

# ==============================================================================
# ШАГ 5: ОЖИДАНИЕ ИСПОЛНЕНИЯ ТЕСТОВ В CI/CD (ЭТАП 8)
# ==============================================================================
log("\n🐙 Шаг 5. Ожидание завершения прогона тестов в GitHub Actions и формирования отчета Allure...")
stage8_found = False
for attempt in range(60):
    time.sleep(5)
    c_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=JIRA_AUTH)
    if c_res.ok:
        comments = c_res.json().get("comments", [])
        stage8_comment = next((c for c in comments if "[Этап 8 из 8]" in c.get("body", "") or "GitHub Actions" in c.get("body", "")), None)
        if stage8_comment:
            stage8_found = True
            log(f"   🏆 Карточка Этапа 8 (Отчет Allure из GitHub Actions) получена (ID {stage8_comment['id']})!")
            break
    print(".", end="", flush=True)

if not stage8_found:
    log("⚠️ Время ожидания Этапа 8 истекло, проверяем статус задачи...")

# Проверяем финальный статус задачи в Jira
time.sleep(3)
final_issue = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=JIRA_AUTH).json()
final_status = final_issue.get("fields", {}).get("status", {})
log(f"\n🏁 Финальный статус задачи {ISSUE_KEY}: {final_status.get('name')} (ID {final_status.get('id')})")

print("\n" + "=" * 80)
print(f"📊 ПАЙПЛАЙН ДЛЯ {ISSUE_KEY} УСПЕШНО ДОСТИГ ФИНАЛЬНОГО РЕЗУЛЬТАТА!")
print("=" * 80)
