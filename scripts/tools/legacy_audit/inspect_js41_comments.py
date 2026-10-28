import os
import requests
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

r = requests.get(
    'https://romeo-timony.atlassian.net/rest/api/2/issue/JS-41',
    auth=(os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))
)
comments = r.json().get('fields', {}).get('comment', {}).get('comments', [])
print(f"Total comments on JS-41: {len(comments)}")
for c in comments:
    cid = c.get('id')
    body = str(c.get('body'))
    first_line = body.strip().splitlines()[0] if body else ""
    print(f"Comment {cid}: {first_line[:100]}")
