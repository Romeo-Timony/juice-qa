import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
url = (os.getenv('N8N_URL') or os.getenv('N8N_SERVER_URL') or 'http://201.34.147.33:5678').rstrip('/')
key = os.getenv('N8N_API_KEY')

r = requests.get(f"{url}/api/v1/workflows/Dv1WydaTMC1lxR0E", headers={"X-N8N-API-KEY": key})
data = r.json()
print("Workflow Name:", data.get("name"))
print("Nodes count:", len(data.get("nodes", [])))

out_file = Path("n8n/current_main_workflow.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("Saved to", out_file)
