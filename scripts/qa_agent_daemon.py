import os
import time
import requests
import sqlite3
import subprocess
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Настройка системы логирования ---
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "qa_agent.log"

logger = logging.getLogger("QA_Daemon")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    fmt="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Вывод в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Вывод в файл с ротацией (максимум 5 файлов по 5 МБ)
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

load_dotenv(BASE_DIR / ".env")

JIRA_URL = (os.getenv("ATLASSIAN_BASE_URL") or "https://romeo-timony.atlassian.net").rstrip('/')
JIRA_EMAIL = os.getenv("ATLASSIAN_USER_EMAIL")
JIRA_TOKEN = os.getenv("ATLASSIAN_API_TOKEN")

def get_in_progress_issues():
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    jql = 'status = 10046 OR status = "In Progress"'
    try:
        res = requests.get(url, auth=(JIRA_EMAIL, JIRA_TOKEN), params={"jql": jql, "fields": "comment"}, timeout=10)
        res.raise_for_status()
        return res.json().get("issues", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка связи с API Jira: Не удалось получить задачи. Подробности: {e}")
        return []

def update_sqlite(issue_key: str):
    logger.info(f"Обновление локальной базы SQLite для задачи {issue_key}...")
    try:
        from scripts.qa_db import record_stage, upsert_task
        upsert_task(issue_key, f"Task {issue_key}", current_stage=7, status="COMPLETED")
        record_stage(
            issue_key=issue_key,
            stage_number=7,
            stage_name="Завершение: Автотесты созданы и добавлены в проект",
            status="COMPLETED",
            score=100,
            verdict="АВТОТЕСТЫ ВНЕДРЕНЫ",
            payload={"source": "Jira polling daemon"}
        )
        logger.info(f"База данных SQLite успешно обновлена для {issue_key}.")
    except ImportError:
        logger.error("Ошибка импорта: Не найден модуль scripts.qa_db. Проверьте структуру проекта.")
    except Exception as e:
        logger.error(f"Системная ошибка при обновлении SQLite: {e}", exc_info=True)

def git_commit_and_push(issue_key: str):
    logger.info(f"Выполнение Git-операций для задачи {issue_key}...")
    try:
        branch_name = f"qa/{issue_key.lower()}"
        
        # Индексируем файлы
        subprocess.run(["git", "add", "tests/backend/"], cwd=BASE_DIR, check=True, capture_output=True)
        subprocess.run(["git", "add", "tests/frontend/"], cwd=BASE_DIR, check=True, capture_output=True)
        
        status = subprocess.run(["git", "status", "--porcelain"], cwd=BASE_DIR, capture_output=True, text=True)
        if not status.stdout.strip():
            logger.info("Нет изменений для коммита. Пропускаем.")
            return

        # Переключаемся на новую ветку для безопасной работы команды
        logger.info(f"Создание новой ветки: {branch_name}")
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=BASE_DIR, capture_output=True)

        logger.info("Создание коммита...")
        subprocess.run(["git", "commit", "-m", f"🤖 Автоматическая генерация тестов для {issue_key}"], cwd=BASE_DIR, check=True, capture_output=True)
        
        logger.info("Пуш изменений на удаленный сервер...")
        push_res = subprocess.run(["git", "push", "-u", "qa", branch_name], cwd=BASE_DIR, capture_output=True, text=True)
        if push_res.returncode != 0:
            logger.warning(f"Коммит создан локально, но пуш отклонен (Возможно, нет прав 403): {push_res.stderr.strip()}")
        else:
            logger.info("✅ Файлы успешно закоммичены и отправлены в репозиторий!")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Критическая ошибка выполнения Git команд. Код возврата: {e.returncode}. Вывод: {e.stderr}")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в Git-операциях: {e}", exc_info=True)

def daemon_loop():
    logger.info("🚀 Запуск QA Агента-демона (Jira Poller). Ожидание задач...")
    
    if str(BASE_DIR / "scripts") not in sys.path:
        sys.path.insert(0, str(BASE_DIR / "scripts"))
        
    while True:
        try:
            issues = get_in_progress_issues()
            for issue in issues:
                issue_key = issue["key"]
                comments = issue.get("fields", {}).get("comment", {}).get("comments", [])
                
                has_stage_7 = any("Автотесты созданы и добавлены в проект" in str(c.get("body", {})) for c in comments)
                
                if has_stage_7:
                    safe_key = issue_key.lower().replace("-", "")
                    api_file = BASE_DIR / f"tests/backend/test_{safe_key}_api.py"
                    ui_file = BASE_DIR / f"tests/frontend/test_{safe_key}_ui.py"
                    
                    if not api_file.exists() or not ui_file.exists():
                        logger.info(f"🎯 Обнаружен успешный пайплайн n8n для {issue_key}! Начинаем локальную генерацию тестов...")
                        try:
                            from scaffold_dynamic import generate_tests
                            generate_tests(issue_key)
                            update_sqlite(issue_key)
                            git_commit_and_push(issue_key)
                            
                            from scripts.hitl_review_gate import add_jira_label
                            add_jira_label(issue_key, "qa-autotests-created")
                            logger.info(f"✅ Полный цикл для {issue_key} успешно завершен.")
                        except ImportError as e:
                            logger.error(f"Ошибка импорта модулей генерации: {e}")
                        except Exception as ex:
                            logger.error(f"Критическая ошибка при генерации или обработке тестов для {issue_key}: {ex}", exc_info=True)
                            
        except Exception as e:
            logger.error(f"Глобальная ошибка в цикле поллинга Jira: {e}", exc_info=True)
            
        time.sleep(10)

if __name__ == "__main__":
    daemon_loop()
