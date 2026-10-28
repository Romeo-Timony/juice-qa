import os
import sys
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')

u = os.getenv('ATLASSIAN_BASE_URL').rstrip('/')
a = (os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))
issue_key = 'JS-40'

stage3_body = """h2. 🧪 [Этап 3 из 8] Реестр тест-кейсов (BDD): [API] Регистрация пользователей (JS-40)

*Статус:* Спроектированы и переданы на согласование (Quality Gate 1).
*Раздел Qase TMS:* API / JS-40: [API] Реализация серверной логики и контрактов регистрации (POST /api/Users)

||ID||Название тест-кейса||Тип / Приоритет||Слой||Статус покрытия||
|[TC-579|https://app.qase.io/case/JS-579]|[API] Успешная регистрация нового покупателя с валидными данными|Functional / High|API|(/) Спроектирован|
|[TC-580|https://app.qase.io/case/JS-580]|[API] Получение полного справочника контрольных вопросов|Functional / High|API|(/) Спроектирован|
|[TC-581|https://app.qase.io/case/JS-581]|[API] Отказ в регистрации при передаче дубликата Email|Negative / High|API|(/) Спроектирован|
|[TC-582|https://app.qase.io/case/JS-582]|[API] Валидация запрета пустых значений Email и пароля|Negative / Medium|API|(/) Спроектирован|
|[TC-583|https://app.qase.io/case/JS-583]|[API] Сохранение ответа на контрольный вопрос пользователя|Integration / High|API|(/) Спроектирован|
|[TC-584|https://app.qase.io/case/JS-584]|[API] Назначение роли администратора через параметр role|Security / Critical|API|(/) Спроектирован|
"""

stage4_body = """h2. 📊 [Этап 4 из 8] Матрица трассируемости требований (RTM): [API] Регистрация пользователей (JS-40)

*Статус покрытия:* (/) *100% ПОКРЫТО (Full Coverage)*

||Требование / Бизнес-правило||Связанные тест-кейсы Qase||Тип проверки||Слой автоматизации||Статус||
|*BR-AUTH-01 (Уникальность Email)*|[TC-579|https://app.qase.io/case/JS-579], [TC-581|https://app.qase.io/case/JS-581]|Positive / Negative|API|(/) 100% Покрыто|
|*BR-AUTH-02 (Хэширование пароля)*|[TC-579|https://app.qase.io/case/JS-579]|Functional / Security|API|(/) 100% Покрыто|
|*BR-AUTH-03 (Секретный вопрос)*|[TC-580|https://app.qase.io/case/JS-580], [TC-583|https://app.qase.io/case/JS-583]|Functional / Integration|API|(/) 100% Покрыто|
|*BR-AUTH-04 (Санитизация и Trim)*|[TC-579|https://app.qase.io/case/JS-579]|Functional / Security|API|(/) 100% Покрыто|
|*BR-AUTH-05 (Запрет пустых полей)*|[TC-582|https://app.qase.io/case/JS-582]|Negative / BVA|API|(/) 100% Покрыто|
|*CHALLENGE: registerAdmin*|[TC-584|https://app.qase.io/case/JS-584]|Security / Exploit|API|(/) 100% Покрыто|

(/) *Заключение QA Lead:* Все требования задачи имеют двустороннюю трассируемость (Bi-directional Traceability) в Qase TMS. Покрытие скоупа составляет 100%.
"""

r_comms = requests.get(f"{u}/rest/api/2/issue/{issue_key}/comment", auth=a)
if r_comms.ok:
    for c in r_comms.json().get('comments', []):
        body = c.get('body', '')
        if '[Этап 3 из' in body:
            requests.put(f"{u}/rest/api/2/issue/{issue_key}/comment/{c['id']}", auth=a, json={"body": stage3_body})
            print(f"Updated Stage 3 comment {c['id']}")
        elif '[Этап 4 из' in body:
            requests.put(f"{u}/rest/api/2/issue/{issue_key}/comment/{c['id']}", auth=a, json={"body": stage4_body})
            print(f"Updated Stage 4 comment {c['id']}")

print("Jira JS-40 comments updated to clean prefix standard!")
