import os
import re
import json
import time
import requests
import sqlite3
import subprocess
import sys
import shutil
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "scripts"))

from qaops import idempotency  # noqa: E402
from qaops.config import settings as qaops_settings  # noqa: E402
from qaops.jira import comment_once, transition_once  # noqa: E402
from qaops.observability import trace  # noqa: E402

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

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

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
    t_clean = re.sub(r'\s+', ' ', t)
    
    # Check for any robot/pipeline template markers
    robot_markers = [
        "h1.", "h2.", "h3.", "[этап", "этап 1", "этап 2", "этап 3", "этап 4", 
        "этап 5", "этап 6", "этап 7", "этап 8", "контроль 1", "контроль 2",
        "quality gate", "dor gate", "n8n_execution_id", "{code", "{noformat",
        "allure", "требования отклонены", "оценка качества проверок",
        "текущее решение", "состав проверок", "проверенная задача",
        "для перехода к генерации"
    ]
    for marker in robot_markers:
        if marker in t_clean:
            return False
            
    # Real human approval comments are short (usually 1-100 characters)
    if len(t) > 200:
        return False
    return True

def is_approval_comment(text: str) -> bool:
    # 1. MUST be a genuine human comment first (never a robot card)
    if not is_human_comment(text):
        return False
        
    cleaned = str(text or "").strip().rstrip(".!").strip()
    # Строго только комментарий «ОК» с больших букв (русская О+К или латинская O+K)
    return cleaned in ("ОК", "OK")

def extract_delta_requirements(text: str) -> Optional[str]:
    t = str(text or "").strip()
    if not is_human_comment(t):
        return None
    if re.search(r"(@qa-bot|\[ДОПОЛНЕНИЕ\]|\[QA-AMEND\]|\[ТРЕБОВАНИЯ-ДЕЛЬТА\]|дополнительные требования)", t, re.IGNORECASE):
        cleaned = re.sub(r"(?i)@qa-bot|\[ДОПОЛНЕНИЕ.*?\]|\[QA-AMEND\]|\[ТРЕБОВАНИЯ-ДЕЛЬТА\]", "", t).strip()
        return cleaned or t
    return None

def update_stage_comment_in_jira(issue_key: str, stage_tag: str, new_body: str):
    """Находит комментарий по тегу этапа (например '[Этап 1 из' или '[Этап 5 из') и обновляет его in-place (PUT)."""
    comments_url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/comment"
    try:
        res = requests.get(comments_url, auth=(JIRA_EMAIL, JIRA_TOKEN), timeout=15)
        if res.ok:
            for c in res.json().get("comments", []):
                c_body = str(c.get("body", ""))
                if stage_tag in c_body:
                    cid = c["id"]
                    requests.put(f"{comments_url}/{cid}", auth=(JIRA_EMAIL, JIRA_TOKEN), json={"body": new_body}, timeout=15)
                    logger.info(f"[{issue_key}] 🔄 In-place PUT обновление комментария Jira (ID={cid}, {stage_tag})")
                    return cid
    except Exception as e:
        logger.error(f"Ошибка обновления комментария в Jira: {e}")
    return None

def get_in_progress_issues():
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    jql = 'status IN (10045, 10046, 10048) AND project = JS ORDER BY updated DESC'
    try:
        res = requests.get(url, auth=(JIRA_EMAIL, JIRA_TOKEN), params={"jql": jql, "fields": "comment,labels,summary,status"}, timeout=10)
        res.raise_for_status()
        return res.json().get("issues", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка связи с API Jira: Не удалось получить задачи. Подробности: {e}")
        return None

# --- Строгий конечный автомат (State Machine) для Telegram-оповещений и Human-in-the-Loop ---
STATE_IDLE = 0
STATE_STARTED = 1
STATE_DOR_REJECTED = 2
STATE_GATE1_WAITING = 3
STATE_GATE1_APPROVED = 4
STATE_GATE2_WAITING = 5
STATE_GATE2_APPROVED = 6
STATE_CI_RUNNING = 7
STATE_COMPLETED = 8
STATE_PAUSED = 9

class PipelineTracker:
    def __init__(self, issue_key: str):
        self.issue_key = issue_key
        self.state = STATE_IDLE
        self.resume_state = STATE_IDLE
        self.processed_comment_ids = set()
        self.sent_notifications = set()

    def pause(self, resume_state: int, reason: str):
        self.state = STATE_PAUSED
        self.resume_state = resume_state
        logger.warning(f"[{self.issue_key}] ⏸️ QAOps: пайплайн на паузе ({reason}). Снимите метку {qaops_settings.paused_label} для продолжения.")

    def step(self, issue: dict):
        fields = issue.get("fields", {})
        status_id = fields.get("status", {}).get("id")
        summary = fields.get("summary", "")
        comments = fields.get("comment", {}).get("comments", [])
        labels = fields.get("labels", []) or []

        if self.state == STATE_PAUSED:
            if qaops_settings.paused_label in labels:
                return
            self.state = self.resume_state
            logger.info(f"[{self.issue_key}] ▶️ QAOps: метка {qaops_settings.paused_label} снята -> возобновление в состояние {self.state} (нужно новое согласование)")

        try:
            from scripts.telegram_notifier import (
                notify_pipeline_started,
                notify_dor_rejected,
                notify_gate1_waiting,
                notify_gate1_approved,
                notify_gate2_waiting,
                notify_gate2_approved,
                notify_cicd_started,
                notify_pipeline_completed,
                notify_error
            )
        except Exception:
            return

        # При полной очистке комментариев сбрасываем трекер в начальное состояние
        if len(comments) == 0:
            if self.state != STATE_IDLE:
                self.state = STATE_IDLE
                self.processed_comment_ids.clear()
                self.sent_notifications.clear()
                logger.info(f"[{self.issue_key}] 🔄 Задача очищена -> сброс трекера в STATE_IDLE")
            return

        sorted_comments = sorted(comments, key=lambda x: int(x.get("id", 0)))
        
        # 0. Проверяем наличие дельта-комментариев на доработку требований (@qa-bot [ДОПОЛНЕНИЕ])
        for c in sorted_comments:
            cid = c.get("id")
            if cid not in self.processed_comment_ids:
                body = extract_comment_text(c.get("body", ""))
                delta_text = extract_delta_requirements(body)
                if delta_text:
                    self.processed_comment_ids.add(cid)
                    author = (c.get("author") or {}).get("displayName", "QA Lead")
                    with idempotency.idempotent("jira.delta_comment", self.issue_key, str(cid)) as guard:
                        if guard.duplicate:
                            logger.info(f"[{self.issue_key}] ♻️ Дельта-комментарий ID={cid} уже был обработан ранее — повторная обработка заблокирована.")
                        else:
                            logger.info(f"[{self.issue_key}] ➕ Обработка новых дельта-требований (ID={cid}): {delta_text[:80]}")
                            try:
                                from scripts.qaops_delta_refine import process_delta_requirements
                                res = process_delta_requirements(self.issue_key, delta_text, author=author)
                                guard.complete(res)
                            except Exception as de:
                                logger.error(f"[{self.issue_key}] Ошибка обработки дельта-требований: {de}", exc_info=True)

        # 1. Проверяем наличие DoR отказа
        dor_reject_comment = next((c for c in sorted_comments if "ТРЕБОВАНИЯ ОТКЛОНЕНЫ" in extract_comment_text(c.get("body", "")).upper()), None)
        has_override = "[DOR_OVERRIDE_APPROVED]" in summary

        if self.state == STATE_IDLE:
            if status_id == "10046" and not dor_reject_comment:
                self.state = STATE_STARTED
                if "started" not in self.sent_notifications:
                    notify_pipeline_started(self.issue_key, summary)
                    self.sent_notifications.add("started")
            elif dor_reject_comment and not has_override:
                self.state = STATE_DOR_REJECTED
                if "dor_rejected" not in self.sent_notifications:
                    body = extract_comment_text(dor_reject_comment.get("body", ""))
                    score_match = re.search(r"Итоговый балл:\s*(\d+)%", body)
                    score = int(score_match.group(1)) if score_match else 0
                    notify_dor_rejected(self.issue_key, score=score, blockers="C06 — Не описано поведение системы при ошибках")
                    self.sent_notifications.add("dor_rejected")
            elif has_override:
                self.state = STATE_STARTED

        # 1.5. Ручное переопределение DoR: пользователь написал «ОК»
        if self.state == STATE_DOR_REJECTED and not has_override and dor_reject_comment:
            for c in sorted_comments:
                cid = c.get("id")
                if int(cid) > int(dor_reject_comment.get("id", 0)):
                    body = extract_comment_text(c.get("body", ""))
                    if is_approval_comment(body) and cid not in self.processed_comment_ids:
                        self.processed_comment_ids.add(cid)
                        logger.info(f"[{self.issue_key}] 🚀 Ручное переопределение DoR: '{body.strip()[:60]}'.")
                        
                        # In-place PUT обновление комментария [Этап 1 из 8]
                        st1_body = extract_comment_text(dor_reject_comment.get("body", ""))
                        updated_st1 = st1_body.replace("(x) ТРЕБОВАНИЯ ОТКЛОНЕНЫ (DoR FAIL)", "(/) ТРЕБОВАНИЯ ПРИНЯТЫ (DoR Override by QA Lead)")
                        updated_st1 = updated_st1.replace("(x) Задача возвращена в статус «К выполнению».", "(/) Требования согласованы QA Lead (Ручное переопределение).")
                        update_stage_comment_in_jira(self.issue_key, "[Этап 1 из", updated_st1)

                        # Добавляем маркер [DOR_OVERRIDE_APPROVED] в summary
                        new_summary = summary if "[DOR_OVERRIDE_APPROVED]" in summary else summary + " [DOR_OVERRIDE_APPROVED]"
                        requests.put(f"{JIRA_URL}/rest/api/2/issue/{self.issue_key}", auth=(JIRA_EMAIL, JIRA_TOKEN), json={"fields": {"summary": new_summary}}, timeout=10)
                        
                        # Переводим в «В работе» (10046)
                        transition_once(self.issue_key, "21", scope_key=f"dor-override:{cid}")
                        
                        self.state = STATE_STARTED
                        if "started" not in self.sent_notifications:
                            notify_pipeline_started(self.issue_key, summary)
                            self.sent_notifications.add("started")
                        logger.info(f"[{self.issue_key}] 🚀 Задача переведена в «В работе». n8n запускает этапы 1-5.")
                        break



        # 2. Остановка на Quality Gate 1 (Этап 5)
        stage5_comments = [c for c in sorted_comments if "[этап 5 из" in extract_comment_text(c.get("body", "")).lower() or "контроль 1" in extract_comment_text(c.get("body", "")).lower()]
        stage5_comment = stage5_comments[-1] if stage5_comments else None
        if stage5_comment and self.state in (STATE_STARTED, STATE_DOR_REJECTED):
            self.state = STATE_GATE1_WAITING
            if "gate1_waiting" not in self.sent_notifications:
                notify_gate1_waiting(self.issue_key, 12, 12)
                self.sent_notifications.add("gate1_waiting")
                logger.info(f"[{self.issue_key}] 📱 Telegram: Оповещение об ожидании Gate 1 (Human-in-the-Loop пауза)")

        # 3. Согласование Quality Gate 1: пользователь написал «ОК»
        if self.state == STATE_GATE1_WAITING and stage5_comment:
            for c in sorted_comments:
                cid = c.get("id")
                if int(cid) > int(stage5_comment.get("id", 0)):
                    body = extract_comment_text(c.get("body", ""))
                    if is_approval_comment(body) and cid not in self.processed_comment_ids:
                        self.processed_comment_ids.add(cid)
                        self.state = STATE_GATE1_APPROVED
                        if "gate1_approved" not in self.sent_notifications:
                            notify_gate1_approved(self.issue_key, approver="QA Lead")
                            self.sent_notifications.add("gate1_approved")
                        logger.info(f"[{self.issue_key}] 📱 Telegram: Оповещение о согласовании Gate 1 ({body.strip()[:60]})")

                        # In-place PUT обновление карточки Gate 1 на ОДОБРЕНО
                        st5_body = extract_comment_text(stage5_comment.get("body", ""))
                        updated_st5 = st5_body.replace("⏳ *ОЖИДАЕТ СОГЛАСОВАНИЯ QA LEAD*", "(/) *ОДОБРЕНО*")
                        updated_st5 = updated_st5.replace("Ожидает проверки QA Lead", "QA Lead (Human in the Loop)")
                        update_stage_comment_in_jira(self.issue_key, "[Этап 5 из", updated_st5)

                        # Ставим метки в Jira
                        from hitl_review_gate import add_jira_label
                        add_jira_label(self.issue_key, "qa-ready-for-autotests")

                        # Генерация реальных тестов строго по профилю задачи (backend vs frontend vs e2e)
                        if re.search(r"\[\s*e2e\s*\]|\[\s*end-to-end\s*\]|e2e\b|journey|онбординг", summary, re.I):
                            task_kind = "e2e"
                        elif re.search(r"\[\s*frontend\s*\]|frontend|angular|ui\b", summary, re.I):
                            task_kind = "frontend"
                        else:
                            task_kind = "backend"
                        with trace("pipeline.gate1_to_gate2", issue_key=self.issue_key, input={"kind": task_kind}, tags=["daemon"]) as tr:
                            from qaops.seams import check_issue_contract, run_design_seam
                            from scaffold_dynamic import fetch_qase_cases, generate_tests

                            if not check_issue_contract(self.issue_key):
                                self.pause(STATE_GATE1_WAITING, "Seam 1: нарушен контракт задачи")
                                break
                            if not run_design_seam(self.issue_key, fetch_qase_cases(self.issue_key)):
                                self.pause(STATE_GATE1_WAITING, "Seam 2: Test Design Integrity ниже порога")
                                break

                            logger.info(f"[{self.issue_key}] 🛠️ Запуск генерации автотестов (scaffold_dynamic, kind={task_kind})...")
                            generate_tests(self.issue_key, kind=task_kind, target_dir=BASE_DIR / "tests" / "review")

                            # Seam 3 (AST + ruff + pytest --collect-only) -> AI-аудит -> [Этап 6 из 8] с Evidence Pack
                            logger.info(f"[{self.issue_key}] 🔍 Статический гейт и AI-аудит автотестов (Gate 2 Staging Review)...")
                            from hitl_review_gate import run_staging_review
                            review_ok = run_staging_review(self.issue_key)
                            tr.output = {"review_ok": review_ok}
                        if not review_ok:
                            self.pause(STATE_GATE1_WAITING, "Seam 3: код автотестов не собирается или отклонён аудитором")
                            break

                        # Возобновляем воркфлоу n8n из Gate 1 Wait -> переход к Gate 2
                        logger.info(f"[{self.issue_key}] 🚀 Возобновление воркфлоу n8n из Gate 1...")
                        resume_n8n_execution(self.issue_key)

                        # Переводим в состояние ожидания согласования Gate 2
                        self.state = STATE_GATE2_WAITING
                        if "gate2_waiting" not in self.sent_notifications:
                            notify_gate2_waiting(self.issue_key, score=95, verdict="ACCEPT", summary="Код автотестов успешно прошел независимый аудит.")
                            self.sent_notifications.add("gate2_waiting")
                            logger.info(f"[{self.issue_key}] 📱 Telegram: Оповещение об ожидании Gate 2 (Human-in-the-Loop пауза)")
                        break

        # 4. Согласование Quality Gate 2: пользователь написал «ОК»
        stage6_comments = [c for c in sorted_comments if "[этап 6 из" in extract_comment_text(c.get("body", "")).lower() or "контроль 2" in extract_comment_text(c.get("body", "")).lower()]
        stage6_comment = stage6_comments[-1] if stage6_comments else None
        if self.state == STATE_GATE2_WAITING and stage6_comment:
            for c in sorted_comments:
                cid = c.get("id")
                if int(cid) > int(stage6_comment.get("id", 0)):
                    body = extract_comment_text(c.get("body", ""))
                    if is_approval_comment(body) and cid not in self.processed_comment_ids:
                        self.processed_comment_ids.add(cid)
                        self.state = STATE_GATE2_APPROVED
                        if "gate2_approved" not in self.sent_notifications:
                            notify_gate2_approved(self.issue_key, approver="QA Lead")
                            self.sent_notifications.add("gate2_approved")
                        logger.info(f"[{self.issue_key}] 📱 Telegram: Оповещение о согласовании Gate 2 ({body.strip()[:60]})")

                        # Промоушн файлов автотестов в боевую папку и публикация Этапа 7
                        logger.info(f"[{self.issue_key}] 🚀 Промоушн автотестов в репозиторий (promote_files)...")
                        from hitl_review_gate import promote_files
                        promote_files("QA Lead", self.issue_key)

                        # Создаем ветку и пушим в репозиторий
                        branch_name = f"qa/{self.issue_key.lower()}"
                        wt_dir = BASE_DIR.parent / ".worktrees" / f"qa-{self.issue_key.lower()}"
                        wt_dir.parent.mkdir(parents=True, exist_ok=True)
                        promoted_backend = sorted((BASE_DIR / "tests" / "backend").glob(f"*{self.issue_key.lower().replace('-', '')}*.py"))
                        promoted_frontend = sorted((BASE_DIR / "tests" / "frontend").glob(f"*{self.issue_key.lower().replace('-', '')}*.py"))
                        promoted = promoted_backend + promoted_frontend
                        content_digest = idempotency.make_key("files", *[(p.name, p.read_text(encoding="utf-8")) for p in promoted])
                        try:
                            with idempotency.idempotent("git.push", self.issue_key, branch_name, content_digest) as push_guard:
                                if push_guard.duplicate:
                                    logger.info(f"[{self.issue_key}] ♻️ Идентичный набор тестов уже запушен в {branch_name} — повторный push заблокирован.")
                                else:
                                    subprocess.run(["git", "fetch", "qa"], cwd=BASE_DIR.parent, check=True)
                                    if wt_dir.exists():
                                        subprocess.run(["git", "worktree", "remove", "--force", str(wt_dir)], cwd=BASE_DIR.parent, capture_output=True)
                                    subprocess.run(["git", "worktree", "add", "-B", branch_name, str(wt_dir), "qa/main"], cwd=BASE_DIR.parent, check=True)

                                    if promoted_backend:
                                        (wt_dir / "tests" / "backend").mkdir(parents=True, exist_ok=True)
                                        for f in promoted_backend:
                                            shutil.copy(f, wt_dir / "tests" / "backend" / f.name)
                                    if promoted_frontend:
                                        (wt_dir / "tests" / "frontend").mkdir(parents=True, exist_ok=True)
                                        for f in promoted_frontend:
                                            shutil.copy(f, wt_dir / "tests" / "frontend" / f.name)

                                    subprocess.run(["git", "add", "tests/"], cwd=wt_dir, check=False)
                                    subprocess.run(["git", "commit", "-m", f"🤖 Автоматическая генерация тестов для {self.issue_key}"], cwd=wt_dir, check=False)
                                    push_res = subprocess.run(["git", "push", "-u", "--force", "qa", branch_name], cwd=wt_dir, capture_output=True, text=True)
                                    subprocess.run(["git", "push", "qa", f"{branch_name}:main"], cwd=wt_dir, capture_output=True, text=True)
                                    subprocess.run(["git", "worktree", "remove", "--force", str(wt_dir)], cwd=BASE_DIR.parent, capture_output=True)
                                    if push_res.returncode != 0:
                                        raise RuntimeError(push_res.stderr[-500:])
                                    push_guard.complete({"branch": branch_name})
                                    logger.info(f"[{self.issue_key}] ✅ Ветка {branch_name} и main успешно обновлены в репозитории.")

                                    # Возобновляем воркфлоу n8n из Gate 2 Wait -> Отчет 7 и запуск GitHub Actions CI/CD
                                    logger.info(f"[{self.issue_key}] 🚀 Возобновление воркфлоу n8n из Gate 2...")
                                    resume_n8n_execution(self.issue_key)
                        except Exception as ge:
                            logger.error(f"Git push error: {ge}")

                        self.state = STATE_CI_RUNNING
                        if "cicd_started" not in self.sent_notifications:
                            notify_cicd_started(self.issue_key, branch=branch_name)
                            self.sent_notifications.add("cicd_started")
                            logger.info(f"[{self.issue_key}] 📱 Telegram: Оповещение о старте CI/CD")
                        break

        # 5. Завершение прогона в GitHub Actions (Этап 8)
        stage8_comment = next((c for c in sorted_comments if "[Этап 8 из 8]" in extract_comment_text(c.get("body", ""))), None)
        if self.state in (STATE_GATE2_APPROVED, STATE_CI_RUNNING):
            if stage8_comment or status_id == "10048":
                self.state = STATE_COMPLETED
                if "completed" not in self.sent_notifications:
                    is_success = "УСПЕШНО" in extract_comment_text(stage8_comment.get("body", "") if stage8_comment else "") or status_id == "10048"
                    notify_pipeline_completed(self.issue_key, success=is_success, summary="Все автотесты успешно выполнены в GitHub Actions, сформирован отчет Allure.")
                    self.sent_notifications.add("completed")
                    logger.info(f"[{self.issue_key}] 🏁 Пайплайн завершен, отправлено итоговое Telegram-уведомление.")
                if status_id != "10048":
                    stage8_id = stage8_comment.get("id") if stage8_comment else "status"
                    if transition_once(self.issue_key, "31", scope_key=f"stage8:{stage8_id}"):
                        logger.info(f"[{self.issue_key}] 🏁 Задача переведена в «Автотесты пройдены» (10048)")
                if "release_quality" not in self.sent_notifications:
                    try:
                        from qaops.metrics import format_jira, release_quality
                        report = release_quality(self.issue_key)
                        body = "\n".join(["h3. 🏁 QAOps: Итоговое решение Go/No-Go по релизу", *format_jira(report)])
                        comment_once(self.issue_key, body, scope_key=f"release-quality:{stage8_comment.get('id') if stage8_comment else 'status'}")
                        logger.info(f"[{self.issue_key}] 📈 Индекс качества релиза: {report['release_quality_index']} ({report['decision']})")
                    except Exception as qe:
                        logger.warning(f"[{self.issue_key}] Индекс качества релиза не рассчитан: {qe}")
                    self.sent_notifications.add("release_quality")

trackers: dict = {}


def get_latest_execution_id(comments: list):
    for c in reversed(comments):
        match = re.search(r"\[N8N_EXECUTION_ID:\s*([^\]]+)\]", str(c.get("body", {})))
        if match:
            return match.group(1).strip()
    return None

def resume_n8n_execution(issue_key: str, max_retries: int = 5, delay: float = 2.0) -> bool:
    """Находит ожидающее (status=waiting) execution воркфлоу n8n для задачи issue_key и возобновляет его."""
    for attempt in range(1, max_retries + 1):
        try:
            res = requests.get(
                f"{N8N_URL}/api/v1/executions?limit=20",
                headers={"X-N8N-API-KEY": N8N_API_KEY},
                timeout=15
            )
            if not res.ok:
                logger.error(f"[{issue_key}] Ошибка запроса executions к n8n ({res.status_code}): {res.text}")
                time.sleep(delay)
                continue

            for ex in res.json().get("data", []):
                eid = ex.get("id")
                if ex.get("status") != "waiting":
                    continue

                detail_res = requests.get(
                    f"{N8N_URL}/api/v1/executions/{eid}?includeData=true",
                    headers={"X-N8N-API-KEY": N8N_API_KEY},
                    timeout=20
                )
                if not detail_res.ok:
                    continue

                detail = detail_res.json()
                run_data = (detail.get("data") or {}).get("resultData", {}).get("runData", {})
                filter_node = run_data.get("Фильтр: Задача взята в работу")
                if not filter_node:
                    continue
                main_out = filter_node[0].get("data", {}).get("main", [[]])
                if not main_out or not main_out[0]:
                    continue
                item_key = main_out[0][0].get("json", {}).get("issueKey")
                if item_key != issue_key:
                    continue

                last_node = (detail.get("data") or {}).get("resultData", {}).get("lastNodeExecuted")
                resume_token = (detail.get("data") or {}).get("resumeToken")
                logger.info(f"[{issue_key}] 🎯 Найдено waiting execution n8n ID={eid}, lastNode={last_node}")

                resume_url = None
                if last_node and last_node in run_data:
                    node_runs = run_data[last_node]
                    if node_runs:
                        resume_url = node_runs[-1].get("metadata", {}).get("resumeUrl")

                if not resume_url and resume_token:
                    resume_url = f"{N8N_URL}/webhook-waiting/{eid}?signature={resume_token}"
                elif resume_url:
                    resume_url = re.sub(r"https?://[^/]+", N8N_URL, resume_url)

                if resume_url:
                    logger.info(f"[{issue_key}] 🚀 Возобновление execution n8n: {resume_url}")
                    try:
                        trig_res = requests.get(resume_url, timeout=20)
                        if trig_res.status_code == 404:
                            trig_res = requests.post(resume_url, timeout=20)
                    except Exception:
                        trig_res = requests.post(resume_url, timeout=20)
                    logger.info(f"[{issue_key}] Ответ n8n на resume: {trig_res.status_code}")
                    if trig_res.ok:
                        return True

        except Exception as e:
            logger.error(f"[{issue_key}] Ошибка при поиске/возобновлении execution n8n (попытка {attempt}): {e}")

        time.sleep(delay)

    logger.warning(f"[{issue_key}] ⚠️ Не удалось найти или возобновить waiting execution n8n после {max_retries} попыток.")
    return False

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
        git("add", "tests/api/", "tests/ui/", "tests/backend/", "tests/frontend/", check=False)
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
        
    while True:
        try:
            issues = get_in_progress_issues()
            if issues is None:
                time.sleep(10)
                continue

            active_keys = {issue["key"] for issue in issues}
            for k in list(trackers.keys()):
                if k not in active_keys and trackers[k].state not in (STATE_GATE2_APPROVED, STATE_CI_RUNNING, STATE_PAUSED):
                    logger.info(f"[{k}] 🧹 Задача больше не в очереди -> удаление трекера из памяти")
                    del trackers[k]

            for issue in issues:
                issue_key = issue["key"]
                tracker = trackers.setdefault(issue_key, PipelineTracker(issue_key))
                try:
                    tracker.step(issue)
                except Exception as te:
                    logger.warning(f"Ошибка при обработке для {issue_key}: {te}", exc_info=True)

        except Exception as e:
            logger.error(f"Глобальная ошибка в цикле поллинга Jira: {e}", exc_info=True)

        time.sleep(10)

if __name__ == "__main__":
    daemon_loop()
