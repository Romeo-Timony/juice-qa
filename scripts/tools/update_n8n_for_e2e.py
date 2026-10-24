import json
import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(".env")

N8N_URL = os.getenv("N8N_API_URL", "http://201.34.147.33:5678").rstrip("/")
N8N_KEY = os.getenv("N8N_API_KEY")
WORKFLOW_ID = "Dv1WydaTMC1lxR0E"

def update_workflow():
    with open("n8n_live_workflow.json", "r", encoding="utf-8") as f:
        wf = json.load(f)

    # 1. Update "Правила проверки готовности задачи"
    for node in wf.get("nodes", []):
        if node["name"] == "Правила проверки готовности задачи":
            code = node["parameters"]["jsCode"]
            if "e2e: {" not in code:
                profile_insert = """    e2e: {
      label: 'E2E-подзадача (Сквозные сценарии)',
      criteria: [
        { id: 'E01', mandatory: true, title: 'Сквозные пользовательские сценарии', rule: 'Описаны сквозные сценарии онбординга и пользовательского пути (Happy Path и интеграция).' },
        { id: 'E02', mandatory: true, title: 'Интеграция UI и API', rule: 'Описано взаимодействие клиентской части и серверных эндпоинтов, обработка ошибок бэкенда.' },
        { id: 'E03', mandatory: false, title: 'НФТ и безопасность', rule: 'Указаны требования к безопасности токенов, логированию и производительности.' }
      ]
    },
    generic: {"""
                code = code.replace("    generic: {", profile_insert)
                
                baseline_insert = """    e2e: [
      'Сквозные E2E-сценарии онбординга', 'Интеграция клиент-сервер (UI <-> API)',
      'Сквозная обработка ошибок сервера (HTTP 400 и дубликаты)', 'Безопасность JWT и хранение в Storage',
      'Производительность и время отклика онбординга (< 3с)'
    ],
    generic: ["""
                code = code.replace("    generic: [", baseline_insert)
                node["parameters"]["jsCode"] = code
                print("✅ Node 'Правила проверки готовности задачи' verified")

    # 2. Update "Подготовка задачи к проверке"
    for node in wf.get("nodes", []):
        if node["name"] == "Подготовка задачи к проверке":
            code = node["parameters"]["jsCode"]
            if "standard.profiles[kind] || standard.profiles.e2e" not in code:
                code = code.replace(
                    "const profile = standard.profiles[kind]",
                    "const profile = standard.profiles[kind] || standard.profiles.e2e || standard.profiles.frontend || standard.profiles.generic"
                )
                node["parameters"]["jsCode"] = code
                print("✅ Node 'Подготовка задачи к проверке' verified")

    # 3. Update "Создание тест-кейсов без повторов"
    for node in wf.get("nodes", []):
        if node["name"] == "Создание тест-кейсов без повторов":
            code = node["parameters"]["jsCode"]
            
            # Remove any misplaced defaultE2ECases from top
            if code.strip().startswith("const defaultE2ECases = ["):
                # Cut until the original node comment
                idx = code.find('// n8n Code node: "Создание тест-кейсов без повторов"')
                if idx != -1:
                    code = code[idx:]
            
            e2e_cases_js = """const defaultE2ECases = [
  {
    id: 'TC-E2E-01',
    title: '[E2E][Smoke] Полный приемочный цикл онбординга нового покупателя: регистрация, вход и переход к покупкам',
    description: `## 📌 Цель тест-кейса
Сквозная проверка полного пути нового покупателя в интернет-магазине OWASP Juice Shop: переход на форму регистрации, заполнение валидных данных, редирект на экран авторизации, успешный вход в систему и отображение профиля/корзины на главной странице.

## 🥒 Спецификация BDD Gherkin
\`\`\`gherkin
@allure.epic("OWASP Juice Shop")
@allure.feature("Customer Onboarding Journey")
@allure.story("${ctx.issueKey}: Полный цикл онбординга нового покупателя")
@allure.severity("blocker")
@smoke @regress @fast-regression @full-regression
Scenario: Полный цикл онбординга от регистрации до готовности к покупкам
  Given новый посетитель находится на главной странице Juice Shop
  When он переходит на страницу регистрации "/#/register" и регистрирует аккаунт
  And входит в систему с созданными учетными данными на странице "/#/login"
  Then пользователь перенаправляется на главную страницу
  And в шапке отображается кнопка профиля аккаунта и доступна корзина
\`\`\``,
    covers: ['AC-E2E-01', 'AC-E2E-02', 'NFR-E2E-03'],
    type: 'smoke',
    severity: 'blocker',
    priority: 'high',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'e2e', 'onboarding', 'smoke', 'regress', 'fast-regression', 'full-regression', ctx.issueKey, 'to-be-automated'],
    preconditions: 'Пользователь не авторизован, сервер запущен.',
    steps: [
      { action: '[Given] Открыть главную страницу Juice Shop', data: '/', expected_result: 'Главная страница успешно загружена' },
      { action: '[When] Зарегистрировать нового покупателя с уникальным email', data: 'Unique email, Password123!', expected_result: 'Регистрация успешна, редирект на страницу /#/login' },
      { action: '[And] Ввести учетные данные и нажать кнопку Login', data: 'Login form submit', expected_result: 'Авторизация успешна, редирект на витрину магазина' },
      { action: '[Then] Проверить отображение элементов авторизованного пользователя', data: 'Header account icon & basket', expected_result: 'Отображается кнопка аккаунта и корзина покупок' }
    ]
  },
  {
    id: 'TC-E2E-02',
    title: '[E2E][Integration] Сквозная консистентность сессии и проверка сохранения Bearer JWT в Web Storage',
    description: `## 📌 Цель тест-кейса
Проверка безопасности сессии и корректности инициализации клиентского контекста: после успешного входа JWT токен сохраняется в localStorage/sessionStorage, содержит корректный заголовок Bearer и обеспечивает доступ к защищенным API-ресурсам без утечек пароля в открытом виде.

## 🥒 Спецификация BDD Gherkin
\`\`\`gherkin
@allure.epic("OWASP Juice Shop")
@allure.feature("Authentication & Security")
@allure.story("${ctx.issueKey}: Сохранение и валидация JWT токена")
@allure.severity("critical")
@security @regress @fast-regression @full-regression
Scenario: Проверка наличия и структуры JWT токена в браузере после входа
  Given зарегистрированный пользователь авторизуется через форму логина
  When авторизация завершается успешно
  Then в Web Storage (localStorage) присутствует ключ "token"
  And значение токена является валидным JWT (содержит 3 сегмента, разделенных точками)
  And в сетевых логах и storage отсутствует открытый пароль пользователя
\`\`\``,
    covers: ['AC-E2E-02', 'NFR-E2E-01'],
    type: 'integration',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'e2e', 'jwt', 'security', 'regress', 'fast-regression', 'full-regression', ctx.issueKey, 'to-be-automated'],
    preconditions: 'Учетная запись создана.',
    steps: [
      { action: '[Given] Выполнить логин через веб-интерфейс', data: 'Valid user credentials', expected_result: 'Пользователь успешно вошел в систему' },
      { action: '[When] Извлечь токен авторизации из localStorage', data: 'localStorage.getItem("token")', expected_result: 'Ключ token существует и не пустой' },
      { action: '[Then] Проверить формат JWT токена', data: 'Token structure: header.payload.signature', expected_result: 'Токен соответствует формату JWT (3 части через точку)' }
    ]
  },
  {
    id: 'TC-E2E-03',
    title: '[E2E][Negative] Сквозная обработка дубликата Email при регистрации (HTTP 400 и UI Notification)',
    description: `## 📌 Цель тест-кейса
Негативная сквозная интеграционная проверка: попытка повторной регистрации существующего Email приводит к возврату HTTP 400 с сервера и корректному отображению ошибки на фронтенде без падения клиентского приложения.

## 🥒 Спецификация BDD Gherkin
\`\`\`gherkin
@allure.epic("OWASP Juice Shop")
@allure.feature("Customer Registration")
@allure.story("${ctx.issueKey}: Сквозная обработка дубликата Email")
@allure.severity("critical")
@negative @regress @fast-regression @full-regression
Scenario: Регистрация с уже существующим в системе Email
  Given в системе уже зарегистрирован пользователь с email "duplicate_user@juice-sh.op"
  When новый гость пытается зарегистрироваться с тем же email "duplicate_user@juice-sh.op"
  Then сервер возвращает HTTP статус 400 "Email must be unique"
  And в веб-интерфейсе отображается понятное уведомление об ошибке
  And состояние формы остается стабильным
\`\`\``,
    covers: ['AC-E2E-03'],
    type: 'functional',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'negative',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'e2e', 'negative', 'regress', 'fast-regression', 'full-regression', ctx.issueKey, 'to-be-automated'],
    preconditions: 'Пользователь с данным email уже существует в БД.',
    steps: [
      { action: '[Given] Открыть страницу /#/register', data: '/#/register', expected_result: 'Форма открыта' },
      { action: '[When] Заполнить форму с дублирующим email и отправить', data: 'Existing duplicate email', expected_result: 'Запрос отправлен на POST /api/Users' },
      { action: '[Then] Проверить отображение сообщения об ошибке', data: 'Error alert/snack bar', expected_result: 'Отображается сообщение о том, что email уже используется' }
    ]
  },
  {
    id: 'TC-E2E-04',
    title: '[E2E][Security] Сквозной сценарий сброса и восстановления пароля по секретному вопросу',
    description: `## 📌 Цель тест-кейса
Проверка сквозного механизма безопасности: восстановление доступа к учетной записи через контрольный вопрос (Security Question) на странице /#/forgot-password и последующий успешный вход с обновленным паролем.

## 🥒 Спецификация BDD Gherkin
\`\`\`gherkin
@allure.epic("OWASP Juice Shop")
@allure.feature("Account Security")
@allure.story("${ctx.issueKey}: Восстановление пароля по секретному вопросу")
@allure.severity("critical")
@security @regress @fast-regression @full-regression
Scenario: Восстановление пароля и успешная последующая авторизация
  Given зарегистрированный пользователь открыл форму восстановления пароля "/#/forgot-password"
  When он вводит свой email и правильный ответ на секретный вопрос
  And указывает новый валидный пароль
  Then пароль успешно обновляется в системе
  And пользователь может авторизоваться с новым паролем на странице входа
\`\`\``,
    covers: ['AC-E2E-04'],
    type: 'security',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'e2e', 'security', 'recovery', 'regress', 'fast-regression', 'full-regression', ctx.issueKey, 'to-be-automated'],
    preconditions: 'Пользователь зарегистрирован с установленным секретным вопросом.',
    steps: [
      { action: '[Given] Открыть страницу /#/forgot-password', data: '/#/forgot-password', expected_result: 'Форма восстановления отображается' },
      { action: '[When] Заполнить email, ответ на секретный вопрос и новый пароль', data: 'Valid answer, NewPassword123!', expected_result: 'Кнопка смены пароля активна' },
      { action: '[And] Подтвердить смену пароля', data: 'Click change password', expected_result: 'Пароль успешно изменен' },
      { action: '[Then] Авторизоваться с новым паролем', data: 'Login with NewPassword123!', expected_result: 'Успешный вход в аккаунт' }
    ]
  },
  {
    id: 'TC-E2E-05',
    title: '[E2E][NFR] Валидация SLA производительности полного цикла онбординга (< 3 секунд)',
    description: `## 📌 Цель тест-кейса
Нефункциональная проверка производительности: измерение суммарного времени выполнения сквозного сценария онбординга (регистрация + логин). Время отклика не должно превышать установленный в NFR-E2E-02 SLA лимит в 3.0 секунды.

## 🥒 Спецификация BDD Gherkin
\`\`\`gherkin
@allure.epic("OWASP Juice Shop")
@allure.feature("Performance & NFR")
@allure.story("${ctx.issueKey}: SLA времени выполнения онбординга")
@allure.severity("major")
@performance @regress @fast-regression @full-regression
Scenario: Проверка времени завершения сквозного процесса онбординга
  Given тестовое окружение и Juice Shop сервер функционируют штатно
  When выполняется сквозной процесс регистрации и последующего входа
  Then общее время выполнения операций не превышает 3000 миллисекунд
\`\`\``,
    covers: ['NFR-E2E-02'],
    type: 'performance',
    severity: 'major',
    priority: 'medium',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'e2e', 'performance', 'sla', 'regress', 'fast-regression', 'full-regression', ctx.issueKey, 'to-be-automated'],
    preconditions: 'Сервер запущен, сетевые задержки в пределах нормы.',
    steps: [
      { action: '[Given] Зафиксировать начальное время (timestamp)', data: 'performance.now()', expected_result: 'Таймер запущен' },
      { action: '[When] Выполнить сквозную регистрацию и вход пользователя', data: 'Full onboarding flow', expected_result: 'Операции завершены успешно' },
      { action: '[Then] Вычислить затраченное время (delta)', data: 'delta = end - start', expected_result: 'delta < 3000 ms' }
    ]
  },
  {
    id: 'TC-E2E-06',
    title: '[E2E][Integration] Сквозная авторизация созданного через UI пользователя через прямой API POST /rest/user/login',
    description: `## 📌 Цель тест-кейса
Интеграционная проверка консистентности данных между слоями: учетная запись, созданная через интерфейс браузера, немедленно доступна для успешной авторизации через REST API эндпоинт POST /rest/user/login, возвращающий HTTP 200 и валидный объект аутентификации.

## 🥒 Спецификация BDD Gherkin
\`\`\`gherkin
@allure.epic("OWASP Juice Shop")
@allure.feature("API & UI Integration")
@allure.story("${ctx.issueKey}: Консистентность пользователя между UI и API")
@allure.severity("critical")
@integration @regress @fast-regression @full-regression
Scenario: Прямой вызов API логина для учетной записи, созданной на фронтенде
  Given пользователь зарегистрирован через веб-форму UI
  When отправляется прямой HTTP POST запрос на "/rest/user/login" с этими учетными данными
  Then сервер возвращает HTTP статус 200 OK
  And тело ответа содержит валидный токен авторизации "authentication.token"
  And идентификатор пользователя совпадает с созданным аккаунтом
\`\`\``,
    covers: ['AC-E2E-02'],
    type: 'integration',
    severity: 'critical',
    priority: 'high',
    layer: 'e2e',
    behavior: 'positive',
    automation: 'to-be-automated',
    tags: ['bdd', 'gherkin', 'allure', 'e2e', 'api', 'integration', 'regress', 'fast-regression', 'full-regression', ctx.issueKey, 'to-be-automated'],
    preconditions: 'Пользователь зарегистрирован на UI.',
    steps: [
      { action: '[Given] Создать пользователя через UI', data: 'RegisterPage.register()', expected_result: 'Пользователь сохранен в базе данных' },
      { action: '[When] Отправить POST /rest/user/login', data: '{ email, password }', expected_result: 'Сервер отвечает HTTP 200' },
      { action: '[Then] Проверить тело ответа API', data: 'response.body.authentication', expected_result: 'Присутствует валидный Bearer токен' }
    ]
  }
]
"""
            # Insert defaultE2ECases immediately before const defaultFrontendCases = [
            if "const defaultE2ECases = [" not in code:
                code = code.replace("const defaultFrontendCases = [", e2e_cases_js + "\nconst defaultFrontendCases = [")
            
            # Update case selection
            if "else if (kind === 'e2e') cases = defaultE2ECases" not in code:
                code = code.replace(
                    "let cases = defaultFrontendCases\nif (kind === 'backend') cases = defaultBackendCases",
                    "let cases = defaultFrontendCases\nif (kind === 'backend') cases = defaultBackendCases\nelse if (kind === 'e2e') cases = defaultE2ECases"
                )
            
            # Update kindTitle
            if "else if (kind === 'e2e') kindTitle = 'E2E Onboarding'" not in code:
                code = code.replace(
                    "let kindTitle = 'Frontend'\nif (kind === 'backend') kindTitle = 'Backend'",
                    "let kindTitle = 'Frontend'\nif (kind === 'backend') kindTitle = 'Backend'\nelse if (kind === 'e2e') kindTitle = 'E2E Onboarding'"
                )
            
            # Update RTM table in generateRtmComment
            rtm_e2e = """  } else if (kind === 'e2e') {
    lines.push('|*AC-E2E-01*|Happy Path: Полный цикл онбординга (регистрация -> логин -> витрина)|[TC-E2E-01]|Полный приемочный цикл онбординга нового покупателя: регистрация, вход и переход к покупкам|Smoke / Critical|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-E2E-02*|Интеграция: Консистентность данных между UI и API (POST /rest/user/login)|[TC-E2E-02]|Сквозная консистентность сессии и проверка сохранения Bearer JWT в Web Storage|Integration / Session|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-E2E-03*|Интеграция / Негативный: Сквозная обработка дубликата Email (HTTP 400 и UI Notification)|[TC-E2E-03]|Сквозная обработка дубликата Email при регистрации (HTTP 400 и UI Notification)|Negative / Functional|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*AC-E2E-04*|Безопасность: Сквозное восстановление пароля по секретному вопросу|[TC-E2E-04]|Сквозной сценарий сброса и восстановления пароля по секретному вопросу|Security / Recovery|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*NFR-E2E-01*|Безопасность / OWASP: Хранение Bearer токенов в localStorage, маскирование паролей|[TC-E2E-02]|Сквозная консистентность сессии и проверка сохранения Bearer JWT в Web Storage|Security / OWASP|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*NFR-E2E-02*|Производительность: Онбординг завершается быстрее 3 секунд (SLA)|[TC-E2E-05]|Валидация SLA производительности полного цикла онбординга (< 3 секунд)|Performance / SLA|E2E (Playwright)|(/) Покрыто (100%)|')
    lines.push('|*NFR-E2E-03*|Надежность: 100% стабильность прохождения тестов без флаки-эффектов|[TC-E2E-01]|Полный приемочный цикл онбординга нового покупателя: регистрация, вход и переход к покупкам|Reliability / Quality|E2E (Playwright)|(/) Покрыто (100%)|')
"""
            if "lines.push('|*AC-E2E-01*|" not in code:
                code = code.replace("  } else if (isStory) {", rtm_e2e + "  } else if (isStory) {")
            
            # Update RTM NFR section
            rtm_nfr_e2e = """  } else if (kind === 'e2e') {
    lines.push('* *End-to-End Onboarding Journey:* Полный сквозной путь покупателя покрыт E2E спецификациями TC-E2E-01, TC-E2E-02.')
    lines.push('* *OWASP Session Management:* Контроль хранения JWT-токена в localStorage и отсутствие утечек паролей верифицируется TC-E2E-02.')
    lines.push('* *Error Handling & SLA:* Отображение HTTP 400 ошибок бэкенда на UI и SLA производительности (< 3s) проверяются кейсами TC-E2E-03, TC-E2E-05.')
"""
            if "End-to-End Onboarding Journey" not in code:
                code = code.replace("  } else if (isStory) {", rtm_nfr_e2e + "  } else if (isStory) {")
                
            node["parameters"]["jsCode"] = code
            print("✅ Node 'Создание тест-кейсов без повторов' updated cleanly with defaultE2ECases")

    # Save to local file
    with open("n8n_live_workflow.json", "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print("💾 Saved updated n8n_live_workflow.json locally")

    # Push to n8n server
    payload = {
        "name": wf.get("name", "Juice Shop"),
        "nodes": wf.get("nodes", []),
        "connections": wf.get("connections", {}),
        "settings": wf.get("settings", {})
    }
    
    url = f"{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}"
    headers = {
        "X-N8N-API-KEY": N8N_KEY,
        "Content-Type": "application/json"
    }
    
    r = requests.put(url, headers=headers, json=payload, timeout=30)
    if r.status_code == 200:
        print(f"🚀 n8n server successfully updated with new workflow! Status: {r.status_code}")
    else:
        print(f"❌ Failed to update n8n workflow: {r.status_code} - {r.text}")

    # Ensure workflow is active
    r_act = requests.post(f"{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}/activate", headers=headers, timeout=15)
    print(f"⚡ Workflow activation status: {r_act.status_code}")

if __name__ == "__main__":
    update_workflow()
