import os
import re
import json
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
sys.path.append(str(BASE_DIR))

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
N8N_URL = (os.getenv("N8N_URL") or os.getenv("N8N_SERVER_URL") or "http://201.34.147.33:5678").rstrip('/')
N8N_API_KEY = os.getenv("N8N_API_KEY")

def get_in_progress_issues():
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    jql = 'status = 10046 OR status = "In Progress"'
    try:
        res = requests.get(url, auth=(JIRA_EMAIL, JIRA_TOKEN), params={"jql": jql, "fields": "comment,labels,summary"}, timeout=10)
        res.raise_for_status()
        return res.json().get("issues", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка связи с API Jira: Не удалось получить задачи. Подробности: {e}")
        return []

def get_latest_execution_id(comments: list):
    for c in reversed(comments):
        match = re.search(r"\[N8N_EXECUTION_ID:\s*([^\]]+)\]", str(c.get("body", {})))
        if match:
            return match.group(1).strip()
    return None

def get_resume_token(exec_id: str):
    """Waiting webhooks in n8n require ?signature=<resumeToken>; it is only persisted once the execution reaches the Wait node."""
    try:
        res = requests.get(
            f"{N8N_URL}/api/v1/executions/{exec_id}",
            headers={"X-N8N-API-KEY": N8N_API_KEY},
            params={"includeData": "true"},
            timeout=30
        )
        res.raise_for_status()
        execution = res.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка связи с API n8n для execution {exec_id}: {e}")
        return None, None
    return execution.get("status"), (execution.get("data") or {}).get("resumeToken")

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

def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=BASE_DIR, check=check, capture_output=True, text=True)

def prepare_branch(issue_key: str) -> str:
    """Branch off the latest origin/main so the pushed commit carries the current GitHub Actions workflow."""
    branch_name = f"qa/{issue_key.lower()}"
    logger.info(f"Подготовка ветки {branch_name} от origin/main...")
    git("fetch", "origin")
    git("checkout", "-B", branch_name, "origin/main")
    return branch_name

def git_commit_and_push(issue_key: str, branch_name: str) -> bool:
    logger.info(f"Выполнение Git-операций для задачи {issue_key}...")
    try:
        # Индексируем файлы
        git("add", "tests/backend/", "tests/frontend/")
        git("add", "n8n_execution.json", check=False)

        if git("diff", "--cached", "--quiet", check=False).returncode == 0:
            logger.info("Нет изменений для коммита. Пропускаем.")
            return False

        logger.info("Создание коммита...")
        git("commit", "-m", f"🤖 Автоматическая генерация тестов для {issue_key}")

        logger.info(f"Пуш ветки {branch_name} на удаленный сервер...")
        push_res = git("push", "-u", "--force-with-lease", "origin", branch_name, check=False)
        if push_res.returncode != 0:
            logger.error(f"Коммит создан локально, но пуш отклонен: {push_res.stderr.strip()}")
            return False
        logger.info("✅ Файлы успешно закоммичены и отправлены в репозиторий!")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Критическая ошибка выполнения Git команд. Код возврата: {e.returncode}. Вывод: {e.stderr}")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в Git-операциях: {e}", exc_info=True)
    return False

def daemon_loop():
    logger.info("🚀 Запуск QA Агента-демона (Jira Poller). Ожидание задач...")
    
    if str(BASE_DIR / "scripts") not in sys.path:
        sys.path.insert(0, str(BASE_DIR / "scripts"))

    announced_pending = set()
        
    while True:
        try:
            issues = get_in_progress_issues()
            for issue in issues:
                issue_key = issue["key"]
                fields = issue.get("fields", {})
                labels = fields.get("labels", [])
                
                # If already labeled as autotests created, do not re-run
                if "qa-autotests-created" in labels:
                    continue

                comments = fields.get("comment", {}).get("comments", [])
                stage_7_body = None
                for c in comments:
                    body_text = str(c.get("body", {}))
                    if "Автотесты созданы и добавлены в проект" in body_text:
                        stage_7_body = body_text
                        break

                if stage_7_body:
                    exec_id = get_latest_execution_id(comments)
                    if exec_id:
                        logger.info(f"Найден n8n_execution ID: {exec_id} для {issue_key}")
                    else:
                        logger.info("N8N_EXECUTION_ID не указан в комментариях Jira")

                    logger.info(f"🎯 Обнаружен успешный пайплайн n8n для {issue_key}! Начинаем локальную генерацию тестов...")
                    try:
                        branch_name = f"qa/{issue_key.lower()}"
                        wt_dir = BASE_DIR / ".worktrees" / f"qa-{issue_key.lower()}"
                        wt_dir.parent.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Подготовка изолированного Git Worktree {wt_dir} для {branch_name}...")
                        git("fetch", "origin")
                        if wt_dir.exists():
                            subprocess.run(["git", "worktree", "remove", "--force", str(wt_dir)], cwd=BASE_DIR, capture_output=True)

                        add_res = subprocess.run(["git", "worktree", "add", "-B", branch_name, str(wt_dir), "origin/main"], cwd=BASE_DIR, capture_output=True, text=True)
                        if add_res.returncode != 0:
                            logger.error(f"Не удалось создать worktree: {add_res.stderr}")
                            continue

                        execution_file = wt_dir / "n8n_execution.json"
                        if exec_id:
                            with open(execution_file, "w") as f:
                                json.dump({"executionId": exec_id}, f)
                            logger.info(f"Сохранен n8n_execution.json с ID: {exec_id} в worktree")

                        summary = str(fields.get("summary", "")).lower()
                        is_frontend = ("tests/frontend" in stage_7_body and "tests/backend" not in stage_7_body) or "frontend" in summary or issue_key.upper() == "JS-16"
                        kind = "frontend" if is_frontend else ("backend" if "backend" in summary else "all")

                        logger.info(f"Определен тип задачи: {kind}. Генерация в изолированном Worktree...")
                        from scaffold_dynamic import generate_tests
                        generate_tests(issue_key, kind=kind, target_dir=wt_dir)
                        update_sqlite(issue_key)

                        # Git in worktree
                        subprocess.run(["git", "add", "tests/", "n8n_execution.json"], cwd=wt_dir, check=False)
                        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=wt_dir).returncode == 0:
                            logger.info("Нет изменений для коммита в worktree.")
                            subprocess.run(["git", "worktree", "remove", "--force", str(wt_dir)], cwd=BASE_DIR, capture_output=True)
                            continue

                        logger.info("Создание коммита в worktree...")
                        subprocess.run(["git", "commit", "-m", f"🤖 Автоматическая генерация тестов для {issue_key}"], cwd=wt_dir, check=True)
                        logger.info(f"Пуш ветки {branch_name} на удаленный сервер из worktree...")
                        push_res = subprocess.run(["git", "push", "-u", "--force-with-lease", "origin", branch_name], cwd=wt_dir, capture_output=True, text=True)

                        # Clean up worktree
                        subprocess.run(["git", "worktree", "remove", "--force", str(wt_dir)], cwd=BASE_DIR, capture_output=True)
                        logger.info(f"Worktree {wt_dir} успешно очищен.")

                        if push_res.returncode != 0:
                            logger.error(f"Ошибка пуша из worktree: {push_res.stderr.strip()}")
                            continue

                        logger.info("✅ Файлы успешно закоммичены и отправлены в репозиторий через Worktree!")
                        from scripts.hitl_review_gate import add_jira_label
                        add_jira_label(issue_key, "qa-autotests-created")
                        logger.info(f"✅ Полный цикл для {issue_key} успешно завершен.")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Ошибка выполнения Git-команды для {issue_key}: {e.stderr if hasattr(e, 'stderr') else e}")
                    except ImportError as e:
                        logger.error(f"Ошибка импорта модулей генерации: {e}")
                    except Exception as ex:
                        logger.error(f"Критическая ошибка при генерации или обработке тестов для {issue_key}: {ex}", exc_info=True)
                            
        except Exception as e:
            logger.error(f"Глобальная ошибка в цикле поллинга Jira: {e}", exc_info=True)
            
        time.sleep(10)

if __name__ == "__main__":
    daemon_loop()
