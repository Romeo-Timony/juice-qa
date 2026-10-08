import os
import requests
import sqlite3
from dotenv import load_dotenv

load_dotenv(r"d:\Desktop\Juice_shop\qa-automation\.env")

JIRA_URL = os.getenv("ATLASSIAN_BASE_URL")
JIRA_USER = os.getenv("ATLASSIAN_USER_EMAIL")
JIRA_TOKEN = os.getenv("ATLASSIAN_API_TOKEN")

QASE_URL = os.getenv("QASE_API_URL")
QASE_TOKEN = os.getenv("QASE_API_TOKEN")

ISSUE_KEY = "JS-22"
DB_PATH = r"d:\Desktop\Juice_shop\qa-automation\data\qa_pipeline.db"

def reset_jira():
    print(f"--- Сброс Jira для {ISSUE_KEY} ---")
    auth = (JIRA_USER, JIRA_TOKEN)
    
    # 1. Удаление комментариев
    res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth)
    if res.ok:
        comments = res.json().get('comments', [])
        for c in comments:
            cid = c['id']
            requests.delete(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment/{cid}", auth=auth)
            print(f"Удален комментарий {cid}")
            
    # 2. Удаление меток
    res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth)
    if res.ok:
        labels = res.json().get('fields', {}).get('labels', [])
        qa_labels = [l for l in labels if l.startswith('qa-')]
        if qa_labels:
            update = {"update": {"labels": [{"remove": l} for l in qa_labels]}}
            requests.put(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth, json=update)
            print(f"Удалены метки: {qa_labels}")
            
    # 3. Перемещение в статусы
    # Сначала ищем доступные транзакции
    res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth)
    transitions = res.json().get('transitions', [])
    
    todo_id = next((t['id'] for t in transitions if t['to']['id'] == '10045' or t['to']['name'] == 'К выполнению'), None)
    if todo_id:
        requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth, json={"transition": {"id": todo_id}})
        print(f"Задача переведена в 'К выполнению'")
        
    res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth)
    transitions = res.json().get('transitions', [])
    in_progress_id = next((t['id'] for t in transitions if t['to']['id'] == '10046' or t['to']['name'] == 'В работе'), None)
    if in_progress_id:
        requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth, json={"transition": {"id": in_progress_id}})
        print(f"Задача переведена в 'В работе', триггер n8n запущен!")

def reset_db():
    print(f"--- Сброс базы данных SQLite для {ISSUE_KEY} ---")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM pipeline_tasks WHERE issue_key = ?", (ISSUE_KEY,))
    cur.execute("DELETE FROM pipeline_stages WHERE issue_key = ?", (ISSUE_KEY,))
    cur.execute("DELETE FROM test_cases WHERE issue_key = ?", (ISSUE_KEY,))
    cur.execute("DELETE FROM audit_reports WHERE issue_key = ?", (ISSUE_KEY,))
    cur.execute("DELETE FROM autotest_files WHERE issue_key = ?", (ISSUE_KEY,))
    conn.commit()
    conn.close()
    print("Записи в SQLite удалены.")

def reset_qase():
    print(f"--- Сброс Qase TMS для {ISSUE_KEY} ---")
    headers = {"Token": QASE_TOKEN}
    res = requests.get(f"{QASE_URL}/case/JS?search={ISSUE_KEY}&limit=100", headers=headers)
    if res.ok:
        entities = res.json().get('result', {}).get('entities', [])
        for case in entities:
            case_id = case['id']
            requests.delete(f"{QASE_URL}/case/JS/{case_id}", headers=headers)
            print(f"Удален тест-кейс Qase ID: {case_id}")

if __name__ == "__main__":
    reset_qase()
    reset_db()
    reset_jira()
    print("Сброс завершен.")
