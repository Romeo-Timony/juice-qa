import os, sys, requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv("qa-automation/.env")

base = os.getenv("ATLASSIAN_BASE_URL")
email = os.getenv("ATLASSIAN_USER_EMAIL")
token = os.getenv("ATLASSIAN_API_TOKEN")

for issue_key in ["JS-40", "JS-41", "JS-42"]:
    resp = requests.get(f"{base}/rest/api/2/issue/{issue_key}/comment", auth=HTTPBasicAuth(email, token))
    comments = resp.json().get("comments", [])
    print(f"\n==================== {issue_key}: {len(comments)} comments ====================")
    for c in comments:
        cid = c["id"]
        body = c.get("body", "")
        lines = [l for l in body.split("\n") if l.strip()]
        header = lines[0] if lines else "EMPTY"
        print(f"ID={cid:8s} | {header[:90]}")

