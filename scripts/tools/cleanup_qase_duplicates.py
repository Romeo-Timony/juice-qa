import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

qase_token = os.getenv("QASE_API_TOKEN")
headers = {"Token": qase_token, "Content-Type": "application/json", "accept": "application/json"}
project = os.getenv("QASE_PROJECT_CODE", "JS")

print("=" * 60)
print("1. ОЧИСТКА ДУБЛИКАТОВ И СИНХРОНИЗАЦИЯ СТАТУСОВ В QASE TMS")
print("=" * 60)

# Дубликаты в сьюте 86 (API)
duplicates_to_delete = list(range(883, 895))
print(f"Удаление {len(duplicates_to_delete)} дубликатов кейсов в Suite #86 (API): {duplicates_to_delete}...")

for cid in duplicates_to_delete:
    r = requests.delete(f"https://api.qase.io/v1/case/{project}/{cid}", headers=headers)
    if r.status_code == 200:
        print(f"  🗑️ Дубликат #{cid} успешно удален")
    else:
        print(f"  ⚠️ Ошибка удаления #{cid}: {r.status_code} {r.text}")

# Перевод оригинальных кейсов 871..882 в статус Automated (automation = 2)
api_cases = list(range(871, 883))
print(f"\nОбновление статуса на 'Automated' (automation=2) для кейсов {api_cases}...")

for cid in api_cases:
    # automation: 2 = Automated
    r = requests.patch(f"https://api.qase.io/v1/case/{project}/{cid}", headers=headers, json={"automation": 2})
    if r.status_code == 200:
        print(f"  ✅ Кейс #{cid} переведен в статус 'Automated' (auto=2)")
    else:
        print(f"  ❌ Ошибка обновления #{cid}: {r.status_code} {r.text}")

# Проверка итогового состояния
print("\nПроверка итогового состояния сьютов в Qase:")
for sid, sname in [(86, "API"), (87, "UI"), (88, "E2E")]:
    r = requests.get(f"https://api.qase.io/v1/case/{project}?suite_id={sid}&limit=100", headers=headers)
    cases = r.json().get("result", {}).get("entities", [])
    print(f"\nСьют #{sid} ({sname}): всего кейсов {len(cases)}")
    for c in cases:
        print(f"  ID #{c['id']}: auto={c.get('automation')} | {c['title'][:70]}")
