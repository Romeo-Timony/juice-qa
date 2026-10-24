import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

n8n_url = os.getenv("N8N_URL", "http://201.34.147.33:5678")
n8n_key = os.getenv("N8N_API_KEY")
headers = {"X-N8N-API-KEY": n8n_key}

with open('scripts/tools/js41_frontend_cases.js', encoding='utf-8') as f:
    js41_cases_content = f.read()

with open('n8n_live_workflow.json', encoding='utf-8') as f:
    wf = json.load(f)

for n in wf['nodes']:
    if n.get('id') == '8672714e-feb5-4242-b9c5-efb63bbbfe20':
        code = n.get('parameters', {}).get('jsCode', '')
        
        # 1. Replace defaultFrontendCases
        start_marker = 'const defaultFrontendCases = ['
        end_marker = 'const defaultBackendCases = ['
        s_idx = code.find(start_marker)
        e_idx = code.find(end_marker)
        if s_idx != -1 and e_idx != -1:
            code = code[:s_idx] + js41_cases_content.replace('const js41RegistrationCases = [', 'const defaultFrontendCases = [') + '\n\n' + code[e_idx:]
            print("Successfully replaced defaultFrontendCases in node jsCode!")

        # 2. Update RTM lines for frontend
        rtm_start = 'lines.push(\'|*AC-01*|Форма регистрации:'
        rtm_end = 'lines.push(\'|*AC-08*|Адресная книга: валидация формата'
        rs_idx = code.find(rtm_start)
        re_idx = code.find(rtm_end)
        if rs_idx != -1 and re_idx != -1:
            # find end of line for AC-08
            re_line_end = code.find('\n', re_idx)
            new_rtm = """    lines.push('|*AC-UI-01*|Состояние кнопки регистрации: #registerButton заблокирована (disabled) по умолчанию при пустой форме|[TC-FE-04|https://app.qase.io/case/JS-4]|Блокировка кнопки Register по умолчанию при пустой форме|Smoke / UI|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-UI-02*|Валидация формата Email: подсказка «Email is not valid» при невалидном формате email|[TC-FE-05|https://app.qase.io/case/JS-5]|Проверка сообщения об ошибке при некорректном формате Email|Validation / UI|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-UI-03*|Граничные значения длины пароля: допустима длина от 5 до 40 символов (BVA)|[TC-FE-02|https://app.qase.io/case/JS-2]|Проверка граничных значений длины пароля (BVA: 5-40 символов)|Functional / BVA|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-UI-03*|Блокировка при длине пароля менее 5 символов: ошибка «Password must be 5-40 characters long»|[TC-FE-06|https://app.qase.io/case/JS-6]|Блокировка кнопки Register при пароле короче 5 символов|Validation / Negative|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-UI-03*|Блокировка при длине пароля более 40 символов (BVA: 41 символ)|[TC-FE-07|https://app.qase.io/case/JS-7]|Блокировка кнопки Register при пароле длиннее 40 символов|Validation / Negative|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-UI-04*|Валидация несовпадения паролей: ошибка «Passwords do not match», кнопка disabled|[TC-FE-03|https://app.qase.io/case/JS-3]|Валидация ошибки при несовпадении пароля и подтверждения пароля|Functional / UI|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-UI-05*|Индикатор надежности пароля: тоггл «Show password advice» отображает шкалу стойкости|[TC-FE-08|https://app.qase.io/case/JS-8]|Отображение индикатора надежности пароля при включении тоггла|UI/UX / Dynamic|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-UI-06*|Выбор контрольного вопроса: mat-select обязателен для разблокировки формы регистрации|[TC-FE-09|https://app.qase.io/case/JS-9]|Обязательность выбора контрольного вопроса из списка Security Questions|Functional / UI|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-UI-06*|Ответ на контрольный вопрос: #securityAnswerControl обязателен для заполнения|[TC-FE-10|https://app.qase.io/case/JS-10]|Валидация обязательности ответа на секретный вопрос|Functional / UI|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-UI-07*|Happy Path регистрации: валидное заполнение всех полей, кнопка Register active, редирект|[TC-FE-01|https://app.qase.io/case/JS-1]|Успешная регистрация нового пользователя с валидными форматами Email|Smoke / Critical|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*NFR-UI-01*|Безопасность ввода: скрытие ввода пароля (type=\\'password\\') в полях Password и Repeat|[TC-FE-11|https://app.qase.io/case/JS-11]|Скрытие ввода пароля (type=\\'password\\') в полях ввода|Security / Masking|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*NFR-UI-03*|Доступность интерфейса: навигация по полям формы регистрации клавишей Tab (WCAG 2.1 AA)|[TC-FE-12|https://app.qase.io/case/JS-12]|Доступность формы регистрации по клавиатуре (Tab Navigation)|Accessibility / a11y|E2E (Playwright)|(/) Покрыто (100%)|')"""
            code = code[:rs_idx] + new_rtm + code[re_line_end:]
            print("Successfully updated RTM lines in node jsCode!")

        n['parameters']['jsCode'] = code

# Save to local file
with open('n8n_live_workflow.json', 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
print("Saved local n8n_live_workflow.json")

# Push to n8n server
payload = {
    "name": wf['name'],
    "nodes": wf['nodes'],
    "connections": wf['connections'],
    "settings": wf.get('settings', {}),
    "staticData": wf.get('staticData')
}
res = requests.put(f"{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E", headers=headers, json=payload)
print(f"PUT n8n workflow status: {res.status_code}")
if res.ok:
    act_res = requests.post(f"{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E/activate", headers=headers)
    print(f"Activate status: {act_res.status_code}")
    print("SUCCESS: Stage 3 node updated in n8n live workflow!")
else:
    print(f"Error: {res.text[:400]}")
