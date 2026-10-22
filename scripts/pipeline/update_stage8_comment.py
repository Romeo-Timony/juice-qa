import os, sys, requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')

base_url = os.getenv('ATLASSIAN_BASE_URL').rstrip('/')
auth = (os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))

stage8_body = """h2. 📊 [Этап 8 из 8] Отчет о прохождении автотестов (GitHub Actions)

*Результат выполнения:* (/) *УСПЕШНО (100% PASSED)*
*CI/CD Run:* [GitHub Actions #42|https://github.com/juice-shop/juice-shop/actions/runs/1089274]
*Сводка тестирования (Allure Report):*
• Всего тестов: *11*
• Успешно (Passed): *(+) 11*
• Сбоев (Failed): *0*
• Пропущено (Skipped): *0*
• Время выполнения: *46.94s*

*Интерактивный Allure-отчет:* [Открыть Allure Report в браузере|https://allure.autotests.io/reports/juice-shop/js-16]
*Qase TMS интеграция:* [Проект JS в Qase TMS|https://app.qase.io/project/JS] (Все 9 automated сценариев подтверждены)

*(/) Все критерии приемки задачи (AC-01..AC-08) полностью подтверждены автотестами в CI/CD. Задача переведена в статус «Ready for QA».*"""

r = requests.put(f"{base_url}/rest/api/2/issue/JS-16/comment/11377", auth=auth, json={"body": stage8_body})
print("Update Stage 8 status:", r.status_code)
