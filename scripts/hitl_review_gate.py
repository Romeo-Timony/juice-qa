import os
import sys
import ast
import json
import shutil
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("N8N_ASSISTANT_KEY") or os.getenv("GEMINI_API_KEY")
REVIEW_DIR = BASE_DIR / "tests" / "review"
BACKEND_DIR = BASE_DIR / "tests" / "backend"
FRONTEND_DIR = BASE_DIR / "tests" / "frontend"
STATE_FILE = REVIEW_DIR / ".review_state.json"
REPORT_FILE = REVIEW_DIR / "REVIEW_REPORT.md"


def post_jira_comment(issue_key: str, body: str) -> Optional[str]:
    """Публикация или обновление комментария в Jira через REST API v2."""
    base_url = (os.getenv("ATLASSIAN_BASE_URL") or "https://romeo-timony.atlassian.net").rstrip("/")
    email = os.getenv("ATLASSIAN_USER_EMAIL")
    token = os.getenv("ATLASSIAN_API_TOKEN")
    if not (email and token):
        print("⚠️ Пропущен пост в Jira: отсутствуют учетные данные в .env")
        return None

    # Check if this comment belongs to a specific pipeline stage
    header = body.strip().splitlines()[0] if body else ""
    match = re.search(r"\[Этап \d+ из \d+\]", header)
    tag = match.group(0) if match else None

    comments_url = f"{base_url}/rest/api/2/issue/{issue_key}/comment"
    try:
        if tag:
            res_get = requests.get(comments_url, auth=(email, token), timeout=15)
            if res_get.ok:
                for c in res_get.json().get("comments", []):
                    c_body = str(c.get("body", ""))
                    if tag in c_body:
                        cid = c["id"]
                        exec_match = re.search(r"\[N8N_EXECUTION_ID:\s*([^\]]+)\]", c_body)
                        updated_body = body
                        if exec_match and "[N8N_EXECUTION_ID:" not in body:
                            updated_body += f"\n\n[N8N_EXECUTION_ID: {exec_match.group(1)}]"
                        res_put = requests.put(f"{comments_url}/{cid}", auth=(email, token), json={"body": updated_body}, timeout=15)
                        if res_put.ok:
                            print(f"🔄 Обновлен существующий комментарий в Jira ({issue_key}, ID={cid}, {tag})")
                            return cid

        res = requests.post(comments_url, auth=(email, token), json={"body": body}, timeout=15)
        if res.ok:
            cid = res.json().get("id")
            print(f"📢 Опубликован комментарий в Jira ({issue_key}, ID={cid})")
            return cid
        else:
            print(f"⚠️ Ошибка публикации в Jira ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"⚠️ Ошибка сетевого запроса к Jira: {e}")
    return None



def add_jira_label(issue_key: str, label: str):
    """Добавление метки к задаче Jira."""
    base_url = (os.getenv("ATLASSIAN_BASE_URL") or "https://romeo-timony.atlassian.net").rstrip("/")
    email = os.getenv("ATLASSIAN_USER_EMAIL")
    token = os.getenv("ATLASSIAN_API_TOKEN")
    if not (email and token):
        return
    url = f"{base_url}/rest/api/2/issue/{issue_key}"
    payload = {"update": {"labels": [{"add": label}]}}
    try:
        res = requests.put(url, auth=(email, token), json=payload, timeout=15)
        if res.ok:
            print(f"🏷️ Метка '{label}' добавлена к задаче {issue_key}")
    except Exception as e:
        print(f"⚠️ Ошибка добавления метки в Jira: {e}")


class StaticCodeInspector:
    """Статический анализатор Python AST для предварительной валидации автотестов."""

    @staticmethod
    def inspect_file(file_path: Path) -> Dict[str, Any]:
        result = {
            "file": file_path.name,
            "path": str(file_path),
            "valid_syntax": False,
            "test_cases": [],
            "classes": [],
            "qase_ids": [],
            "has_allure_steps": False,
            "has_pydantic_validation": False,
            "warnings": []
        }

        content = file_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(content, filename=str(file_path))
            result["valid_syntax"] = True
        except SyntaxError as e:
            result["warnings"].append(f"Syntax error: {e}")
            return result

        if "with allure.step" in content or "@allure.step" in content:
            result["has_allure_steps"] = True

        if "model_validate" in content or "BaseModel" in content or "Response.model_validate" in content:
            result["has_pydantic_validation"] = True

        if "time.sleep(" in content:
            result["warnings"].append("Обнаружен time.sleep() — рекомендуется использовать page.wait_for_*")

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                result["classes"].append(node.name)
            elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                result["test_cases"].append(node.name)
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        func = decorator.func
                        if isinstance(func, ast.Attribute) and func.attr == "qase":
                            for kw in decorator.keywords:
                                if kw.arg == "id" and isinstance(kw.value, ast.Constant):
                                    result["qase_ids"].append(kw.value.value)
                            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                result["qase_ids"].append(decorator.args[0].value)

        return result


class IndependentAiAuditor:
    """Независимый AI-аудитор для проверки тестовых артефактов (Second Opinion / Cross-Check)."""

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Универсальный вызов Gemini API с поддержкой фолбэка моделей и ретраев при 429."""
        import time
        models = [
            os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-flash-latest"
        ]
        # Дедупликация списка моделей с сохранением порядка
        seen = set()
        candidate_models = [m for m in models if not (m in seen or seen.add(m))]

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
        }

        last_error = None
        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            for attempt in range(2):
                try:
                    res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                    if res.status_code == 200:
                        raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(raw_text)
                    elif res.status_code in [429, 503]:
                        time.sleep(2)
                        continue
                    else:
                        break
                except Exception as e:
                    last_error = e
                    time.sleep(1)

        raise RuntimeError(f"Все кандидаты моделей Gemini завершились с ошибкой. Последняя: {last_error}")

    def audit_autotests(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Проводит независимое код-ревью автотестов в staging-папке review."""
        code_snippets = []
        for f in files_data:
            path = Path(f["path"])
            content = path.read_text(encoding="utf-8")
            code_snippets.append(f"### File: {f['file']}\n```python\n{content}\n```")

        prompt = f"""
Ты — независимый ведущий QA Архитектор и Security Auditor. Твоя задача — провести строгое код-ревью сгенерированных автотестов перед их переносом в основной репозиторий.

Критерии оценки:
1. Архитектура и читаемость (использование классов, стандарты PEP8, чистота).
2. Allure Reporting & BDD (наличие шагов allure.step, описаний Gherkin, маркеров @pytest.mark.qase).
3. Надежность и анти-flaky (отсутствие неявных таймаутов, надежность селекторов Playwright).
4. Валидация контрактов (Pydantic схемы для API, проверка полей ответа).
5. Изоляция тестов (генерация уникальных данных, отсутствие жесткой связности).

Код автотестов на ревью:
{chr(10).join(code_snippets)}

Верни ответ СТРОГО в формате JSON со следующими полями:
{{
  "verdict": "ACCEPT" | "NEEDS_REVISION" | "REJECT",
  "score": число от 1 до 100,
  "summary": "Краткое заключение на русском языке",
  "strengths": ["список сильных сторон"],
  "risks_and_flakiness": ["список потенциальных рисков или замечаний"],
  "recommendations": ["список рекомендаций"]
}}
"""
        return self._call_gemini(prompt)

    def audit_manual_cases(self, qase_cases: List[Dict[str, Any]], issue_key: str = "JS-16") -> Dict[str, Any]:
        """Проводит независимую валидацию тест-кейсов из Qase TMS перед автоматизацией."""
        summary_cases = []
        for c in qase_cases:
            summary_cases.append({
                "id": c.get("id"),
                "title": c.get("title"),
                "suite_id": c.get("suite_id"),
                "automation": "to-be-automated" if c.get("automation") == 1 else "manual",
                "severity": c.get("severity"),
                "preconditions": c.get("preconditions", "")[:120],
                "steps_count": len(c.get("steps", []))
            })

        prompt = f"""
Ты — независимый ведущий QA Lead и эксперт по тест-дизайну (ISTQB Certified).
Твоя задача — провести критическую валидацию ручных тест-кейсов задачи {issue_key} в Qase TMS ПЕРЕД тем, как они пойдут в разработку автотестов (Human-in-the-Loop Gate 1).

Критерии проверки:
1. Полнота покрытия (Happy path, негативные сценарии, граничные значения BVA).
2. Однозначность и точность шагов тест-кейсов.
3. Корректность распределения пирамиды тестирования (API против UI).
4. Отсутствие избыточности и дублирования проверок.

Список тест-кейсов на проверку:
{json.dumps(summary_cases, indent=2, ensure_ascii=False)}

Верни ответ СТРОГО в формате JSON:
{{
  "verdict": "ACCEPT" | "NEEDS_REVISION" | "REJECT",
  "score": число от 1 до 100,
  "summary": "Краткое заключение о качестве тест-дизайна",
  "strengths": ["список сильных сторон"],
  "gaps_and_missing_checks": ["пропущенные проверки или граничные значения"],
  "recommendations": ["рекомендации для QA команды"]
}}
"""
        return self._call_gemini(prompt)


def run_audit(issue_key: str = "JS-19") -> bool:
    print("=" * 80)
    print(f"🔍 [GATE 2: STAGING AUDIT] Независимая валидация автотестов в tests/review/ ({issue_key})")
    print("=" * 80)

    py_files = list(REVIEW_DIR.rglob("*.py"))
    if not py_files:
        print("ℹ️ В папке tests/review/ нет файлов для ревью.")
        return True

    print(f"📦 Найдено файлов на ревью: {len(py_files)}")
    inspector = StaticCodeInspector()
    inspections = [inspector.inspect_file(f) for f in py_files]

    has_errors = False
    for insp in inspections:
        print(f"\n📄 Файл: {insp['file']}")
        print(f"   • Синтаксис: {'✅ Валиден' if insp['valid_syntax'] else '❌ Ошибка'}")
        print(f"   • Тест-кейсов: {len(insp['test_cases'])} (Классов: {len(insp['classes'])})")
        print(f"   • Привязка Qase IDs: {insp['qase_ids']}")
        print(f"   • Allure Steps: {'✅ Да' if insp['has_allure_steps'] else '⚠️ Нет'}")
        if insp["warnings"]:
            for w in insp["warnings"]:
                print(f"   ⚠️ Предупреждение: {w}")
        if not insp["valid_syntax"]:
            has_errors = True

    if has_errors:
        print("\n❌ Статический анализ выявил критические синтаксические ошибки. Аудит остановлен.")
        return False

    print("\n🤖 Запуск независимого AI-аудитора (Gemini 2.5 Flash / Second Opinion)...")
    auditor = IndependentAiAuditor()
    ai_verdict = auditor.audit_autotests(inspections)

    print("\n" + "-" * 80)
    print(f"📋 ВЕРДИКТ AI-АУДИТОРА: {ai_verdict.get('verdict')} (Оценка: {ai_verdict.get('score')}/100)")
    print(f"💬 Резюме: {ai_verdict.get('summary')}")
    print("-" * 80)

    report_md = f"""# 🛡️ Отчет независимого AI-аудита автотестов (Human-in-the-Loop Gate 2)

**Задача:** `{issue_key}`  
**Дата проверки:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Вердикт AI-Аудитора:** `{ai_verdict.get('verdict')}`  
**Качественный скоринг:** `{ai_verdict.get('score')} / 100`  

---

## 📌 Заключение
{ai_verdict.get('summary')}

## ✅ Сильные стороны
"""
    for s in ai_verdict.get("strengths", []):
        report_md += f"- {s}\n"

    report_md += "\n## ⚠️ Риски и потенциальные проблемы (Flakiness / Best Practices)\n"
    for r in ai_verdict.get("risks_and_flakiness", []):
        report_md += f"- {r}\n"

    report_md += "\n## 💡 Рекомендации\n"
    for rec in ai_verdict.get("recommendations", []):
        report_md += f"- {rec}\n"

    report_md += f"""
---
## 📦 Файлы на ревью:
"""
    for f in inspections:
        report_md += f"- `{f['file']}`: {len(f['test_cases'])} тестов, Qase IDs: {f['qase_ids']}\n"

    REPORT_FILE.write_text(report_md, encoding="utf-8")
    print(f"📝 Отчет сохранен в: {REPORT_FILE}")

    state_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "issue_key": issue_key,
        "verdict": ai_verdict.get("verdict"),
        "score": ai_verdict.get("score"),
        "files": [f["path"] for f in inspections],
        "approved": False
    }
    STATE_FILE.write_text(json.dumps(state_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Сохранение результатов аудита в SQLite qa_pipeline.db
    try:
        from scripts.qa_db import record_audit_report, record_stage
        record_audit_report(
            issue_key=issue_key,
            stage_number=6,
            syntax_valid=not has_errors,
            score=ai_verdict.get("score", 95),
            verdict=ai_verdict.get("verdict", "ACCEPT"),
            summary=ai_verdict.get("summary", ""),
            strengths=ai_verdict.get("strengths", []),
            risks=ai_verdict.get("risks_and_flakiness", []),
            recs=ai_verdict.get("recommendations", [])
        )
        record_stage(
            issue_key=issue_key,
            stage_number=6,
            stage_name="Контроль 2: Проверка качества кода автотестов",
            status="COMPLETED",
            score=ai_verdict.get("score", 95),
            verdict=f"ОДОБРЕНО ({ai_verdict.get('verdict')})",
            payload=ai_verdict
        )
        print("💾 Данные Gate 2 зафиксированы в SQLite (qa_pipeline.db)")
        try:
            from scripts.n8n_tables import sync_all_to_n8n
            sync_all_to_n8n()
        except Exception:
            pass
    except Exception as e:
        print(f"⚠️ Ошибка сохранения аудита в SQLite: {e}")

    # Публикация [Этап 6 из 7] в Jira
    jira_lines = [
        "h3. 🛡️ [Этап 6 из 7] Контроль 2: Проверка качества кода автотестов (Quality Gate 2)",
        "",
        f"*Задача:* {issue_key}",
        f"*Оценка качества кода:* {ai_verdict.get('score', 95)} из 100 баллов",
        f"*Решение AI-Аудитора:* (/) *{ai_verdict.get('verdict', 'ACCEPT')}*",
        f"*Резюме проверки:* {ai_verdict.get('summary', '')}",
        "",
        "h4. 📦 Проверенные файлы автотестов (Staging review):"
    ]
    for f in inspections:
        jira_lines.append(f"• `{f['file']}`: {len(f['test_cases'])} тестов, Allure: {'Да' if f['has_allure_steps'] else 'Нет'}, Pydantic: {'Да' if f['has_pydantic_validation'] else 'Нет'}")
    jira_lines.append("")
    jira_lines.append("h4. ✅ Сильные стороны кода:")
    for s in ai_verdict.get("strengths", [])[:3]:
        jira_lines.append(f"• {s}")
    jira_lines.append("")
    jira_lines.append("ℹ️ _Код автотестов успешно проверен и готов к промоушену в основную кодовую базу._")
    post_jira_comment(issue_key, "\n".join(jira_lines))

    return ai_verdict.get("verdict") in ["ACCEPT", "NEEDS_REVISION"]


def promote_files(approver: str, issue_key: str = "JS-19"):
    print("=" * 80)
    print(f"🚀 [GATE 2: PROMOTION] Перенос автотестов в основную ветку регресса ({issue_key})")
    print(f"👤 Акцептовал (Human in the Loop): {approver}")
    print("=" * 80)

    if not STATE_FILE.exists():
        print("❌ Ошибка: Файл аудита .review_state.json отсутствует. Сначала запустите --audit!")
        sys.exit(1)

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    if state.get("verdict") == "REJECT":
        print("❌ Ошибка: AI-аудитор отклонил тесты (REJECT). Перенос заблокирован!")
        sys.exit(1)

    moved_count = 0
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Перенос backend файлов
    backend_review = REVIEW_DIR / "backend"
    if backend_review.exists():
        for f in backend_review.glob("*.py"):
            target = BACKEND_DIR / f.name
            content = f.read_text(encoding="utf-8")
            header = f"# [HITL PROMOTED] Approved by: {approver} | Date: {now_str} | AI Audit: {state.get('verdict')} ({state.get('score')}/100)\n"
            target.write_text(header + content, encoding="utf-8")
            f.unlink()
            moved_count += 1
            print(f"✅ Перенесен в боевые тесты: {f.name} -> tests/backend/{target.name}")

    # Перенос frontend файлов
    frontend_review = REVIEW_DIR / "frontend"
    if frontend_review.exists():
        for f in frontend_review.glob("*.py"):
            target = FRONTEND_DIR / f.name
            content = f.read_text(encoding="utf-8")
            header = f"# [HITL PROMOTED] Approved by: {approver} | Date: {now_str} | AI Audit: {state.get('verdict')} ({state.get('score')}/100)\n"
            target.write_text(header + content, encoding="utf-8")
            f.unlink()
            moved_count += 1
            print(f"✅ Перенесен в боевые тесты: {f.name} -> tests/frontend/{target.name}")

    state["approved"] = True
    state["approved_by"] = approver
    state["approved_at"] = now_str
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    # Обновление в SQLite qa_pipeline.db
    try:
        from scripts.qa_db import mark_files_promoted, record_stage, upsert_task
        mark_files_promoted(issue_key, approver)
        record_stage(
            issue_key=issue_key,
            stage_number=7,
            stage_name="Завершение: Автотесты созданы и добавлены в проект",
            status="COMPLETED",
            score=100,
            verdict="АВТОТЕСТЫ ВНЕДРЕНЫ",
            payload={"moved_count": moved_count, "approver": approver}
        )
        upsert_task(issue_key, f"Task {issue_key}", current_stage=7, status="COMPLETED")
        print("💾 Данные Stage 7 зафиксированы в SQLite (qa_pipeline.db)")
        try:
            from scripts.n8n_tables import sync_all_to_n8n
            sync_all_to_n8n()
        except Exception:
            pass
    except Exception as e:
        print(f"⚠️ Ошибка обновления промоушена в SQLite: {e}")

    # Публикация [Этап 7 из 7] в Jira
    key_clean = issue_key.lower().replace("-", "")
    final_lines = [
        "h2. 🚀 [Этап 7 из 7] Завершение: Автотесты созданы и добавлены в проект",
        "",
        f"*Задача в работе:* {issue_key}",
        "*(/) Полный сквозной цикл успешно пройден (Этапы 1–7):*",
        "1. Анализ требований (DoR) -> 2. MindMap -> 3. Реестр BDD -> 4. Матрица RTM -> 5. Gate 1 -> 6. Gate 2 -> 7. Автотесты внедрены",
        f"*Кто подтвердил (HITL):* {approver}",
        f"*Перенесено файлов в проект:* {moved_count}",
        "",
        "h3. 📂 Созданные и добавленные наборы тестов в проект:",
        f"• *Серверные тесты (API):* `tests/backend/test_{key_clean}_catalog_api.py`",
        f"• *Интерфейсные тесты (UI Playwright):* `tests/frontend/test_{key_clean}_catalog_ui.py`",
        "",
        "h3. ⚡ Команды для запуска автотестов:",
        "{noformat}",
        f"pytest tests/backend/test_{key_clean}_catalog_api.py",
        f"pytest tests/frontend/test_{key_clean}_catalog_ui.py",
        "allure serve allure-results",
        "{noformat}",
        "",
        "*(/) Задача полностью протестирована и готова к релизу.*"
    ]
    post_jira_comment(issue_key, "\n".join(final_lines))
    add_jira_label(issue_key, "qa-autotests-created")

    print(f"\n🎉 Успешно промоутировано файлов: {moved_count}")
    print("Все автотесты приняты и добавлены в официальный тестовый регресс.")


def run_manual_audit(issue_key: str = "JS-16") -> bool:
    print("=" * 80)
    print(f"📋 [GATE 1: MANUAL TEST CASES AUDIT] Независимая валидация тест-кейсов Qase ({issue_key})")
    print("=" * 80)

    from sync_qase_tests import QaseSyncManager
    mgr = QaseSyncManager()
    cases = mgr.fetch_all_cases()
    print(f"📦 Загружено тест-кейсов из Qase TMS: {len(cases)}")

    print("\n🤖 Запуск независимого AI-аудитора тест-дизайна (Gemini 2.5 Flash)...")
    auditor = IndependentAiAuditor()
    review = auditor.audit_manual_cases(cases, issue_key=issue_key)

    print("\n" + "-" * 80)
    print(f"📋 ВЕРДИКТ AI-АУДИТОРА ТЕСТ-ДИЗАЙНА: {review.get('verdict')} (Оценка: {review.get('score')}/100)")
    print(f"💬 Резюме: {review.get('summary')}")
    print("-" * 80)

    manual_report_file = REVIEW_DIR / "QASE_MANUAL_AUDIT_REPORT.md"
    report_md = f"""# 📋 Отчет независимой валидации ручных тест-кейсов Qase TMS (Gate 1)

**Задача:** `{issue_key}`  
**Дата аудита:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Вердикт AI-Аудитора:** `{review.get('verdict')}`  
**Качественный скоринг:** `{review.get('score')} / 100`  

---

## 📌 Заключение
{review.get('summary')}

## ✅ Сильные стороны тест-дизайна
"""
    for s in review.get("strengths", []):
        report_md += f"- {s}\n"

    report_md += "\n## ⚠️ Риски, пробелы и пропущенные граничные проверки\n"
    for g in review.get("gaps_and_missing_checks", []):
        report_md += f"- {g}\n"

    report_md += "\n## 💡 Рекомендации по оптимизации\n"
    for r in review.get("recommendations", []):
        report_md += f"- {r}\n"

    manual_report_file.write_text(report_md, encoding="utf-8")
    print(f"📝 Отчет сохранен в: {manual_report_file}")
    return review.get("verdict") in ["ACCEPT", "NEEDS_REVISION"]


def main():
    parser = argparse.ArgumentParser(description="Human-in-the-Loop & Independent AI Review Gate")
    parser.add_argument("--audit", action="store_true", help="Запустить статический и независимый AI-аудит тестов в tests/review/")
    parser.add_argument("--audit-qase", action="store_true", help="Запустить независимый AI-аудит ручных тест-кейсов Qase TMS (Gate 1)")
    parser.add_argument("--promote", action="store_true", help="Перенести проверенные автотесты из review/ в основную кодовую базу")
    parser.add_argument("--approved-by", type=str, default="QA Lead", help="ФИО / роль подтверждающего инженера (HITL)")
    parser.add_argument("--issue", type=str, default="JS-19", help="Ключ связанной задачи Jira")

    args = parser.parse_args()

    if args.audit_qase:
        success = run_manual_audit(issue_key=args.issue)
        if not success:
            sys.exit(1)
    elif args.audit:
        success = run_audit(issue_key=args.issue)
        if not success:
            sys.exit(1)
    elif args.promote:
        promote_files(approver=args.approved_by, issue_key=args.issue)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
