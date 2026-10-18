import os
import sys
import json
import shutil
import sqlite3
from pathlib import Path
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

JIRA_URL = os.getenv("ATLASSIAN_BASE_URL")
JIRA_USER = os.getenv("ATLASSIAN_USER_EMAIL")
JIRA_TOKEN = os.getenv("ATLASSIAN_API_TOKEN")

QASE_URL = os.getenv("QASE_API_URL", "https://api.qase.io/v1")
QASE_TOKEN = os.getenv("QASE_API_TOKEN")

ISSUE_KEY = "JS-20"
DB_PATH = BASE_DIR / "data" / "qa_pipeline.db"
REVIEW_DIR = BASE_DIR / "tests" / "review"

auth = (JIRA_USER, JIRA_TOKEN)

def reset_jira():
    print(f"--- 1. Сброс Jira для {ISSUE_KEY} ---")
    
    # 1.1 Удаление всех комментариев
    res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth)
    if res.ok:
        comments = res.json().get('comments', [])
        print(f"Найдено комментариев для удаления: {len(comments)}")
        for c in comments:
            cid = c['id']
            del_res = requests.delete(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment/{cid}", auth=auth)
            if del_res.status_code in [200, 204]:
                print(f"  [x] Удален комментарий {cid}")
            else:
                print(f"  [!] Ошибка удаления комментария {cid}: {del_res.status_code}")
                
    # 1.2 Очистка меток и возврат чистого Summary
    res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth)
    if res.ok:
        data = res.json()
        current_summary = data.get('fields', {}).get('summary', '')
        labels = data.get('fields', {}).get('labels', [])
        
        # Очищаем summary от маркера DOR_OVERRIDE_APPROVED
        clean_summary = current_summary.replace(" [DOR_OVERRIDE_APPROVED]", "").replace("[DOR_OVERRIDE_APPROVED]", "").strip()
        
        qa_labels = [l for l in labels if l.startswith('qa-')]
        update_payload = {}
        fields_payload = {}
        
        if clean_summary != current_summary:
            fields_payload["summary"] = clean_summary
            print(f"  [*] Сброс Summary к: '{clean_summary}'")
            
        if qa_labels:
            update_payload["labels"] = [{"remove": l} for l in qa_labels]
            print(f"  [*] Удаление меток: {qa_labels}")
            
        req_body = {}
        if fields_payload:
            req_body["fields"] = fields_payload
        if update_payload:
            req_body["update"] = update_payload
            
        if req_body:
            put_res = requests.put(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth, json=req_body)
            if put_res.status_code in [200, 204]:
                print("  [x] Summary и метки успешно обновлены.")
            else:
                print(f"  [!] Ошибка обновления issue: {put_res.status_code} {put_res.text}")
                
    # 1.3 Удаление Remote Links от Qase
    links_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/remotelink", auth=auth)
    if links_res.ok:
        links = links_res.json()
        for link in links:
            app = link.get('application', {})
            obj = link.get('object', {})
            title = obj.get('title', '')
            link_id = link.get('id')
            if 'qase' in app.get('type', '').lower() or 'qase' in title.lower():
                del_link = requests.delete(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/remotelink/{link_id}", auth=auth)
                print(f"  [x] Удалена Qase Remote Link {link_id} ({title})")
                
    # 1.4 Перевод статуса в 'К выполнению' (To Do: 10045)
    trans_res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth)
    if trans_res.ok:
        transitions = trans_res.json().get('transitions', [])
        todo_trans = next((t['id'] for t in transitions if t.get('to', {}).get('id') == '10045' or t.get('to', {}).get('name') == 'К выполнению'), None)
        if todo_trans:
            t_res = requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth, json={"transition": {"id": todo_trans}})
            if t_res.status_code in [200, 204]:
                print(f"  [x] Задача {ISSUE_KEY} переведена в статус 'К выполнению' (ID перехода {todo_trans})")
            else:
                print(f"  [!] Ошибка смены статуса: {t_res.status_code} {t_res.text}")
        else:
            current_status = data.get('fields', {}).get('status', {}).get('name')
            print(f"  [*] Переход в 'К выполнению' не требуется или текущий статус: {current_status}")

def reset_db():
    print(f"--- 2. Сброс SQLite базы данных ---")
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        for table in ["pipeline_tasks", "pipeline_stages", "test_cases", "audit_reports", "autotest_files"]:
            try:
                cur.execute(f"DELETE FROM {table} WHERE issue_key = ?", (ISSUE_KEY,))
            except sqlite3.OperationalError:
                pass
        conn.commit()
        conn.close()
        print("  [x] Записи для JS-20 удалены из SQLite.")
    else:
        print("  [*] База данных SQLite не найдена.")

def reset_qase():
    print(f"--- 3. Сброс Qase TMS ---")
    headers = {"Token": QASE_TOKEN, "Accept": "application/json"}
    
    # 3.1 Поиск сьютов для JS-20
    suites_res = requests.get(f"{QASE_URL}/suite/JS?limit=100", headers=headers)
    suite_ids = []
    if suites_res.ok:
        suites = suites_res.json().get('result', {}).get('entities', [])
        for s in suites:
            if ISSUE_KEY in s.get('title', ''):
                suite_ids.append(s['id'])
                print(f"  [*] Найден сьют JS-20: ID {s['id']} '{s.get('title')}'")
                
    # 3.2 Получение всех кейсов и удаление относящихся к JS-20
    cases_res = requests.get(f"{QASE_URL}/case/JS?limit=100", headers=headers)
    if cases_res.ok:
        cases = cases_res.json().get('result', {}).get('entities', [])
        for c in cases:
            cid = c.get('id')
            c_suite = c.get('suite_id')
            if c_suite in suite_ids or ISSUE_KEY in c.get('title', ''):
                del_c = requests.delete(f"{QASE_URL}/case/JS/{cid}", headers=headers)
                if del_c.status_code in [200, 204]:
                    print(f"  [x] Удален тест-кейс Qase ID: {cid}")
                else:
                    print(f"  [!] Ошибка удаления тест-кейса {cid}: {del_c.status_code}")
                    
    # 3.3 Удаление сьютов
    for sid in suite_ids:
        del_s = requests.delete(f"{QASE_URL}/suite/JS/{sid}", headers=headers)
        if del_s.status_code in [200, 204]:
            print(f"  [x] Удален сьют Qase ID: {sid}")
        else:
            print(f"  [!] Ошибка удаления сьюта {sid}: {del_s.status_code}")

def reset_local_files():
    print(f"--- 4. Очистка локальных файлов стейджинга ---")
    if REVIEW_DIR.exists():
        for item in REVIEW_DIR.iterdir():
            if item.name.startswith(".git"):
                continue
            if item.is_file():
                item.unlink()
                print(f"  [x] Удален файл: {item.name}")
            elif item.is_dir():
                shutil.rmtree(item)
                print(f"  [x] Удалена папка: {item.name}")
        # Пересоздаем пустые папки
        (REVIEW_DIR / "backend").mkdir(exist_ok=True, parents=True)
        (REVIEW_DIR / "frontend").mkdir(exist_ok=True, parents=True)
        print("  [x] Папка tests/review сброшена к чистой структуре.")

if __name__ == "__main__":
    reset_qase()
    reset_db()
    reset_local_files()
    reset_jira()
    print("\n✅ Полная очистка JS-20 завершена! Задача готова к ручному запуску.")
