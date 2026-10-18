import os, requests, dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(BASE_DIR / ".env")
u = os.getenv("ATLASSIAN_BASE_URL", "https://romeo-timony.atlassian.net").rstrip("/")
a = (os.getenv("ATLASSIAN_USER_EMAIL"), os.getenv("ATLASSIAN_API_TOKEN"))

r = requests.get(u + "/rest/api/3/search/jql", auth=a, params={"jql": "project = JS ORDER BY key ASC", "fields": "summary,status,labels"})
for iss in r.json().get("issues", []):
    key = iss["key"]
    if key == "JS-16":
        continue
    c_res = requests.get(f"{u}/rest/api/2/issue/{key}/comment", auth=a)
    comments = c_res.json().get("comments", [])
    if comments:
        print(f"Issue {key} has {len(comments)} comments.")
