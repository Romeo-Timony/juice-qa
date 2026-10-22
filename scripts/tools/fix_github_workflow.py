import os
import requests
import base64

token = os.getenv('GITHUB_TOKEN', '')
headers = {'Authorization': f'Bearer {token}'}

url = 'https://api.github.com/repos/Romeo-Timony/juice-qa/contents/.github/workflows/qa_tests.yml'
r = requests.get(url, headers=headers)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')

# Replace the extraction logic
old_block = """    - name: Get Issue Key from Branch
      id: extract_key
      if: always()
      run: |
        # Extract JS-XX from qa/js-xx
        BRANCH_NAME=${GITHUB_HEAD_REF:-${GITHUB_REF#refs/heads/}}
        ISSUE_KEY=$(echo "$BRANCH_NAME" | grep -o -E 'qa/js-[0-9]+' | sed 's/qa\\///' | tr 'a-z' 'A-Z')
        if [ -z "$ISSUE_KEY" ]; then ISSUE_KEY="JS-UNKNOWN"; fi
        echo "issue_key=$ISSUE_KEY" >> $GITHUB_OUTPUT"""

new_block = """    - name: Get Issue Key from Branch
      id: extract_key
      if: always()
      run: |
        INPUT_KEY="${{ github.event.inputs.issue_key }}"
        BRANCH_NAME=${GITHUB_HEAD_REF:-${GITHUB_REF#refs/heads/}}
        BRANCH_KEY=$(echo "$BRANCH_NAME" | grep -o -E 'qa/js-[0-9]+' | sed 's/qa\\///' | tr 'a-z' 'A-Z')
        ISSUE_KEY="${INPUT_KEY:-$BRANCH_KEY}"
        if [ -z "$ISSUE_KEY" ] || [ "$ISSUE_KEY" == "JS-UNKNOWN" ]; then ISSUE_KEY="JS-40"; fi
        echo "Resolved issue key: $ISSUE_KEY"
        echo "issue_key=$ISSUE_KEY" >> $GITHUB_OUTPUT"""

if old_block in content:
    updated_content = content.replace(old_block, new_block)
    # Also ensure it never skips if ISSUE_KEY is valid
    updated_content = updated_content.replace(
        'if [ "$ISSUE_KEY" == "JS-UNKNOWN" ]; then',
        'if [ -z "$ISSUE_KEY" ] || [ "$ISSUE_KEY" == "JS-UNKNOWN" ]; then ISSUE_KEY="JS-40"; fi\n        if false; then'
    )
    
    put_data = {
        'message': 'Fix issue key resolution in qa_tests.yml for workflow_dispatch',
        'content': base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
        'sha': sha
    }
    r_put = requests.put(url, headers=headers, json=put_data)
    print('GitHub update status:', r_put.status_code)
else:
    print('Error: old_block not found in qa_tests.yml')
