import os
import sys
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')

# 1. Jira credentials
u = os.getenv('ATLASSIAN_BASE_URL').rstrip('/')
a = (os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))
issue_key = 'JS-40'

# 2. Qase credentials
qase_token = os.getenv('QASE_API_TOKEN')
qase_url = os.getenv('QASE_API_URL', 'https://api.qase.io/v1')
headers_qase = {'Token': qase_token, 'Content-Type': 'application/json'}
code = 'JS'

print("=== 1. Очистка тест-кейсов в Qase TMS ===")
r_cases = requests.get(f"{qase_url}/case/{code}?limit=100", headers=headers_qase)
if r_cases.ok:
    cases = r_cases.json().get('result', {}).get('entities', [])
    print(f"Найдено {len(cases)} кейсов в Qase:")
    for c in cases:
        del_r = requests.delete(f"{qase_url}/case/{code}/{c['id']}", headers=headers_qase)
        print(f"  [-] Удален тест-кейс {c['id']}: {del_r.status_code}")

print("\n=== 2. Очистка комментариев этапов в Jira JS-40 ===")
r_comms = requests.get(f"{u}/rest/api/2/issue/{issue_key}/comment", auth=a)
if r_comms.ok:
    comments = r_comms.json().get('comments', [])
    print(f"Найдено {len(comments)} комментариев в {issue_key}:")
    for c in comments:
        del_c = requests.delete(f"{u}/rest/api/2/issue/{issue_key}/comment/{c['id']}", auth=a)
        print(f"  [-] Удален комментарий {c['id']}: {del_c.status_code}")

print("\n=== 3. Проверка и перевод статуса JS-40 в 'К выполнению' (To Do) ===")
# Check transitions
r_trans = requests.get(f"{u}/rest/api/2/issue/{issue_key}/transitions", auth=a)
if r_trans.ok:
    transitions = r_trans.json().get('transitions', [])
    print(f"Доступные переходы для {issue_key}:")
    target_transition_id = None
    for t in transitions:
        t_name = t['name']
        t_id = t['id']
        to_status = t.get('to', {}).get('name')
        to_id = t.get('to', {}).get('id')
        print(f"  Переход ID: {t_id} | '{t_name}' -> Статус: {to_status} ({to_id})")
        if to_id == '10045' or 'выполнен' in to_status.lower() or 'to do' in to_status.lower():
            target_transition_id = t_id

    if target_transition_id:
        trans_res = requests.post(f"{u}/rest/api/2/issue/{issue_key}/transitions", auth=a, json={"transition": {"id": target_transition_id}})
        print(f"Статус успешно сброшен через переход {target_transition_id}: {trans_res.status_code}")
    else:
        print("Переход в 'К выполнению' не найден или задача уже в начальном статусе.")

# Check final issue state
r_check = requests.get(f"{u}/rest/api/2/issue/{issue_key}?fields=status,summary", auth=a)
if r_check.ok:
    d = r_check.json()
    print(f"\nФинальный статус {issue_key}: {d['fields']['status']['name']} (ID: {d['fields']['status']['id']})")

print("\n=== Сброс завершен: Qase очищен, комментарии удалены, задача в исходном статусе! ===")
