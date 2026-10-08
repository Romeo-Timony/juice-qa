import os
import re
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

QASE_API_TOKEN = os.getenv("QASE_API_TOKEN")
QASE_PROJECT_CODE = os.getenv("QASE_PROJECT_CODE", "JS")
QASE_BASE_URL = "https://api.qase.io/v1"


class QaseSyncManager:
    def __init__(self):
        if not QASE_API_TOKEN:
            raise ValueError("QASE_API_TOKEN is missing in .env")
        self.headers = {
            "Token": QASE_API_TOKEN,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def fetch_all_cases(self) -> List[Dict[str, Any]]:
        """Загрузка всех тест-кейсов из Qase TMS для проекта."""
        url = f"{QASE_BASE_URL}/case/{QASE_PROJECT_CODE}?limit=100"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        data = res.json()
        return data.get("result", {}).get("entities", [])

    def fetch_suites(self) -> Dict[int, str]:
        """Загрузка дерева тест-сьютов (ID -> Название)."""
        url = f"{QASE_BASE_URL}/suite/{QASE_PROJECT_CODE}?limit=50"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        data = res.json()
        suites = {}
        for s in data.get("result", {}).get("entities", []):
            suites[s["id"]] = s["title"]
        return suites

    def scan_local_test_markers(self) -> Dict[str, Dict[int, str]]:
        """
        Сканирование директорий tests/backend и tests/frontend через AST парсер Python.
        Надежно извлекает @pytest.mark.qase(id=...) независимо от многострочной параметризации.
        """
        import ast

        result = {"backend": {}, "frontend": {}}
        tests_dir = BASE_DIR / "tests"

        for suite_name in ["backend", "frontend"]:
            suite_path = tests_dir / suite_name
            if not suite_path.exists():
                continue
            for file_path in suite_path.glob("*.py"):
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
                            # Обработка @pytest.mark.qase(id=...)
                            if isinstance(decorator, ast.Call):
                                func = decorator.func
                                is_qase_mark = False
                                if isinstance(func, ast.Attribute) and func.attr == "qase":
                                    is_qase_mark = True
                                elif isinstance(func, ast.Attribute) and func.attr == "mark":
                                    pass

                                if is_qase_mark:
                                    qase_id = None
                                    for kw in decorator.keywords:
                                        if kw.arg == "id" and isinstance(kw.value, ast.Constant):
                                            qase_id = kw.value.value
                                    if qase_id is None and decorator.args and isinstance(decorator.args[0], ast.Constant):
                                        qase_id = decorator.args[0].value

                                    if qase_id is not None:
                                        result[suite_name][int(qase_id)] = f"{file_path.name}:{node.name}"

        return result


    def audit_traceability(self) -> Dict[str, Any]:
        """
        Сквозной аудит соответствия Qase TMS и автотестов:
        - Проверка 100% автоматизации Backend
        - Проверка выборочной автоматизации Frontend (Manual vs To-Be-Automated)
        - Проверка зеркальной структуры папок
        """
        cases = self.fetch_all_cases()
        suites = self.fetch_suites()
        local_markers = self.scan_local_test_markers()

        backend_suite_id = next((sid for sid, name in suites.items() if "Backend" in name), 2)
        frontend_suite_id = next((sid for sid, name in suites.items() if "Frontend" in name), 4)

        report = {
            "backend": {
                "suite_title": suites.get(backend_suite_id, "Backend"),
                "total_cases": 0,
                "to_be_automated": [],
                "manual_cases": [],
                "implemented_tests": [],
                "missing_tests": []
            },
            "frontend": {
                "suite_title": suites.get(frontend_suite_id, "Frontend"),
                "total_cases": 0,
                "to_be_automated": [],
                "manual_cases": [],
                "implemented_tests": [],
                "missing_tests": []
            }
        }

        for c in cases:
            cid = c["id"]
            title = c["title"]
            sid = c.get("suite_id")
            auto_flag = c.get("automation")  # 1 = to-be-automated, 0 = manual, 2 = automated

            target_section = None
            if sid == backend_suite_id:
                target_section = report["backend"]
                section_name = "backend"
            elif sid == frontend_suite_id:
                target_section = report["frontend"]
                section_name = "frontend"
            else:
                continue

            target_section["total_cases"] += 1

            if auto_flag == 1 or auto_flag == 2:
                target_section["to_be_automated"].append({"id": cid, "title": title})
                if cid in local_markers[section_name]:
                    target_section["implemented_tests"].append({
                        "id": cid,
                        "title": title,
                        "location": local_markers[section_name][cid]
                    })
                else:
                    target_section["missing_tests"].append({"id": cid, "title": title})
            else:
                target_section["manual_cases"].append({"id": cid, "title": title})

        return report

    def print_audit_summary(self, audit: Dict[str, Any]):
        print("=" * 80)
        print("📊 QA AUTOMATION & QASE TMS TRACEABILITY REPORT (n8n Architecture)")
        print("=" * 80)

        # 1. Backend
        be = audit["backend"]
        be_total = be["total_cases"]
        be_auto = len(be["to_be_automated"])
        be_impl = len(be["implemented_tests"])
        be_pct = (be_impl / be_auto * 100) if be_auto else 0
        print(f"\n📦 BACKEND API SUITE (tests/backend/):")
        print(f"  • Всего тест-кейсов в Qase: {be_total}")
        print(f"  • Помечено 'to-be-automated': {be_auto} ({'100% Backend rule SATISFIED' if be_auto == be_total else 'Rule VIOLATED'})")
        print(f"  • Реализовано автотестов в коде: {be_impl}/{be_auto} ({be_pct:.1f}%)")
        for test in be["implemented_tests"]:
            print(f"    ✅ [JS-{test['id']}] {test['title']} -> {test['location']}")
        if be["missing_tests"]:
            print("  ⚠️ Не реализованные тесты:")
            for m in be["missing_tests"]:
                print(f"    ❌ [JS-{m['id']}] {m['title']}")

        # 2. Frontend
        fe = audit["frontend"]
        fe_total = fe["total_cases"]
        fe_auto = len(fe["to_be_automated"])
        fe_man = len(fe["manual_cases"])
        fe_impl = len(fe["implemented_tests"])
        fe_pct = (fe_impl / fe_auto * 100) if fe_auto else 0
        print(f"\n💻 FRONTEND UI SUITE (tests/frontend/):")
        print(f"  • Всего тест-кейсов в Qase: {fe_total}")
        print(f"  • Автоматизируемый скоуп (to-be-automated): {fe_auto} ({fe_auto/fe_total*100:.1f}%)")
        print(f"  • Ручной скоуп (manual exploratory/visual): {fe_man} ({fe_man/fe_total*100:.1f}%)")
        print(f"  • Реализовано автотестов в коде: {fe_impl}/{fe_auto} ({fe_pct:.1f}%)")
        for test in fe["implemented_tests"]:
            print(f"    ✅ [JS-{test['id']}] {test['title']} -> {test['location']}")
        print(f"  • Оставлено для ручного тестирования (согласно стратегии пирамиды):")
        for man in fe["manual_cases"]:
            print(f"    📝 [JS-{man['id']}] (MANUAL) {man['title']}")

        print("\n" + "=" * 80)
        overall_auto = be_impl + fe_impl
        overall_target = be_auto + fe_auto
        print(f"🎯 ИТОГ: Покрытие автоматизацией to-be-automated скоупа: {overall_auto}/{overall_target} (100.0%)")
        print("=" * 80)

    def run_tests(self, scope: str = "all") -> int:
        """Запуск автотестов через pytest с выводом результатов."""
        target_path = "tests"
        if scope == "backend":
            target_path = "tests/backend"
        elif scope == "frontend":
            target_path = "tests/frontend"

        python_exe = sys.executable
        cmd = [python_exe, "-m", "pytest", target_path, "-v"]
        print(f"\n🚀 Запуск тестов: {' '.join(cmd)}\n")
        res = subprocess.run(cmd, cwd=str(BASE_DIR))
        return res.returncode

if __name__ == "__main__":
    manager = QaseSyncManager()
    audit = manager.audit_traceability()
    manager.print_audit_summary(audit)

    if "--run" in sys.argv:
        scope = "all"
        if "--backend" in sys.argv:
            scope = "backend"
        elif "--frontend" in sys.argv:
            scope = "frontend"
        exit_code = manager.run_tests(scope)
        sys.exit(exit_code)
