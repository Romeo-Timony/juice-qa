import os, sys, requests, time
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv('qa-automation/.env')
base_url = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
auth = (email, token)
issue_key = 'JS-16'

print(f"Мониторинг генерации комментариев n8n для {issue_key}...")
seen_comment_ids = set()

for attempt in range(25):
    r = requests.get(f"{base_url}/rest/api/2/issue/{issue_key}/comment", auth=auth)
    if r.ok:
        comments = r.json().get('comments', [])
        new_comments = [c for c in comments if c['id'] not in seen_comment_ids]
        for c in new_comments:
            seen_comment_ids.add(c['id'])
            body = c.get('body', '')
            first_line = body.strip().splitlines()[0] if body.strip() else 'Empty'
            print(f"[{time.strftime('%H:%M:%S')}] Новый комментарий (ID {c['id']}): {first_line}")
        
        gate1 = next((c for c in comments if "[Этап 5 из" in c.get('body', '')), None)
        if gate1:
            print("\n>>> УСПЕХ: Карточка Quality Gate 1 опубликована! <<<")
            break
    time.sleep(3)

print(f"Всего комментариев на данный момент: {len(seen_comment_ids)}")
