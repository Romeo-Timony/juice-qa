import os, sys, requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')

token = os.getenv('QASE_API_TOKEN')
url = 'https://api.qase.io/v1/case/JS'
headers = {'Token': token, 'Content-Type': 'application/json'}

implemented_ids = [561, 562, 563, 564, 565, 566, 568, 569, 570]

print(f"Синхронизация статуса Automated в Qase TMS для {len(implemented_ids)} кейсов...")
for cid in implemented_ids:
    r = requests.patch(f"{url}/{cid}", headers=headers, json={'automation': 2})
    if r.ok:
        print(f"  ✅ Кейс JS-{cid} переведен в статус 'Automated' в Qase")
    else:
        print(f"  ❌ Ошибка обновления JS-{cid}: {r.status_code}")
