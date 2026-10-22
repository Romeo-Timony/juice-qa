import os, sys, time, requests, json
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'scripts'))
load_dotenv(BASE_DIR / '.env')

from scripts.qaops_delta_refine import process_delta_requirements

issue_key = 'JS-16'
base_url = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
auth = (email, token)

print(f"=== [ШАГ 1] Публикация дельта-комментария от Product/Security в Jira {issue_key} ===")
delta_comment_text = (
    "@qa-bot [ДОПОЛНЕНИЕ] Требования безопасности (OWASP Security Audit):\n"
    "Необходимо добавить в тестовый регресс проверку устойчивости формы авторизации к классической SQL-инъекции (' or 1=1--) в поле Email "
    "для предотвращения обхода авторизации, а также проверку экранирования XSS (<script>alert(1)</script>) в поле контрольного вопроса."
)

r_comm = requests.post(
    f"{base_url}/rest/api/2/issue/{issue_key}/comment",
    auth=auth,
    json={"body": delta_comment_text}
)
comment_id = r_comm.json().get('id')
print(f"✅ Дельта-комментарий опубликован в Jira (ID: {comment_id})")

print("\n=== [ШАГ 2] Запуск QAOps Delta Refinement Engine ===")
res = process_delta_requirements(
    issue_key=issue_key,
    delta_prompt=delta_comment_text,
    author="Product Security Lead"
)

print("\n=== [ШАГ 3] Результат работы Delta Refinement Engine ===")
print("Статус успеха:", res.get("success"))
print(f"Создано кейсов в Qase TMS: {len(res.get('published_cases', []))}")
for c in res.get('published_cases', []):
    print(f"  • Qase #{c.get('qase_id')}: {c.get('title')} (auto={c.get('is_auto')})")

print(f"Результат прогона тестов в Playwright: {'PASSED' if res.get('test_success') else 'FAILED'}")
print(f"Сквозной трейс Langfuse: {res.get('trace_url')}")
