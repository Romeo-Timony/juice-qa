import os
import pytest
import allure
from pathlib import Path
from playwright.sync_api import Page
from dotenv import load_dotenv
from api.client import JuiceShopApiClient

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
VIDEOS_DIR = BASE_DIR / "allure-results" / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

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
    """Хук фиксации статуса выполнения теста для передачи в фикстуру артефактов."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)

@pytest.fixture(autouse=True)
def capture_artifacts_on_failure(request):
    """
    Автоматическое снятие скриншота и прикрепление видео-скринкаста при падении UI тестов.
    При успешном прохождении теста видео удаляется для экономии дискового пространства.
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

        # 2. Сохраняем и прикрепляем скринкаст видео
        try:
            if video:
                page.close()
                video_path = video.path()
                if os.path.exists(video_path):
                    allure.attach.file(
                        video_path,
                        name=f"Screencast_Failure_{test_name}",
                        attachment_type=allure.attachment_type.WEBM
                    )
        except Exception as e:
            print(f"Warning: could not attach failure video: {e}")
    else:
        # Если тест прошел успешно — удаляем видеофайл, оставляя только нужные артефакты
        try:
            if video:
                page.close()
                video_path = video.path()
                if os.path.exists(video_path):
                    os.remove(video_path)
        except Exception:
            pass
