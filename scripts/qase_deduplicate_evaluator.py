#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qase Deduplication and Logical Evaluator
========================================
Автоматическая система дедупликации и логической оценки тест-кейсов для Qase TMS.
Выполняет:
1. Загрузку всей базы тест-кейсов из Qase TMS (с поддержкой полной пагинации).
2. Выявление и устранение дубликатов (как по названию, так и по логическим сигнатурам).
3. Логическую оценку кандидатных тест-кейсов перед их добавлением в Qase:
   - Проверка по точным заголовкам (Title match)
   - Проверка по логическим сигнатурам (Endpoint, HTTP Method, Error Code, Target Component)
   - Семантическая оценка схожести сценариев и шагов (Semantic & Token Similarity)
4. Предотвращение раздувания тестовой модели аналогичными проверками.
"""

import os
import sys
import re
import json
import argparse
from typing import Dict, List, Any, Tuple, Optional, Set
from pathlib import Path
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

QASE_API_TOKEN = os.getenv("QASE_API_TOKEN")
QASE_PROJECT_CODE = os.getenv("QASE_PROJECT_CODE", "JS")
QASE_BASE_URL = os.getenv("QASE_API_URL", "https://api.qase.io/v1")


class QaseApiClient:
    def __init__(self):
        if not QASE_API_TOKEN:
            raise ValueError("QASE_API_TOKEN is not defined in .env")
        self.headers = {
            "Token": QASE_API_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_all_suites(self) -> List[Dict[str, Any]]:
        """Загружает все сьюты проекта."""
        url = f"{QASE_BASE_URL}/suite/{QASE_PROJECT_CODE}?limit=100"
        res = requests.get(url, headers=self.headers, timeout=15)
        res.raise_for_status()
        return res.json().get("result", {}).get("entities", [])

    def get_all_cases(self) -> List[Dict[str, Any]]:
        """Загружает ВСЕ тест-кейсы проекта с учетом полной пагинации."""
        all_cases = []
        limit = 100
        offset = 0
        while True:
            url = f"{QASE_BASE_URL}/case/{QASE_PROJECT_CODE}?limit={limit}&offset={offset}"
            res = requests.get(url, headers=self.headers, timeout=15)
            res.raise_for_status()
            data = res.json().get("result", {})
            entities = data.get("entities", [])
            if not entities:
                break
            all_cases.extend(entities)
            offset += len(entities)
            total = data.get("total", 0)
            if offset >= total:
                break
        return all_cases

    def delete_case(self, case_id: int) -> bool:
        """Удаляет тест-кейс из Qase TMS."""
        url = f"{QASE_BASE_URL}/case/{QASE_PROJECT_CODE}/{case_id}"
        res = requests.delete(url, headers=self.headers, timeout=15)
        return res.status_code in [200, 204]

    def delete_suite(self, suite_id: int) -> bool:
        """Удаляет сьют из Qase TMS."""
        url = f"{QASE_BASE_URL}/suite/{QASE_PROJECT_CODE}/{suite_id}"
        res = requests.delete(url, headers=self.headers, timeout=15)
        return res.status_code in [200, 204]


class LogicSignatureExtractor:
    """Извлечение смысловых и технических сигнатур из тест-кейса."""

    API_ENDPOINT_PATTERN = re.compile(r'(/api/[a-zA-Z0-9_\-/]+|/rest/[a-zA-Z0-9_\-/]+|/profile/[a-zA-Z0-9_\-/]+)', re.IGNORECASE)
    HTTP_METHOD_PATTERN = re.compile(r'\b(GET|POST|PUT|PATCH|DELETE|OPTIONS)\b', re.IGNORECASE)
    STATUS_CODE_PATTERN = re.compile(r'\b(200|201|204|400|401|403|404|409|422|500)\b')

    @classmethod
    def extract_api_signature(cls, title: str, description: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        full_text = f"{title} {description} " + " ".join(
            f"{s.get('action', '')} {s.get('data', '')} {s.get('expected_result', '')}" for s in steps
        )

        endpoints = list(set(cls.API_ENDPOINT_PATTERN.findall(full_text)))
        methods = list(set(cls.HTTP_METHOD_PATTERN.findall(full_text)))
        statuses = list(set(cls.STATUS_CODE_PATTERN.findall(full_text)))

        # Определение бизнес-направления
        intent = "general"
        lower = full_text.lower()
        if "sql" in lower or "injection" in lower or "инъекц" in lower:
            intent = "sql_injection"
        elif "jwt" in lower or "bearer" in lower or "токен" in lower:
            intent = "jwt_token_auth"
        elif "смен" in lower and "парол" in lower:
            intent = "change_password"
        elif "сброс" in lower or "reset" in lower:
            intent = "reset_password"
        elif "аватар" in lower or "avatar" in lower or "image" in lower:
            intent = "upload_avatar"
        elif "адрес" in lower or "address" in lower:
            intent = "delivery_address"
        elif "учетн" in lower or "регистрац" in lower or "register" in lower:
            intent = "user_registration"
        elif "вход" in lower or "логин" in lower or "login" in lower:
            intent = "user_login"

        return {
            "endpoints": sorted(endpoints),
            "methods": [m.upper() for m in methods],
            "statuses": sorted(statuses),
            "intent": intent
        }

    @classmethod
    def extract_ui_signature(cls, title: str, description: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        full_text = f"{title} {description} " + " ".join(
            f"{s.get('action', '')} {s.get('data', '')} {s.get('expected_result', '')}" for s in steps
        )
        lower = full_text.lower()

        module = "other"
        if "регистрац" in lower or "registration" in lower:
            module = "registration_page"
        elif "логин" in lower or "вход" in lower or "login" in lower:
            module = "login_page"
        elif "парол" in lower and "смен" in lower:
            module = "change_password_page"
        elif "forgot" in lower or "восстановл" in lower:
            module = "forgot_password_page"
        elif "аватар" in lower or "изображен" in lower:
            module = "profile_avatar"
        elif "адрес" in lower or "address" in lower:
            module = "address_book"

        check_type = "positive"
        if "ошибк" in lower or "неверн" in lower or "занят" in lower or "409" in lower or "401" in lower or "блокировк" in lower:
            check_type = "negative"
        elif "валидац" in lower or "граничн" in lower or "bva" in lower or "длин" in lower:
            check_type = "validation"

        return {
            "module": module,
            "check_type": check_type
        }

    @classmethod
    def tokenize(cls, text: str) -> Set[str]:
        words = re.findall(r'[a-zA-Zа-яА-Я0-9_-]{3,}', text.lower())
        stopwords = {"тест", "проверка", "для", "при", "через", "после", "что", "как", "test", "case", "with", "from"}
        return set(w for w in words if w not in stopwords)

    @classmethod
    def jaccard_similarity(cls, set1: Set[str], set2: Set[str]) -> float:
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0


class QaseDeduplicator:
    def __init__(self):
        self.api = QaseApiClient()

    def clean_existing_duplicates(self) -> Dict[str, Any]:
        """Находит и удаляет дублирующиеся тест-кейсы и паразитные сьюты."""
        print("🔍 Сканирование существующей базы Qase TMS на дубликаты...")
        cases = self.api.get_all_cases()
        suites = self.api.get_all_suites()

        print(f"📦 Всего тест-кейсов в Qase: {len(cases)}")
        print(f"📁 Всего сьютов в Qase: {len(suites)}")

        # Группировка кейсов по нормализованному названию
        cases_by_title: Dict[str, List[Dict[str, Any]]] = {}
        for c in cases:
            norm_title = re.sub(r'\s+', ' ', c["title"]).strip().lower()
            cases_by_title.setdefault(norm_title, []).append(c)

        deleted_cases = []
        kept_cases = []

        for title, clist in cases_by_title.items():
            if len(clist) > 1:
                # Сортируем: сохраняем самый ранний (наименьший ID)
                clist.sort(key=lambda x: x["id"])
                original = clist[0]
                kept_cases.append(original)
                for duplicate in clist[1:]:
                    print(f"🗑️ Удаление дубликата тест-кейса: #{duplicate['id']} «{duplicate['title']}» (Оригинал: #{original['id']})")
                    self.api.delete_case(duplicate["id"])
                    deleted_cases.append(duplicate["id"])
            else:
                kept_cases.append(clist[0])

        # Чистка дублирующихся сьютов
        # Например дублирующийся "Backend" (Suite 40) и пустой "JS-17" (Suite 42)
        deleted_suites = []
        fresh_cases = self.api.get_all_cases()
        used_suite_ids = set(c.get("suite_id") for c in fresh_cases if c.get("suite_id"))

        suites_by_name_and_parent: Dict[Tuple[str, Optional[int]], List[Dict[str, Any]]] = {}
        for s in suites:
            key = (s["title"].strip().lower(), s.get("parent_id"))
            suites_by_name_and_parent.setdefault(key, []).append(s)

        for (title, parent_id), slist in suites_by_name_and_parent.items():
            if len(slist) > 1:
                slist.sort(key=lambda x: x["id"])
                for duplicate_suite in slist[1:]:
                    # Если в сьюте больше нет тестов, удаляем его
                    if duplicate_suite["id"] not in used_suite_ids:
                        print(f"📁 Удаление паразитного дубликата папки #{duplicate_suite['id']} «{duplicate_suite['title']}»")
                        self.api.delete_suite(duplicate_suite["id"])
                        deleted_suites.append(duplicate_suite["id"])

        print(f"✅ Очистка завершена. Удалено дубликатов кейсов: {len(deleted_cases)}, папок: {len(deleted_suites)}")
        return {
            "deleted_cases_count": len(deleted_cases),
            "deleted_cases": deleted_cases,
            "deleted_suites": deleted_suites,
            "remaining_cases_count": len(fresh_cases)
        }

    def evaluate_candidates(self, candidates: List[Dict[str, Any]], is_backend: bool = True) -> Dict[str, Any]:
        """
        Проводит строгую оценку списка кандидатных тест-кейсов против всей существующей базы Qase.
        Возвращает:
        - unique_cases: список тест-кейсов, прошедших валидацию
        - rejected_cases: список отклонённых тест-кейсов с подробной причиной отклонения
        """
        existing_cases = self.api.get_all_cases()
        print(f"🧠 Логическая оценка {len(candidates)} кандидатов против {len(existing_cases)} существующих кейсов...")

        existing_profiles = []
        for ec in existing_cases:
            title = ec.get("title", "")
            desc = ec.get("description", "")
            steps = ec.get("steps", [])
            norm_title = re.sub(r'\s+', ' ', title).strip().lower()
            tokens = LogicSignatureExtractor.tokenize(f"{title} {desc}")
            api_sig = LogicSignatureExtractor.extract_api_signature(title, desc, steps)
            ui_sig = LogicSignatureExtractor.extract_ui_signature(title, desc, steps)

            existing_profiles.append({
                "id": ec["id"],
                "title": title,
                "norm_title": norm_title,
                "tokens": tokens,
                "api_sig": api_sig,
                "ui_sig": ui_sig
            })

        unique_cases = []
        rejected_cases = []

        for cand in candidates:
            c_title = cand.get("title", "")
            c_desc = cand.get("description", "")
            c_steps = cand.get("steps", [])
            c_norm_title = re.sub(r'\s+', ' ', c_title).strip().lower()
            c_tokens = LogicSignatureExtractor.tokenize(f"{c_title} {c_desc}")
            c_api_sig = LogicSignatureExtractor.extract_api_signature(c_title, c_desc, c_steps)
            c_ui_sig = LogicSignatureExtractor.extract_ui_signature(c_title, c_desc, c_steps)

            is_duplicate = False
            reject_reason = ""
            matched_existing_id = None

            # 1. Проверка на точный заголовок
            for ep in existing_profiles:
                if ep["norm_title"] == c_norm_title:
                    is_duplicate = True
                    matched_existing_id = ep["id"]
                    reject_reason = f"Точное совпадение заголовка с существующим тест-кейсом Qase #{ep['id']} («{ep['title']}»)"
                    break

            # 2. Логическая проверка по сигнатуре API (для бэкенда)
            if not is_duplicate and is_backend:
                for ep in existing_profiles:
                    # Если совпадают эндпоинт, метод и ключевое бизнес-намерение (intent)
                    ep_endpoints = ep["api_sig"]["endpoints"]
                    c_endpoints = c_api_sig["endpoints"]
                    common_endpoints = set(ep_endpoints) & set(c_endpoints)

                    ep_methods = ep["api_sig"]["methods"]
                    c_methods = c_api_sig["methods"]
                    common_methods = set(ep_methods) & set(c_methods)

                    if common_endpoints and common_methods:
                        if ep["api_sig"]["intent"] == c_api_sig["intent"] and c_api_sig["intent"] != "general":
                            is_duplicate = True
                            matched_existing_id = ep["id"]
                            reject_reason = (
                                f"Логический дубликат API проверки для эндпоинта {list(common_endpoints)} "
                                f"[{list(common_methods)[0]}] с намерением '{c_api_sig['intent']}' "
                                f"(Уже реализован в Qase #{ep['id']} «{ep['title']}»)"
                            )
                            break

            # 3. Логическая проверка по UI (для фронтенда)
            if not is_duplicate and not is_backend:
                for ep in existing_profiles:
                    if ep["ui_sig"]["module"] == c_ui_sig["module"] and ep["ui_sig"]["check_type"] == c_ui_sig["check_type"] and c_ui_sig["module"] != "other":
                        sim = LogicSignatureExtractor.jaccard_similarity(ep["tokens"], c_tokens)
                        if sim > 0.65:
                            is_duplicate = True
                            matched_existing_id = ep["id"]
                            reject_reason = (
                                f"Логический UI дубликат модуля '{c_ui_sig['module']}' ({c_ui_sig['check_type']}) "
                                f"со схожестью шагов {round(sim*100)}% с Qase #{ep['id']} «{ep['title']}»"
                            )
                            break

            # 4. Общая семантическая проверка сходства (Jaccard > 0.85)
            if not is_duplicate:
                for ep in existing_profiles:
                    sim = LogicSignatureExtractor.jaccard_similarity(ep["tokens"], c_tokens)
                    if sim >= 0.85:
                        is_duplicate = True
                        matched_existing_id = ep["id"]
                        reject_reason = f"Высокое семантическое сходство ({round(sim*100)}%) сценария с Qase #{ep['id']} «{ep['title']}»"
                        break

            if is_duplicate:
                rejected_cases.append({
                    "candidate_title": c_title,
                    "existing_case_id": matched_existing_id,
                    "reason": reject_reason
                })
                print(f"⚠️ [ОТКЛОНЕН] «{c_title}» -> {reject_reason}")
            else:
                unique_cases.append(cand)
                # Добавляем в текущий пул, чтобы избежать дублей внутри самого списка кандидатов
                existing_profiles.append({
                    "id": f"CAND-{len(unique_cases)}",
                    "title": c_title,
                    "norm_title": c_norm_title,
                    "tokens": c_tokens,
                    "api_sig": c_api_sig,
                    "ui_sig": c_ui_sig
                })
                print(f"✅ [ОДОБРЕНО К ДОБАВЛЕНИЮ] «{c_title}»")

        return {
            "total_candidates": len(candidates),
            "approved_unique_count": len(unique_cases),
            "rejected_count": len(rejected_cases),
            "unique_cases": unique_cases,
            "rejected_cases": rejected_cases
        }


def main():
    parser = argparse.ArgumentParser(description="Qase TMS Deduplication & Logical Evaluation Engine")
    parser.add_argument("--clean-duplicates", action="store_true", help="Найти и удалить все существующие дубликаты кейсов и папок в Qase")
    parser.add_argument("--evaluate-file", type=str, help="JSON файл со списком тест-кейсов для проверки на уникальность")
    parser.add_argument("--is-backend", action="store_true", help="Применять правила логической проверки для бэкенда")

    args = parser.parse_args()
    engine = QaseDeduplicator()

    if args.clean_duplicates:
        engine.clean_existing_duplicates()
    elif args.evaluate_file:
        data = json.loads(Path(args.evaluate_file).read_text(encoding="utf-8"))
        res = engine.evaluate_candidates(data, is_backend=args.is_backend)
        print("\n" + json.dumps({
            "approved_unique_count": res["approved_unique_count"],
            "rejected_count": res["rejected_count"],
            "rejected_summary": res["rejected_cases"]
        }, indent=2, ensure_ascii=False))
    else:
        # По умолчанию сканируем и чистим
        engine.clean_existing_duplicates()


if __name__ == "__main__":
    main()
