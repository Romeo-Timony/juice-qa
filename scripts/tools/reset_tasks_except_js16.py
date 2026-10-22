import os
import re
import sys
import glob
import shutil
import sqlite3
import requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

JIRA_URL = (os.getenv("ATLASSIAN_BASE_URL") or "https://romeo-timony.atlassian.net").rstrip('/')
JIRA_EMAIL = os.getenv("ATLASSIAN_USER_EMAIL")
JIRA_TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
QASE_TOKEN = os.getenv("QASE_API_TOKEN")
QASE_PROJECT = os.getenv("QASE_PROJECT_CODE", "JS")

jira_auth = (JIRA_EMAIL, JIRA_TOKEN)
qase_headers = {"Token": QASE_TOKEN, "Content-Type": "application/json"}

print("================================================================================")
print("🧹 СБРОС И ОБНУЛЕНИЕ ВСЕХ ЗАДАЧ В ДЕФОЛТНОЕ СОСТОЯНИЕ (КРОМЕ JS-16)")
print("================================================================================")

# ----------------------------------------------------------------------
# 1. СБРОС JIRA ЗАДАЧ (JS-17, JS-19, JS-20 и любых других, кроме JS-16)
# ----------------------------------------------------------------------
print("\n--- 1. Сброс задач в Jira ---")
target_issues = ["JS-17", "JS-19", "JS-20"]

for key in target_issues:
    print(f"\n[JIRA] Обработка задачи {key}...")
    
    # 1.1 Удаление комментариев
    c_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{key}/comment", auth=jira_auth)
    if c_res.ok:
        comments = c_res.json().get("comments", [])
        print(f"   • Найдено {len(comments)} комментариев. Удаление...")
        for c in comments:
            cid = c["id"]
            del_r = requests.delete(f"{JIRA_URL}/rest/api/2/issue/{key}/comment/{cid}", auth=jira_auth)
            print(f"     - Удален комментарий {cid} (HTTP {del_r.status_code})")
    
    # 1.2 Очистка remote links (ссылок на Qase и т.п.)
    rl_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{key}/remotelink", auth=jira_auth)
    if rl_res.ok and isinstance(rl_res.json(), list):
        for rl in rl_res.json():
            rl_id = rl.get("id")
            title = rl.get("object", {}).get("title", "")
            url = rl.get("object", {}).get("url", "")
            if any(term in str(x).lower() for term in ["qase", "test", "allure"] for x in [title, url]):
                requests.delete(f"{JIRA_URL}/rest/api/2/issue/{key}/remotelink/{rl_id}", auth=jira_auth)
                print(f"     - Удалена внешняя ссылка {rl_id} ({title})")
                
    # 1.3 Очистка меток (labels) и очистка [DOR_OVERRIDE_APPROVED] из summary
    iss_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{key}", auth=jira_auth)
    if iss_res.ok:
        fields = iss_res.json().get("fields", {})
        summary = fields.get("summary", "")
        cleaned_summary = re.sub(r"\s*\[DOR_OVERRIDE_APPROVED\]", "", summary).strip()
        
        update_payload = {
            "fields": {
                "labels": [],
                "summary": cleaned_summary
            }
        }
        u_res = requests.put(f"{JIRA_URL}/rest/api/2/issue/{key}", auth=jira_auth, json=update_payload)
        print(f"   • Метки очищены, summary обновлен: '{cleaned_summary}' (HTTP {u_res.status_code})")

    # 1.4 Сброс статуса на «К выполнению» (Status ID 10045)
    trans_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{key}/transitions", auth=jira_auth)
    if trans_res.ok:
        transitions = trans_res.json().get("transitions", [])
        target_trans = next((t for t in transitions if t["to"]["id"] == "10045" or t["id"] == "11" or "к выполнению" in t["name"].lower()), None)
        if target_trans:
            post_t = requests.post(f"{JIRA_URL}/rest/api/2/issue/{key}/transitions", auth=jira_auth, json={"transition": {"id": target_trans["id"]}})
            print(f"   • Переход в статус 'К выполнению' через '{target_trans['name']}' (ID {target_trans['id']}): HTTP {post_t.status_code}")
        else:
            current_status = fields.get("status", {}).get("name")
            print(f"   ℹ️ Переход в 10045 не найден (текущий статус: {current_status})")

# ----------------------------------------------------------------------
# 2. ОЧИСТКА В QASE TMS (КРОМЕ СЬЮТОВ И КЕЙСОВ ДЛЯ JS-16)
# ----------------------------------------------------------------------
print("\n--- 2. Очистка Qase TMS ---")
# Получаем все сьюты
s_res = requests.get(f"https://api.qase.io/v1/suite/{QASE_PROJECT}?limit=100", headers=qase_headers)
if s_res.ok:
    suites = s_res.json().get("result", {}).get("entities", [])
    for s in suites:
        sid = s["id"]
        title = s.get("title", "")
        # Оставляем корневые Frontend (71), Backend (73), и сьют JS-16 (72)
        if "JS-16" in title or sid in [71, 72, 73]:
            print(f"   🔒 Сохраняем сьют #{sid} «{title}»")
            continue
        print(f"   🗑️ Удаляем нежелательный сьют #{sid} «{title}»...")
        del_s = requests.delete(f"https://api.qase.io/v1/suite/{QASE_PROJECT}/{sid}", headers=qase_headers)
        print(f"     - Результат: HTTP {del_s.status_code}")

# Проверяем оставшиеся кейсы: если кейс не принадлежит сьюту JS-16 (id 72), удаляем его
c_res = requests.get(f"https://api.qase.io/v1/case/{QASE_PROJECT}?limit=100", headers=qase_headers)
if c_res.ok:
    cases = c_res.json().get("result", {}).get("entities", [])
    for c in cases:
        cid = c["id"]
        suite_id = c.get("suite_id")
        title = c.get("title", "")
        if suite_id == 72 or "JS-16" in title or cid in range(532, 546):
            # Сохраняем кейсы JS-16
            continue
        print(f"   🗑️ Удаляем посторонний тест-кейс #{cid} «{title}» (Suite #{suite_id})...")
        del_c = requests.delete(f"https://api.qase.io/v1/case/{QASE_PROJECT}/{cid}", headers=qase_headers)
        print(f"     - Результат: HTTP {del_c.status_code}")

# ----------------------------------------------------------------------
# 3. ОЧИСТКА ЛОКАЛЬНЫХ ТЕСТОВЫХ ФАЙЛОВ И STAGING
# ----------------------------------------------------------------------
print("\n--- 3. Очистка локальных файлов тестов и Staging ---")
# Очистка staging папки tests/review
review_dir = BASE_DIR / "tests" / "review"
if review_dir.exists():
    for f in review_dir.rglob("*"):
        if f.is_file():
            f.unlink()
            print(f"   • Удален staging файл: {f.relative_to(BASE_DIR)}")
    for sub in list(review_dir.glob("*")):
        if sub.is_dir():
            shutil.rmtree(sub)

# Очистка любых не-JS16 файлов в backend и frontend
for pattern in ["tests/backend/test_js1[7-9]*.py", "tests/backend/test_js2*.py", "tests/frontend/test_js1[7-9]*.py", "tests/frontend/test_js2*.py"]:
    for f in BASE_DIR.glob(pattern):
        f.unlink()
        print(f"   • Удален тестовый файл: {f.relative_to(BASE_DIR)}")

# Убеждаемся, что test_js16_ui.py цел
js16_file = BASE_DIR / "tests" / "frontend" / "test_js16_ui.py"
if js16_file.exists():
    print(f"   ✅ Эталонный файл автотестов JS-16 сохранен: {js16_file.relative_to(BASE_DIR)}")
else:
    print(f"   ⚠️ ВНИМАНИЕ: {js16_file} не найден!")

# ----------------------------------------------------------------------
# 4. ОЧИСТКА SQLITE БАЗЫ ДАННЫХ (data/qa_pipeline.db)
# ----------------------------------------------------------------------
print("\n--- 4. Очистка SQLite qa_pipeline.db ---")
db_path = BASE_DIR / "data" / "qa_pipeline.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Очищаем pipeline_tasks, pipeline_stages, test_cases, autotest_files, audit_reports для задач кроме JS-16
    for tbl in ["pipeline_tasks", "pipeline_stages", "test_cases", "autotest_files", "audit_reports"]:
        cur.execute(f"DELETE FROM {tbl} WHERE issue_key != 'JS-16'")
        print(f"   • Очищена таблица {tbl} (оставлены только записи для JS-16)")
        
    # Очищаем qaops_idempotency от записей не JS-16
    cur.execute("DELETE FROM qaops_idempotency WHERE idem_key NOT LIKE '%JS-16%'")
    print("   • Очищена таблица qaops_idempotency")
    
    conn.commit()
    conn.close()

# ----------------------------------------------------------------------
# 5. СИНХРОНИЗАЦИЯ N8N DATA TABLES
# ----------------------------------------------------------------------
print("\n--- 5. Синхронизация n8n Data Tables ---")
try:
    sys.path.insert(0, str(BASE_DIR))
    from scripts.n8n_tables import sync_all_to_n8n
    sync_all_to_n8n()
    print("   ✅ n8n Data Tables успешно синхронизированы с актуальным состоянием базы.")
except Exception as e:
    print(f"   ⚠️ Ошибка синхронизации с n8n: {e}")

print("\n================================================================================")
print("✨ ОБНУЛЕНИЕ ЗАВЕРШЕНО: ВСЕ ЗАДАЧИ В ИСХОДНОМ СОСТОЯНИИ, JS-16 СОХРАНЕНА!")
print("================================================================================")
