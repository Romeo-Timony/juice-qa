import requests
import json
import time

base_url = 'http://localhost:3000'

print('=== 1. Security Questions API ===')
r_sq = requests.get(f'{base_url}/api/SecurityQuestions/')
print(f'Status: {r_sq.status_code}')
sq_data = r_sq.json().get('data', [])
for q in sq_data:
    print(f"  [{q['id']}] {q['question']}")

print('\n=== 2. Empty POST /api/Users/ ===')
r_empty = requests.post(f'{base_url}/api/Users/', json={})
print(f'Status: {r_empty.status_code}, Body: {r_empty.text}')

print('\n=== 3. Valid Registration ===')
test_email = f'pm_test_{int(time.time())}@juice-sh.op'
payload = {
    'email': test_email,
    'password': 'Password123!',
    'passwordRepeat': 'Password123!',
    'securityQuestion': sq_data[0] if sq_data else {'id': 1},
    'securityAnswer': 'JuiceShopTestAnswer'
}
r_valid = requests.post(f'{base_url}/api/Users/', json=payload)
print(f'Status: {r_valid.status_code}')
print('Response JSON:', json.dumps(r_valid.json(), indent=2))

print('\n=== 4. Duplicate Registration (Edge Case) ===')
r_dup = requests.post(f'{base_url}/api/Users/', json=payload)
print(f'Status: {r_dup.status_code}, Body: {r_dup.text}')

print('\n=== 5. Boundary: Password Length < 5 chars ===')
payload_short = dict(payload, email=f'short_{int(time.time())}@juice-sh.op', password='1234', passwordRepeat='1234')
r_short = requests.post(f'{base_url}/api/Users/', json=payload_short)
print(f'Status: {r_short.status_code}, Body: {r_short.text}')

print('\n=== 6. Boundary: Password Length > 40 chars ===')
long_pwd = 'A' * 41
payload_long = dict(payload, email=f'long_{int(time.time())}@juice-sh.op', password=long_pwd, passwordRepeat=long_pwd)
r_long = requests.post(f'{base_url}/api/Users/', json=payload_long)
print(f'Status: {r_long.status_code}, Body: {r_long.text}')

print('\n=== 7. SQL Injection in Email (Juice Shop Edge Case) ===')
payload_sqli = dict(payload, email="admin'--@juice-sh.op")
r_sqli = requests.post(f'{base_url}/api/Users/', json=payload_sqli)
print(f'Status: {r_sqli.status_code}, Body: {r_sqli.text}')
