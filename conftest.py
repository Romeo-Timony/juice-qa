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

@pytest.fixture
def api_client(base_url):
    return JuiceShopApiClient(base_url=base_url)

@pytest.fixture
def auth_api_client(base_url):
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

@pytest.fixture(autouse=True)
def setup_browser_cookies(context, base_url):
    """Автоматическая предустановка кук для отключения всплывающих баннеров."""
    context.add_cookies([
        {"name": "welcomebanner_status", "value": "dismiss", "url": base_url},
        {"name": "cookieconsent_status", "value": "dismiss", "url": base_url}
    ])

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


def pytest_runtest_setup(item):
    """
    Хук визуализации теста перед запуском (Best Practice AQA):
    Выводит четкий баннер с номером кейса в Qase, понятным названием и описанием,
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

    print("\n" + "=" * 80)
    qase_badge = f" [QASE #{qase_id}]" if qase_id else ""
    print(f"[*] ТЕСТ-КЕЙС:{qase_badge} {title}")
    if doc:
        print(f"[*] Описание: {doc}")
    print(f"[*] Модуль: {item.nodeid.split('::')[0]}::{item.cls.__name__ if item.cls else ''}")
    print("=" * 80)


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


