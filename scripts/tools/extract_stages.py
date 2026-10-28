import os, sys, json, requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv("qa-automation/.env")

base = os.getenv("ATLASSIAN_BASE_URL")
email = os.getenv("ATLASSIAN_USER_EMAIL")
token = os.getenv("ATLASSIAN_API_TOKEN")

extracted = {}

for issue_key in ["JS-40", "JS-41", "JS-42"]:
    resp = requests.get(f"{base}/rest/api/2/issue/{issue_key}/comment", auth=HTTPBasicAuth(email, token))
    comments = resp.json().get("comments", [])
    extracted[issue_key] = {}
    for c in comments:
        body = c.get("body", "")
        for stage in range(1, 9):
            tag = f"[Этап {stage} из 8]"
            if tag in body and tag not in extracted[issue_key]:
                extracted[issue_key][tag] = body
        if "QAOps: Итоговое решение" in body and "QAOps" not in extracted[issue_key]:
            extracted[issue_key]["QAOps"] = body

print("Stages found:")
for k, v in extracted.items():
    print(k, list(v.keys()))

with open("qa-automation/scripts/tools/existing_stage_comments.json", "w", encoding="utf-8") as f:
    json.dump(extracted, f, ensure_ascii=False, indent=2)
print("Saved to existing_stage_comments.json")
