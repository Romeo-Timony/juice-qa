import os, requests, dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv.load_dotenv(BASE_DIR / ".env")
u = os.getenv("ATLASSIAN_BASE_URL", "https://romeo-timony.atlassian.net").rstrip("/")
a = (os.getenv("ATLASSIAN_USER_EMAIL"), os.getenv("ATLASSIAN_API_TOKEN"))
r = requests.get(u + "/rest/api/3/search/jql", auth=a, params={"jql": "project = JS ORDER BY key ASC", "fields": "summary,status,labels"})
for i in r.json().get("issues", []):
    print(f"{i['key']} | status={i['fields']['status']['name']} ({i['fields']['status']['id']}) | labels={i['fields'].get('labels')} | {i['fields']['summary']}")
