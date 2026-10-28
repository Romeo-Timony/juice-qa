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
print("Comment 11472 body:")
print(comments[-1].get('body'))
