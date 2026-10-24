import requests
import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('.env')

token = os.getenv('QASE_API_TOKEN') or os.getenv('QASE_TOKEN')
r = requests.get('https://api.qase.io/v1/case/JS?limit=100', headers={'Token': token})
cases = r.json().get('result', {}).get('entities', [])

titles = [
    '[E2E][Smoke] Полный приемочный цикл онбординга нового покупателя: регистрация, вход и переход к покупкам',
    '[E2E][Integration] Сквозная консистентность сессии и проверка сохранения Bearer JWT в Web Storage',
    '[E2E][Negative] Сквозная обработка дубликата Email при регистрации (HTTP 400 и UI Notification)',
    '[E2E][Security] Сквозной сценарий сброса и восстановления пароля по секретному вопросу',
    '[E2E][NFR] Валидация SLA производительности полного цикла онбординга (< 3 секунд)',
    '[E2E][Integration] Сквозная авторизация созданного через UI пользователя через прямой API POST /rest/user/login'
]

for t in titles:
    found = [c for c in cases if c.get('title', '').strip().lower() == t.strip().lower()]
    print(f'"{t[:40]}...": found {len(found)} in Qase')
    for f in found:
        print(f'   ID: {f.get("id")}, Suite ID: {f.get("suite_id")}')
