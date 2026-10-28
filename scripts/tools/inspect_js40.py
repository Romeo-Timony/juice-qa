import os
import sys
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv("qa-automation/.env")

base = os.getenv("ATLASSIAN_BASE_URL")
email = os.getenv("ATLASSIAN_USER_EMAIL")
token = os.getenv("ATLASSIAN_API_TOKEN")

for issue_key in ["JS-40", "JS-41", "JS-42"]:
    resp = requests.get(f"{base}/rest/api/3/issue/{issue_key}/comment", auth=HTTPBasicAuth(email, token))
    comments = resp.json().get("comments", [])
    print(f"\n==================== Total comments on {issue_key}: {len(comments)} ====================")
    for idx, c in enumerate(comments):
        cid = c["id"]
        created = c["created"]
        lines = []
        def extract_text(node):
            if isinstance(node, dict):
                if node.get("type") == "text":
                    lines.append(node.get("text", ""))
                for v in node.values():
                    extract_text(v)
            elif isinstance(node, list):
                for item in node:
                    extract_text(item)
        extract_text(c.get("body"))
        full_text = " ".join(lines)
        header = full_text[:120].replace("\n", " ")
        print(f"[{idx+1}] ID={cid} Created={created} :: {header}")

