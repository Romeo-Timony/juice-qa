import os
import requests
import time
import sys

token = os.getenv('GITHUB_TOKEN', '')
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github.v3+json'
}

run_id = 39664332693
print(f"Monitoring GitHub Run #{run_id}...")

for i in range(25):
    r = requests.get(f'https://api.github.com/repos/Romeo-Timony/juice-qa/actions/runs/{run_id}', headers=headers)
    if r.status_code == 200:
        data = r.json()
        status = data.get('status')
        conclusion = data.get('conclusion')
        print(f"[{i+1}/25] Status: {status}, Conclusion: {conclusion}")
        if status == 'completed':
            print(f"🎉 Run #{run_id} completed with conclusion: {conclusion}!")
            break
    time.sleep(10)
