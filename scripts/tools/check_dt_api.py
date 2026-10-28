import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
n8n_url = os.getenv("N8N_URL", "http://201.34.147.33:5678").rstrip("/")
headers = {"X-N8N-API-KEY": os.getenv("N8N_API_KEY")}

# Check /api/v1/data-tables
res = requests.get(f"{n8n_url}/api/v1/data-tables", headers=headers)
tables = res.json().get("data", [])
for t in tables:
    tid = t["id"]
    tname = t["name"]
    # Check rows
    r_rows = requests.get(f"{n8n_url}/api/v1/data-tables/{tid}/rows", headers=headers)
    rows = r_rows.json().get("data", [])
    print(f"Table {tname} ({tid}): {len(rows)} rows")
    # Check options on /rows
    opt = requests.options(f"{n8n_url}/api/v1/data-tables/{tid}/rows", headers=headers)
    print(f"  Allow on /rows: {opt.headers.get('Allow')}")
    if rows:
        row0 = rows[0]
        # test options on /rows/{id}
        rid = row0.get("id")
        opt_item = requests.options(f"{n8n_url}/api/v1/data-tables/{tid}/rows/{rid}", headers=headers)
        print(f"  Allow on /rows/{rid}: {opt_item.headers.get('Allow')}")
