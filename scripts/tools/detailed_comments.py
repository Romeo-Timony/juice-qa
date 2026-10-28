import os, sys, json, requests
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
    print(f"\n==================== {issue_key}: {len(comments)} comments ====================")
    for c in comments:
        cid = c["id"]
        # extract text lines
        text_lines = []
        def extract(node):
            if isinstance(node, dict):
                if node.get("type") == "text":
                    text_lines.append(node.get("text", ""))
                for v in node.values():
                    extract(v)
            elif isinstance(node, list):
                for i in node:
                    extract(i)
        extract(c.get("body"))
        txt = " ".join(text_lines)
        first_line = txt.strip()[:100].replace("\n", " ")
        print(f"ID={cid:8s} | {first_line}")
