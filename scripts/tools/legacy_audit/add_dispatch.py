import os
import requests
import base64

token = os.getenv('GITHUB_TOKEN', '')
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github.v3+json'
}

r = requests.get('https://api.github.com/repos/Romeo-Timony/juice-qa/contents/.github/workflows/qa_tests.yml', headers=headers)
data = r.json()
sha = data['sha']
content = base64.b64decode(data['content']).decode('utf-8')

if 'workflow_dispatch:' not in content:
    print('Adding workflow_dispatch trigger to qa_tests.yml...')
    addition = "  pull_request:\n    branches:\n      - master\n      - main\n  workflow_dispatch:\n    inputs:\n      issue_key:\n        description: 'Jira Issue Key'\n        required: false\n        default: 'JS-40'"
    target = "  pull_request:\n    branches:\n      - master\n      - main"
    new_content = content.replace(target, addition)
    put_r = requests.put(
        'https://api.github.com/repos/Romeo-Timony/juice-qa/contents/.github/workflows/qa_tests.yml',
        headers=headers,
        json={
            'message': 'ci: add workflow_dispatch trigger for n8n orchestrator',
            'content': base64.b64encode(new_content.encode('utf-8')).decode('ascii'),
            'sha': sha
        }
    )
    print('Update status:', put_r.status_code)
else:
    print('workflow_dispatch already present!')
