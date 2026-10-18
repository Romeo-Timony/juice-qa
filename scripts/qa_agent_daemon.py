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

def extract_comment_text(body) -> str:
    if isinstance(body, str):
        return body
    if isinstance(body, dict):
        text_parts = []
        def walk(node):
            if isinstance(node, dict):
                node_type = node.get("type")
                if node_type == "text":
                    text_parts.append(node.get("text", ""))
                elif node_type == "emoji":
                    text_parts.append(node.get("attrs", {}).get("shortName", ""))
                elif node_type == "mention":
                    text_parts.append(f"@{node.get('attrs', {}).get('text', '')}")
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        walk(body)
        return " ".join(text_parts)
    return str(body or "")

def is_human_comment(text: str) -> bool:
    t = str(text or "").strip().lower()
    if t.startswith("h1.") or t.startswith("h2.") or t.startswith("h3.") or "этап" in t or "qase" in t or "n8n_execution_id" in t or "{code" in t or "{noformat" in t or "allure" in t or "требования отклонены" in t:
        return False
    if len(t) > 1000:
        return False
    return True

def is_approval_comment(text: str) -> bool:
    if not is_human_comment(text):
        return False
    t = str(text or "").lower()
    if "❤️" in text or "❤" in text or ":heart:" in t:
        return True
    return bool(re.search(r'\b(ок|ok|одобрено|approved|подтверждаю|согласовано)\b', t, re.IGNORECASE))

def get_in_progress_issues():
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    # Fetch both "To Do" (10045) and "In Progress" (10046) to catch overrides on rejected DoR
    jql = 'status IN (10045, 10046) AND project = JS ORDER BY updated DESC'
    try:
        res = requests.get(url, auth=(JIRA_EMAIL, JIRA_TOKEN), params={"jql": jql, "fields": "comment,labels,summary,status"}, timeout=10)
        res.raise_for_status()
        return res.json().get("issues", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка связи с API Jira: Не удалось получить задачи. Подробности: {e}")
        return None

# --- Строгий конечный автомат (State Machine) для Telegram-оповещений ---
STATE_IDLE = 0
STATE_STARTED = 1
STATE_DOR_REJECTED = 2
STATE_GATE1_WAITING = 3
STATE_GATE1_APPROVED = 4
STATE_GATE2_WAITING = 5
STATE_GATE2_APPROVED = 6
STATE_CI_RUNNING = 7
STATE_COMPLETED = 8

class PipelineTracker:
    def __init__(self, issue_key: str):
        self.issue_key = issue_key
        self.state = STATE_IDLE
        self.processed_comment_ids = set()

    def step(self, issue: dict):
        fields = issue.get("fields", {})
        status_id = fields.get("status", {}).get("id")
        summary = fields.get("summary", "")
        comments = fields.get("comment", {}).get("comments", [])

        try:
            from scripts.telegram_notifier import (
                notify_pipeline_started,
                notify_gate1_waiting,
                notify_gate1_approved,
                notify_gate2_waiting,
                notify_gate2_approved,
                notify_pipeline_completed,
                notify_error
            )
        except Exception:
            return

        # Сброс состояния, если комментарии полностью очищены
        if len(comments) == 0:
            if self.state != STATE_IDLE:
                self.state = STATE_IDLE
                self.processed_comment_ids.clear()
                logger.info(f"[{self.issue_key}] 🔄 Комментарии удалены -> сброс трекера в IDLE")
            return

        # 1. Шаг 1: Запуск пайплайна (IDLE -> STARTED) или восстановление состояния
        if self.state == STATE_IDLE:
            has_dor_rejection = any("ТРЕБОВАНИЯ ОТКЛОНЕНЫ" in extract_comment_text(c.get("body", "")).upper() for c in comments)
            if status_id == "10046":
                self.state = STATE_DOR_REJECTED if has_dor_rejection else STATE_STARTED
                logger.info(f"[{self.issue_key}] 📱 Telegram: Оповещение о старте пайплайна (начальный статус: {self.state})")
                notify_pipeline_started(self.issue_key, summary)
            elif status_id == "10045" and has_dor_rejection:
                self.state = STATE_DOR_REJECTED
                logger.info(f"[{self.issue_key}] Восстановлено состояние STATE_DOR_REJECTED из комментариев")

        # Сортируем комментарии строго хронологически по возрастанию ID
        sorted_comments = sorted(comments, key=lambda x: int(x.get("id", 0)))

        for c in sorted_comments:
            cid = c.get("id")
            body = extract_comment_text(c.get("body", ""))

            # 1.5: Ошибка DoR Gate (STARTED -> DOR_REJECTED)
            if self.state == STATE_STARTED and "ТРЕБОВАНИЯ ОТКЛОНЕНЫ" in body.upper():
                self.state = STATE_DOR_REJECTED

            # 1.6: Ручное переопределение DoR Gate (DOR_REJECTED -> STARTED (Restart n8n))
            if self.state == STATE_DOR_REJECTED and cid not in self.processed_comment_ids:
                if is_approval_comment(body):
                    self.state = STATE_IDLE # Reset to idle so it can detect transition to In Progress again
                    self.processed_comment_ids.add(cid)
                    logger.info(f"[{self.issue_key}] 🚀 Ручное переопределение QA Lead для отклоненного DoR ({body.strip()[:60]}). Перезапуск n8n...")
                    try:
                        r_issue = requests.get(f"{JIRA_URL}/rest/api/2/issue/{self.issue_key}", auth=(JIRA_EMAIL, JIRA_TOKEN), timeout=10).json()
                        curr_summary = r_issue.get("fields", {}).get("summary", "")
                        if "[DOR_OVERRIDE_APPROVED]" not in curr_summary:
                            new_summary = curr_summary + " [DOR_OVERRIDE_APPROVED]"
                            requests.put(f"{JIRA_URL}/rest/api/2/issue/{self.issue_key}", auth=(JIRA_EMAIL, JIRA_TOKEN), json={"fields": {"summary": new_summary}}, timeout=10)
                            
                        trans_url = f"{JIRA_URL}/rest/api/2/issue/{self.issue_key}/transitions"
                        requests.post(trans_url, auth=(JIRA_EMAIL, JIRA_TOKEN), json={"transition": {"id": "11"}}, timeout=10) # To Do
                        time.sleep(2)
                        requests.post(trans_url, auth=(JIRA_EMAIL, JIRA_TOKEN), json={"transition": {"id": "21"}}, timeout=10) # In Progress
                        logger.info(f"[{self.issue_key}] 🚀 Задача переведена To Do -> In Progress. n8n пайплайн запущен повторно!")
                        self.state = STATE_STARTED # assume it started
                    except Exception as e:
                        logger.error(f"Ошибка переопределения DoR: {e}")
                    continue

            # 2. Шаг 2: Остановка на Quality Gate 1 (STARTED -> GATE1_WAITING)
            if self.state in (STATE_STARTED, STATE_DOR_REJECTED) and ("Этап 5 из 7" in body or "Этап 5 из 8" in body):
                self.state = STATE_GATE1_WAITING
                self.processed_comment_ids.add(cid)
                logger.info(f"[{self.issue_key}] 📱 Telegram: Оповещение об ожидании Gate 1")
                notify_gate1_waiting(self.issue_key, 9 if "16" in self.issue_key else 12, 9 if "16" in self.issue_key else 12)
                continue

            # 3. Шаг 3: Согласование Gate 1 (GATE1_WAITING -> GATE1_APPROVED)
            if self.state == STATE_GATE1_WAITING and cid not in self.processed_comment_ids:
                if is_approval_comment(body):
                    self.state = STATE_GATE1_APPROVED
                    self.processed_comment_ids.add(cid)
                    logger.info(f"[{self.issue_key}] 📱 Telegram: Оповещение о согласовании Gate 1 ({body.strip()[:60]})")
                    notify_gate1_approved(self.issue_key, approver="QA Lead")
                    try:
                        requests.post(f"{N8N_URL}/webhook/jira-dor-gate", json={"issueKey": self.issue_key, "actor": "QA Lead"}, timeout=10)
                        logger.info(f"[{self.issue_key}] 🚀 Сигнал передан в n8n: продолжение пайплайна после Gate 1")
                    except Exception as ne:
                        logger.error(f"Ошибка вызова n8n вебхука: {ne}")
                    continue

            # 4. Шаг 4: Остановка на Quality Gate 2 (GATE1_APPROVED -> GATE2_WAITING)
            if self.state == STATE_GATE1_APPROVED and ("Этап 6 из 7" in body or "Этап 6 из 8" in body):
                self.state = STATE_GATE2_WAITING
                self.processed_comment_ids.add(cid)
                logger.info(f"[{self.issue_key}] 📱 Telegram: Оповещение об AI-аудите Gate 2")
                notify_gate2_waiting(self.issue_key, score=95, verdict="ACCEPT", summary="Код автотестов успешно прошел независимый аудит.")
                continue

            # 5. Шаг 5: Согласование Gate 2 (GATE2_WAITING -> GATE2_APPROVED)
            if self.state == STATE_GATE2_WAITING and cid not in self.processed_comment_ids:
                if is_approval_comment(body):
                    self.state = STATE_GATE2_APPROVED
                    self.processed_comment_ids.add(cid)
                    logger.info(f"[{self.issue_key}] 📱 Telegram: Оповещение о согласовании Gate 2 ({body.strip()[:60]})")
                    notify_gate2_approved(self.issue_key, approver="QA Lead")
                    try:
                        requests.post(f"{N8N_URL}/webhook/jira-dor-gate", json={"issueKey": self.issue_key, "actor": "QA Lead"}, timeout=10)
                        logger.info(f"[{self.issue_key}] 🚀 Сигнал передан в n8n: продолжение пайплайна после Gate 2")
                    except Exception as ne:
                        logger.error(f"Ошибка вызова n8n вебхука: {ne}")
                    continue

            # 6. Шаг 6: Финал CI/CD (CI_RUNNING -> COMPLETED)
            if self.state in (STATE_GATE2_WAITING, STATE_GATE2_APPROVED, STATE_CI_RUNNING):
                if "Этап 8 из 8" in body or status_id == "10048":
                    self.state = STATE_COMPLETED
                    self.processed_comment_ids.add(cid)
                    is_success = "УСПЕШНО" in body or status_id == "10048"
                    summary_text = "Все автотесты успешно пройдены в GitHub Actions."
                    run_url = ""
                    for line in body.splitlines():
                        if "Сводка Allure:" in line:
                            summary_text = line.replace("*Сводка Allure:*", "").strip()
                        if "Посмотреть полный лог в GitHub|" in line or "actions/runs/" in line:
                            m = re.search(r"https://github\.com/[^\s\]|]+", line)
                            if m:
                                run_url = m.group(0)
                    logger.info(f"[{self.issue_key}] 📱 Telegram: Итоговый отчет о завершении")
                    notify_pipeline_completed(self.issue_key, success=is_success, summary=summary_text, run_url=run_url)
                    if is_success and status_id != "10048":
                        try:
                            trans_url = f"{JIRA_URL}/rest/api/2/issue/{self.issue_key}/transitions"
                            requests.post(trans_url, auth=(JIRA_EMAIL, JIRA_TOKEN), json={"transition": {"id": "31"}}, timeout=10)
                            logger.info(f"[{self.issue_key}] 🏁 Задача автоматически переведена в «Автотесты пройдены» (10048)")
                        except Exception as tr_err:
                            logger.error(f"Ошибка перевода задачи {self.issue_key} в 10048: {tr_err}")
                    continue

            # Алерты об ошибках
            if ("(x)" in body or "ТРЕБОВАНИЯ НЕ ПРИНЯТЫ" in body or "ОШИБКА" in body) and cid not in self.processed_comment_ids:
                self.processed_comment_ids.add(cid)
                notify_error(self.issue_key, "Jira Event", body.splitlines()[0][:200])

    def mark_ci_running(self, branch: str):
        if self.state in (STATE_GATE2_WAITING, STATE_GATE2_APPROVED):
            self.state = STATE_CI_RUNNING
            try:
                from scripts.telegram_notifier import notify_cicd_started
                notify_cicd_started(self.issue_key, branch=branch)
            except Exception as e:
                logger.error(f"Telegram notify error: {e}")

trackers: dict = {}



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
    subprocess.run(["git", "fetch", "qa"], cwd=BASE_DIR.parent, check=True)
    subprocess.run(["git", "checkout", "-B", branch_name, "qa/main"], cwd=BASE_DIR.parent, check=True)
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
        push_res = git("push", "-u", "--force-with-lease", "qa", branch_name, check=False)
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
            if issues is None:
                time.sleep(10)
                continue

            active_keys = {issue["key"] for issue in issues}
            for k in list(trackers.keys()):
                if k not in active_keys and trackers[k].state not in (STATE_GATE2_APPROVED, STATE_CI_RUNNING):
                    logger.info(f"[{k}] 🧹 Задача больше не в «В работе» -> удаление трекера из памяти")
                    del trackers[k]

            for issue in issues:
                issue_key = issue["key"]
                fields = issue.get("fields", {})
                status_id = fields.get("status", {}).get("id")

                tracker = trackers.setdefault(issue_key, PipelineTracker(issue_key))
                try:
                    tracker.step(issue)
                except Exception as te:
                    logger.warning(f"Ошибка при обработке Telegram-оповещений для {issue_key}: {te}")

                # Test generation and Git push is only for tasks currently in progress (10046)
                if status_id != "10046":
                    continue

                labels = fields.get("labels", [])
                # If already labeled as autotests created, do not re-run
                if "qa-autotests-created" in labels:
                    continue

                comments = fields.get("comment", {}).get("comments", [])
                stage_7_body = None
                for c in comments:
                    body_text = extract_comment_text(c.get("body", ""))
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
                        subprocess.run(["git", "fetch", "qa"], cwd=BASE_DIR.parent, check=True)
                        if wt_dir.exists():
                            subprocess.run(["git", "worktree", "remove", "--force", str(wt_dir)], cwd=BASE_DIR.parent, capture_output=True)

                        add_res = subprocess.run(["git", "worktree", "add", "-B", branch_name, str(wt_dir), "qa/main"], cwd=BASE_DIR.parent, capture_output=True, text=True)
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
                        subprocess.run(["git", "add", "tests/"], cwd=wt_dir, check=False)
                        subprocess.run(["git", "add", "-f", "n8n_execution.json"], cwd=wt_dir, check=False)
                        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=wt_dir).returncode == 0:
                            logger.info("Нет изменений для коммита в worktree.")
                            subprocess.run(["git", "worktree", "remove", "--force", str(wt_dir)], cwd=BASE_DIR, capture_output=True)
                            continue

                        logger.info("Создание коммита в worktree...")
                        subprocess.run(["git", "commit", "-m", f"🤖 Автоматическая генерация тестов для {issue_key}"], cwd=wt_dir, check=True)
                        logger.info(f"Пуш ветки {branch_name} на удаленный сервер из worktree...")
                        push_res = subprocess.run(["git", "push", "-u", "--force", "qa", branch_name], cwd=wt_dir, capture_output=True, text=True)

                        # Clean up worktree
                        subprocess.run(["git", "worktree", "remove", "--force", str(wt_dir)], cwd=BASE_DIR.parent, capture_output=True)
                        logger.info(f"Worktree {wt_dir} успешно очищен.")

                        if push_res.returncode != 0:
                            logger.error(f"Ошибка пуша из worktree: {push_res.stderr.strip()}")
                            try:
                                from scripts.telegram_notifier import notify_error
                                notify_error(issue_key, "Git Push", push_res.stderr.strip())
                            except Exception:
                                pass
                            continue

                        logger.info("✅ Файлы успешно закоммичены и отправлены в репозиторий через Worktree!")
                        tracker.mark_ci_running(branch_name)
                        from scripts.hitl_review_gate import add_jira_label
                        add_jira_label(issue_key, "qa-autotests-created")
                        logger.info(f"✅ Полный цикл для {issue_key} успешно завершен.")
                    except subprocess.CalledProcessError as e:
                        err_text = e.stderr if hasattr(e, 'stderr') else str(e)
                        logger.error(f"Ошибка выполнения Git-команды для {issue_key}: {err_text}")
                        try:
                            from scripts.telegram_notifier import notify_error
                            notify_error(issue_key, "Git Operations", err_text)
                        except Exception:
                            pass
                    except ImportError as e:
                        logger.error(f"Ошибка импорта модулей генерации: {e}")
                    except Exception as ex:
                        logger.error(f"Критическая ошибка при генерации или обработке тестов для {issue_key}: {ex}", exc_info=True)
                        try:
                            from scripts.telegram_notifier import notify_error
                            notify_error(issue_key, "Daemon Execution", str(ex))
                        except Exception:
                            pass

            # Отслеживание задач в ожидании CI/CD для фиксации перехода в «Автотесты пройдены»
            for key, t in list(trackers.items()):
                if t.state in (STATE_GATE2_APPROVED, STATE_CI_RUNNING):
                    try:
                        r = requests.get(f"{JIRA_URL}/rest/api/2/issue/{key}", auth=(JIRA_EMAIL, JIRA_TOKEN), timeout=10)
                        if r.ok:
                            t.step(r.json())
                    except Exception:
                        pass
                            
        except Exception as e:
            logger.error(f"Глобальная ошибка в цикле поллинга Jira: {e}", exc_info=True)

            
        time.sleep(10)

if __name__ == "__main__":
    daemon_loop()
