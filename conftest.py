import os
import pytest
import allure
from contextlib import contextmanager
from pathlib import Path
from playwright.sync_api import Page
from dotenv import load_dotenv
from api.client import JuiceShopApiClient

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
VIDEOS_DIR = BASE_DIR / "allure-results" / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def step(title: str):
    """
    Контекстный менеджер шага теста (Best Practice AQA):
    Одновременно фиксирует шаг в Allure Report и логирует его в консоль/терминал с отметкой времени.
    """
    print(f"   -> [ШАГ] {title}")
    with allure.step(title):
        yield

@pytest.fixture(scope="session")
def base_url():
    return os.getenv("JUICE_SHOP_LOCAL_URL", "http://localhost:3000").rstrip("/")

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Настройка записи видео (скринкастов) для браузерных контекстов Playwright."""
    return {
        **browser_context_args,
        "record_video_dir": str(VIDEOS_DIR),
        "record_video_size": {"width": 1280, "height": 720}
    }

from data.users import UserPersonas, UserPersona

@pytest.fixture
def api_client(base_url):
    return JuiceShopApiClient(base_url=base_url)

@pytest.fixture
def user_admin() -> UserPersona:
    """Фикстура администратора системы."""
    return UserPersonas.ADMIN

@pytest.fixture
def user_with_money() -> UserPersona:
    """Фикстура покупателя с положительным балансом $100 (Jim)."""
    return UserPersonas.CUSTOMER_WITH_MONEY

@pytest.fixture
def user_without_money() -> UserPersona:
    """Фикстура покупателя с нулевым балансом $0 (Bender)."""
    return UserPersonas.CUSTOMER_WITHOUT_MONEY

@pytest.fixture(params=[UserPersonas.CUSTOMER_WITH_MONEY, UserPersonas.CUSTOMER_WITHOUT_MONEY], ids=["customer_with_money", "customer_without_money"])
def customer_user(request) -> UserPersona:
    """Параметризованная фикстура покупателей (с деньгами и без денег)."""
    return request.param

@pytest.fixture(params=UserPersonas.ALL, ids=["admin", "customer_with_money", "customer_without_money"])
def any_seeded_user(request) -> UserPersona:
    """Параметризованная фикстура для прогона по всем трем типам пользователей."""
    return request.param

@pytest.fixture
def admin_client(base_url, user_admin) -> JuiceShopApiClient:
    """Авторизованный API-клиент с правами администратора."""
    client = JuiceShopApiClient(base_url=base_url)
    res = client.login(user_admin.email, user_admin.password)
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    return client

@pytest.fixture
def user_with_money_client(base_url, user_with_money) -> JuiceShopApiClient:
    """Авторизованный API-клиент покупателя с балансом $100."""
    client = JuiceShopApiClient(base_url=base_url)
    res = client.login(user_with_money.email, user_with_money.password)
    assert res.status_code == 200, f"Login for user with money failed: {res.text}"
    return client

@pytest.fixture
def user_without_money_client(base_url, user_without_money) -> JuiceShopApiClient:
    """Авторизованный API-клиент покупателя без денег."""
    client = JuiceShopApiClient(base_url=base_url)
    res = client.login(user_without_money.email, user_without_money.password)
    assert res.status_code == 200, f"Login for user without money failed: {res.text}"
    return client

@pytest.fixture
def auth_customer_client(base_url, customer_user) -> JuiceShopApiClient:
    """Параметризованный клиент покупателя (автоматически запускает тест дважды: для юзера с деньгами и без)."""
    client = JuiceShopApiClient(base_url=base_url)
    res = client.login(customer_user.email, customer_user.password)
    assert res.status_code == 200, f"Login for customer {customer_user.email} failed: {res.text}"
    return client

@pytest.fixture
def auth_api_client(base_url):
    """Динамический одноразовый пользователь (fallback при необходимости изолированной регистрации)."""
    client = JuiceShopApiClient(base_url=base_url)
    import time
    ts = int(time.time() * 1000)
    email = f"auth_user_{ts}@juice-sh.op"
    password = "ValidPassword123!"
    reg_res = client.register(email, password)
    assert reg_res.status_code == 201, f"Failed to register test user: {reg_res.text}"
    login_res = client.login(email, password)
    assert login_res.status_code == 200, f"Failed to login test user: {login_res.text}"
    return client

@pytest.fixture
def isolate_wallet_state():
    """
    Фикстура изоляции тестовых данных цифрового кошелька (Test Data Isolation & Teardown).
    Выполняется после теста (даже в случае падения/assert failure) и гарантированно восстанавливает
    балансы сидированных персон (Jim UserId=2 -> $100.0, Bender UserId=3 -> $0.0) в базе SQLite.
    """
    import sqlite3
    db_file = Path(__file__).resolve().parent.parent / "data" / "juiceshop.sqlite"
    yield
    if db_file.exists():
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("UPDATE Wallets SET balance = 100 WHERE UserId = 2")
            cursor.execute("UPDATE Wallets SET balance = 0 WHERE UserId = 3")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: could not restore wallet state in SQLite: {e}")

@pytest.fixture(autouse=True)
def setup_browser_cookies(request, base_url):
    """Автоматическая предустановка кук для отключения всплывающих баннеров."""
    if "context" in request.fixturenames:
        try:
            context = request.getfixturevalue("context")
            context.add_cookies([
                {"name": "welcomebanner_status", "value": "dismiss", "url": base_url},
                {"name": "cookieconsent_status", "value": "dismiss", "url": base_url}
            ])
        except Exception:
            pass

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Хук фиксации статуса выполнения теста для передачи в фикстуру артефактов и сводную таблицу."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)
    
    if report.when == "call":
        try:
            from allure_pytest.utils import allure_title
            report.display_title = allure_title(item) or item.name
        except Exception:
            report.display_title = item.name
            
        qase_mark = item.get_closest_marker("qase")
        report.qase_id = qase_mark.kwargs.get("id") if qase_mark else (qase_mark.args[0] if qase_mark and qase_mark.args else None)

@pytest.fixture(autouse=True)
def capture_ui_screencasts_and_artifacts(request):
    """
    Автоматический захват видео-скринкастов для ВСЕХ пройденных и упавших UI-тестов Playwright.
    Для упавших тестов дополнительно прикрепляется скриншот экрана с ошибкой.
    Скринкасты сохраняются в формате WebM и воспроизводятся прямо внутри Allure Report.
    """
    yield
    rep_call = getattr(request.node, "rep_call", None)
    is_failed = rep_call and rep_call.failed

    page: Page = request.node.funcargs.get("page")
    if not page:
        return

    video = page.video
    test_name = request.node.name

    if is_failed:
        # 1. Прикрепляем скриншот упавшего экрана
        try:
            screenshot = page.screenshot(full_page=True)
            allure.attach(
                screenshot,
                name=f"Screenshot_Failure_{test_name}",
                attachment_type=allure.attachment_type.PNG
            )
        except Exception as e:
            print(f"Warning: could not capture failure screenshot: {e}")

    # 2. Сохраняем и прикрепляем видео-скринкаст для каждого теста (Passed и Failure)
    try:
        if video:
            page.close()
            video_path = video.path()
            if os.path.exists(video_path):
                status_label = "Failure" if is_failed else "Passed"
                allure.attach.file(
                    video_path,
                    name=f"Screencast_{status_label}_{test_name}",
                    attachment_type=allure.attachment_type.WEBM
                )
    except Exception as e:
        print(f"Warning: could not attach screencast video: {e}")



import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


CYAN = "\033[1;36m"
YELLOW = "\033[1;33m"
GREEN = "\033[1;32m"
BLUE = "\033[1;34m"
GRAY = "\033[0;37m"
BOLD = "\033[1m"
RESET = "\033[0m"

def pytest_runtest_setup(item):
    """
    Хук визуализации теста перед запуском (Best Practice AQA):
    Выводит четкий цветной баннер с номером кейса в Qase, выделенным названием и описанием,
    а также автоматически связывает тест с Qase TMS и Jira в Allure Report.
    """
    qase_mark = item.get_closest_marker("qase")
    qase_id = qase_mark.kwargs.get("id") if qase_mark else (qase_mark.args[0] if qase_mark and qase_mark.args else None)
    
    try:
        from allure_pytest.utils import allure_title
        title = allure_title(item) or item.name
    except Exception:
        title = item.name
    
    doc = (item.obj.__doc__ or "").strip().split("\n")[0]
    
    # Автоматическое добавление внешних ссылок в Allure Report
    if qase_id:
        allure.dynamic.link(f"https://app.qase.io/case/JS-{qase_id}", name=f"Qase TMS: [JS-{qase_id}]")
    allure.dynamic.issue("https://romeo-timony.atlassian.net/browse/JS-16", name="Jira: JS-16")

    print(f"\n{CYAN}{'=' * 85}{RESET}")
    qase_badge = f" {GREEN}[QASE #{qase_id}]{RESET}" if qase_id else ""
    print(f"{BOLD}[*] ТЕСТ-КЕЙС:{RESET}{qase_badge} {YELLOW}{title}{RESET}")
    if doc:
        print(f"{GRAY}[*] Описание:  {doc}{RESET}")
    print(f"{GRAY}[*] Модуль:    {item.nodeid.split('::')[0]}::{item.cls.__name__ if item.cls else ''}{RESET}")
    print(f"{CYAN}{'=' * 85}{RESET}")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Финальная сводная матрица результатов в терминале (Best Practice AQA):
    Выводит структурированную таблицу всех выполненных кейсов с привязкой к Qase и времени выполнения.
    """
    reports = []
    for key in ["passed", "failed", "skipped"]:
        for rep in terminalreporter.stats.get(key, []):
            if rep.when == "call":
                reports.append((rep, key.upper()))

    if not reports:
        return

    terminalreporter.section("СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ ТЕСТ-СЕССИИ", blue=True, bold=True)
    header = f"{'Qase ID':<10} | {'Статус':<9} | {'Время':<7} | {'Название сценария':<50}"
    terminalreporter.write_line("-" * len(header))
    terminalreporter.write_line(header)
    terminalreporter.write_line("-" * len(header))

    for rep, status_str in reports:
        qase_id = getattr(rep, "qase_id", None) or "-"
        title = getattr(rep, "display_title", None) or rep.nodeid
        
        status_color = {"PASSED": "green", "FAILED": "red", "SKIPPED": "yellow"}.get(status_str, "white")
        line = f"JS-{qase_id:<7} | {status_str:<9} | {rep.duration:>5.2f}s | {title[:50]}"
        terminalreporter.write_line(line, **{status_color: True})


