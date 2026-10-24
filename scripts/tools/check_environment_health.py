import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

def run_health_check():
    print("=" * 65)
    print("🏥 ПРОВЕРКА СОСТОЯНИЯ СЕРВИСОВ И ОКРУЖЕНИЯ QA ECOSYS")
    print("=" * 65)

    checks = {}

    # 1. Juice Shop Website
    try:
        r = requests.get("http://localhost:3000/rest/admin/application-version", timeout=3)
        version = r.json().get("version") if r.ok else "N/A"
        checks["Juice Shop (:3000)"] = ("✅ ONLINE", f"v{version}")
    except Exception as e:
        checks["Juice Shop (:3000)"] = ("❌ OFFLINE", str(e)[:40])

    # 2. ngrok Tunnel
    try:
        r = requests.get("https://stylish-mary-bluebelled.ngrok-free.dev", timeout=5)
        checks["ngrok HTTPS Tunnel"] = ("✅ ONLINE", "https://stylish-mary-bluebelled.ngrok-free.dev")
    except Exception as e:
        checks["ngrok HTTPS Tunnel"] = ("❌ OFFLINE", str(e)[:40])

    # 3. n8n Engine
    n8n_url = os.getenv("N8N_URL", "http://201.34.147.33:5678").rstrip("/")
    try:
        r = requests.get(n8n_url, timeout=5)
        checks["n8n Workflow Engine"] = ("✅ ONLINE", n8n_url)
    except Exception as e:
        checks["n8n Workflow Engine"] = ("❌ OFFLINE", str(e)[:40])

    # 4. Browserless
    bl_url = os.getenv("BROWSERLESS_URL", "http://201.34.147.33:3030").rstrip("/")
    try:
        r = requests.get(bl_url, timeout=5)
        checks["Browserless Chromium"] = ("✅ ONLINE", bl_url)
    except Exception as e:
        checks["Browserless Chromium"] = ("❌ OFFLINE", str(e)[:40])

    # 5. Atlassian Jira
    jira_url = os.getenv("ATLASSIAN_BASE_URL", "https://romeo-timony.atlassian.net").rstrip("/")
    auth = (os.getenv("ATLASSIAN_USER_EMAIL"), os.getenv("ATLASSIAN_API_TOKEN"))
    try:
        r = requests.get(f"{jira_url}/rest/api/2/myself", auth=auth, timeout=5)
        name = r.json().get("displayName", "User") if r.ok else "N/A"
        checks["Jira & Confluence"] = ("✅ ONLINE", name)
    except Exception as e:
        checks["Jira & Confluence"] = ("❌ OFFLINE", str(e)[:40])

    # 6. Telegram Bot
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
        bot_user = r.json().get("result", {}).get("username", "bot") if r.ok else "N/A"
        checks["Telegram QA Bot"] = ("✅ ONLINE", f"@{bot_user}")
    except Exception as e:
        checks["Telegram QA Bot"] = ("❌ OFFLINE", str(e)[:40])

    # 7. Qase TMS
    qase_token = os.getenv("QASE_API_TOKEN")
    try:
        r = requests.get("https://api.qase.io/v1/project/JS", headers={"Token": qase_token}, timeout=5)
        checks["Qase TMS (Project JS)"] = ("✅ ONLINE", "Connected")
    except Exception as e:
        checks["Qase TMS (Project JS)"] = ("❌ OFFLINE", str(e)[:40])

    for service, (status, detail) in checks.items():
        print(f" {status} | {service:<24} | {detail}")
    print("=" * 65)

if __name__ == "__main__":
    run_health_check()
