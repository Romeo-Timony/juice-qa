import os
import sys
import ast
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / ".env")

QASE_API_TOKEN = os.getenv("QASE_API_TOKEN")
QASE_PROJECT_CODE = os.getenv("QASE_PROJECT_CODE", "JS")
QASE_BASE_URL = os.getenv("QASE_API_URL", "https://api.qase.io/v1")
GEMINI_API_KEY = os.getenv("N8N_ASSISTANT_KEY")

TESTS_DIR = BASE_DIR / "tests"
REVIEW_DIR = TESTS_DIR / "review"
BACKEND_DIR = TESTS_DIR / "backend"
FRONTEND_DIR = TESTS_DIR / "frontend"


class QaseApiClient:
    def __init__(self):
        if not QASE_API_TOKEN:
            raise ValueError("QASE_API_TOKEN is missing in .env")
        self.headers = {
            "Token": QASE_API_TOKEN,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def get_case(self, case_id: int) -> Optional[Dict[str, Any]]:
        url = f"{QASE_BASE_URL}/case/{QASE_PROJECT_CODE}/{case_id}"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 404:
            return None
        res.raise_for_status()
        return res.json().get("result")

    def get_all_cases(self) -> List[Dict[str, Any]]:
        url = f"{QASE_BASE_URL}/case/{QASE_PROJECT_CODE}?limit=100"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        return res.json().get("result", {}).get("entities", [])


class LocalTestScanner:
    """Поиск автотестов по номеру Qase ID в кодовой базе."""

    @staticmethod
    def find_test_by_qase_id(qase_id: int) -> Optional[Dict[str, Any]]:
        for folder_name in ["backend", "frontend"]:
            folder = TESTS_DIR / folder_name
            for file_path in folder.glob("*.py"):
                if file_path.name.startswith("__"):
                    continue
                content = file_path.read_text(encoding="utf-8")
                try:
                    tree = ast.parse(content, filename=str(file_path))
                except Exception:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Call):
                                func = decorator.func
                                if isinstance(func, ast.Attribute) and func.attr == "qase":
                                    matched_id = None
                                    for kw in decorator.keywords:
                                        if kw.arg == "id" and isinstance(kw.value, ast.Constant):
                                            matched_id = kw.value.value
                                    if matched_id is None and decorator.args and isinstance(decorator.args[0], ast.Constant):
                                        matched_id = decorator.args[0].value

                                    if matched_id == qase_id:
                                        # Извлекаем фрагмент исходного кода функции
                                        lines = content.splitlines()
                                        first_lineno = node.decorator_list[0].lineno if node.decorator_list else node.lineno
                                        start_line = first_lineno - 1
                                        end_line = getattr(node, "end_lineno", start_line + 30)
                                        code_snippet = "\n".join(lines[start_line:end_line])
                                        return {
                                            "qase_id": qase_id,
                                            "layer": folder_name,
                                            "file": str(file_path),
                                            "function_name": node.name,
                                            "start_line": start_line + 1,
                                            "end_line": end_line,
                                            "code": code_snippet
                                        }
        return None


class TestSynchronizer:
    """Адаптация автотестов под изменения в Qase TMS через независимый AI-движок."""

    @staticmethod
    def adapt_autotest(case_data: Dict[str, Any], local_test: Dict[str, Any]) -> str:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY / N8N_ASSISTANT_KEY is missing")

        prompt = f"""
Ты — ведущий QA Automation Архитектор.
Ручной тест-кейс в Qase TMS был изменен или дополнен!
Тебе необходимо актуализировать исходный код автотеста, строго сохранив:
1. Использование Allure Steps (with allure.step(...)).
2. Использование Pydantic моделей для API (если это backend).
3. Использование Page Object методов Playwright (если это frontend).
4. Маркер @pytest.mark.qase(id={case_data['id']}).
5. Чистоту кода и BDD стиль в docstring.

Обновленный тест-кейс из Qase TMS:
ID: {case_data.get('id')}
Название: {case_data.get('title')}
Предусловия: {case_data.get('preconditions')}
Шаги: {json.dumps(case_data.get('steps', []), indent=2, ensure_ascii=False)}

Текущий исходный код автотеста:
```python
{local_test['code']}
```

Верни ТОЛЬКО обновленный Python код функции автотеста (с декораторами и докстрингом) без лишнего markdown и без пояснений.
"""
        models = [os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"), "gemini-3.5-flash-lite", "gemini-flash-latest"]
        for m in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={GEMINI_API_KEY}"
            try:
                res = requests.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                if res.status_code == 200:
                    text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text.startswith("```python"):
                        text = text[len("```python"):].strip()
                    if text.endswith("```"):
                        text = text[:-3].strip()
                    return text
            except Exception:
                continue

        raise RuntimeError("Не удалось адаптировать автотест через AI модель.")


def normalize_test_snippet(code_str: str, target_base_indent: int = 4) -> str:
    """Гарантирует идеальное выравнивание Python-сниппета для методов тестового класса."""
    lines = code_str.strip().splitlines()
    def_line_idx = next((i for i, l in enumerate(lines) if "def test_" in l), -1)
    if def_line_idx == -1:
        return code_str
    def_indent = len(lines[def_line_idx]) - len(lines[def_line_idx].lstrip())
    normalized = []
    for line in lines:
        if not line.strip():
            normalized.append("")
            continue
        cur_indent = len(line) - len(line.lstrip())
        rel_indent = cur_indent - def_indent
        target_indent = target_base_indent + max(0, rel_indent)
        normalized.append(" " * target_indent + line.lstrip())
    return "\n".join(normalized)


def sync_single_case(case_id: int):
    print("=" * 80)
    print(f"🔄 СИНХРОНИЗАЦИЯ ТЕСТ-КЕЙСА QASE #{case_id} С АВТОТЕСТОМ")
    print("=" * 80)

    qase = QaseApiClient()
    case_data = qase.get_case(case_id)
    scanner = LocalTestScanner()
    local_test = scanner.find_test_by_qase_id(case_id)

    if not local_test:
        print(f"⚠️ Автотест с Qase ID #{case_id} не найден в кодовой базе.")
        return

    print(f"📍 Найден локальный автотест:")
    print(f"   • Файл: {local_test['file']}")
    print(f"   • Функция: {local_test['function_name']}")
    print(f"   • Слой: {local_test['layer']}")

    # Случай 1: Кейс удален в Qase TMS
    if case_data is None:
        print(f"\n🗑️ Тест-кейс #{case_id} был УДАЛЕН из Qase TMS!")
        print("Подготовка предложения на деактивацию в staging tests/review/...")
        # Помещаем в review помеченную версию с @pytest.mark.skip
        review_dest = REVIEW_DIR / local_test["layer"]
        review_dest.mkdir(parents=True, exist_ok=True)
        file_path = Path(local_test["file"])
        orig_content = file_path.read_text(encoding="utf-8")
        # Добавляем метку skip к функции
        modified = orig_content.replace(
            f"def {local_test['function_name']}",
            f"@pytest.mark.skip(reason='Deprecated: Qase case #{case_id} was deleted')\n    def {local_test['function_name']}"
        )
        staging_file = review_dest / file_path.name
        staging_file.write_text(modified, encoding="utf-8")
        print(f"✅ Подготовлен файл с деактивацией: {staging_file}")
        print("Запустите scripts/hitl_review_gate.py --audit для утверждения командой.")
        return

    # Случай 2: Кейс изменен/актуален в Qase TMS
    print(f"\n📝 Загружен актуальный кейс из Qase: «{case_data.get('title')}»")
    print("🤖 Запуск AI-адаптера для обновления кода автотеста...")
    new_code = TestSynchronizer.adapt_autotest(case_data, local_test)

    # Запись в буферную папку review
    review_dest = REVIEW_DIR / local_test["layer"]
    review_dest.mkdir(parents=True, exist_ok=True)
    file_path = Path(local_test["file"])
    orig_content = file_path.read_text(encoding="utf-8")
    
    lines = orig_content.splitlines()
    indented_code = normalize_test_snippet(new_code, target_base_indent=4)

    start_idx = local_test["start_line"] - 1
    end_idx = local_test["end_line"]
    lines[start_idx:end_idx] = indented_code.splitlines()
    updated_content = "\n".join(lines) + "\n"

    staging_file = review_dest / file_path.name
    staging_file.write_text(updated_content, encoding="utf-8")

    # Создаем diff отчет
    diff_report = REVIEW_DIR / "SYNC_DIFF_REPORT.md"
    diff_md = f"""# 🔄 Отчет синхронизации изменений Qase TMS -> Автотест

**Дата синхронизации:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Тест-кейс Qase:** `#{case_id}: {case_data.get('title')}`  
**Целевой автотест:** `{local_test['function_name']}` в `{file_path.name}`  

---

## 📌 Что изменилось в ручном тест-кейсе:
- **Название:** {case_data.get('title')}
- **Предусловия:** {case_data.get('preconditions')}
- **Количество шагов:** {len(case_data.get('steps', []))}

## 🛡️ Статус в Staging:
Файл с обновленным тестом сохранен в буферной папке: `{staging_file}`.
Для применения изменений в регресс пройдите аудит:
```bash
python scripts/hitl_review_gate.py --audit
python scripts/hitl_review_gate.py --promote --approved-by "QA Lead"
```
"""
    diff_report.write_text(diff_md, encoding="utf-8")

    print(f"\n✅ Адаптированный автотест успешно сохранен в карантин: {staging_file}")
    print(f"📝 Отчет сформирован: {diff_report}")
    print("\n🚀 Запуск автоматического Gate 2 аудита...")
    from hitl_review_gate import run_audit
    run_audit()


def run_full_drift_detection():
    """Проверка расхождений (Drift) между всеми кейсами Qase и локальными автотестами."""
    print("=" * 80)
    print("🛰️ ДЕТЕКТИРОВАНИЕ РАСХОЖДЕНИЙ (DRIFT) QASE TMS <-> CODEBASE")
    print("=" * 80)

    qase = QaseApiClient()
    all_cases = qase.get_all_cases()
    qase_dict = {c["id"]: c for c in all_cases}

    from sync_qase_tests import QaseSyncManager
    mgr = QaseSyncManager()
    local_markers = mgr.scan_local_test_markers()
    all_local_ids = set(local_markers["backend"].keys()) | set(local_markers["frontend"].keys())

    print(f"📦 Всего кейсов в Qase TMS: {len(all_cases)}")
    print(f"💻 Автотестов в коде: {len(all_local_ids)}")

    orphans = [cid for cid in all_local_ids if cid not in qase_dict]
    if orphans:
        print(f"\n⚠️ ОБНАРУЖЕНЫ УДАЛЕННЫЕ В QASE КЕЙСЫ (Orphans в коде): {orphans}")
        for cid in orphans:
            print(f"   • ID #{cid} присутствует в коде, но отсутствует в Qase TMS")
    else:
        print("\n✅ Удаленных (сиротских) автотестов не обнаружено.")

    unautomated = [c for c in all_cases if c.get("automation") == 1 and c["id"] not in all_local_ids]
    if unautomated:
        print(f"\n⚠️ КЕЙСЫ К АВТОМАТИЗАЦИИ БЕЗ КОДА (Unimplemented): {len(unautomated)}")
        for c in unautomated:
            print(f"   • [JS-{c['id']}] {c['title']}")
    else:
        print("✅ Все кейсы с признаком 'to-be-automated' полностью автоматизированы (100%).")


def main():
    parser = argparse.ArgumentParser(description="Qase TMS Bidirectional Lifecycle Sync")
    parser.add_argument("--sync-case", type=int, help="Синхронизировать автотест по конкретному ID тест-кейса Qase")
    parser.add_argument("--drift", action="store_true", help="Проверить расхождения между Qase TMS и кодовой базой")

    args = parser.parse_args()

    if args.sync_case:
        sync_single_case(args.sync_case)
    elif args.drift:
        run_full_drift_detection()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
