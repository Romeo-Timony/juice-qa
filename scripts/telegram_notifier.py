import os
import sys
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

DEFAULT_BOT_TOKEN = "8463540623:AAHmW9uuff8C_XQDk4cLby1GoVyc7-zo4Ek"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or DEFAULT_BOT_TOKEN
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def get_or_detect_chat_id() -> Optional[str]:
    """
    Автоматически определяет chat_id пользователя, если он написал боту /start.
    Сохраняет найденный chat_id в .env для постоянного использования.
    """
    global CHAT_ID
    if CHAT_ID:
        return str(CHAT_ID)

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        res = requests.get(url, timeout=10)
        data = res.json()
        if data.get("ok"):
            results = data.get("result", [])
            for item in reversed(results):
                msg = item.get("message") or item.get("channel_post") or item.get("my_chat_member")
                if msg:
                    chat = msg.get("chat", {})
                    cid = str(chat.get("id"))
                    if cid:
                        CHAT_ID = cid
                        # Сохраняем в .env
                        try:
                            set_key(str(ENV_FILE), "TELEGRAM_CHAT_ID", cid)
                        except Exception:
                            pass
                        print(f"✅ Telegram Chat ID обнаружен и сохранен: {cid} (Пользователь: {chat.get('username') or chat.get('first_name')})")
                        return cid
    except Exception as e:
        print(f"⚠️ Ошибка при опросе Telegram getUpdates: {e}")

    return None


def send_telegram(text: str, reply_markup: Optional[Dict[str, Any]] = None, parse_mode: str = "HTML") -> bool:
    """
    Отправляет форматированное сообщение в Telegram бот QApower.
    """
    chat_id = get_or_detect_chat_id()
    if not chat_id:
        print("⚠️ Пропуск отправки Telegram: chat_id не найден. Отправьте боту @QApower_bot команду /start")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.ok:
            return True
        else:
            print(f"⚠️ Ошибка отправки в Telegram ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"⚠️ Ошибка сетевого запроса к Telegram API: {e}")

    return False


# -----------------------------------------------------------------------------
# Высокоуровневые шаблонные уведомления для пайплайна
# -----------------------------------------------------------------------------

def notify_pipeline_started(issue_key: str, summary: str, actor: str = "Roman Timoshenko"):
    text = (
        f"🚀 <b>[QA PIPELINE] Запуск сквозного цикла</b>\n\n"
        f"📌 <b>Задача:</b> <code>{issue_key}</code>\n"
        f"📝 <b>Описание:</b> {summary}\n"
        f"👤 <b>Инициатор:</b> {actor}\n"
        f"⚙️ <b>Статус:</b> DoR Gate пройден, строится MindMap и BDD-тестплан..."
    )
    markup = {
        "inline_keyboard": [
            [
                {"text": "🔗 Открыть задачу в Jira", "url": f"https://romeo-timony.atlassian.net/browse/{issue_key}"},
                {"text": "📊 n8n Workflow", "url": "http://201.34.147.33:5678"}
            ]
        ]
    }
    return send_telegram(text, reply_markup=markup)


def notify_gate1_waiting(issue_key: str, bdd_count: int, rtm_count: int):
    text = (
        f"⏸️ <b>[QUALITY GATE 1] Ожидание подтверждения QA Lead</b>\n\n"
        f"📌 <b>Задача:</b> <code>{issue_key}</code>\n"
        f"🧪 <b>BDD сценариев сформировано:</b> {bdd_count}\n"
        f"📊 <b>Покрытие матрицы RTM:</b> {rtm_count} требований (100%)\n"
        f"⏳ <b>Статус:</b> Пайплайн на паузе (Human in the Loop).\n\n"
        f"👉 <i>Для утверждения отправьте в комментарий задачи реакцию ❤️ или «ОК»</i>"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "❤️ Перейти в Jira для согласования", "url": f"https://romeo-timony.atlassian.net/browse/{issue_key}"}]
        ]
    }
    return send_telegram(text, reply_markup=markup)


def notify_gate1_approved(issue_key: str, approver: str = "QA Lead"):
    text = (
        f"❤️ <b>[QUALITY GATE 1] Согласован (Human in the Loop)</b>\n\n"
        f"📌 <b>Задача:</b> <code>{issue_key}</code>\n"
        f"👤 <b>Подтвердил:</b> {approver}\n"
        f"✅ <b>Результат:</b> BDD тест-кейсы и матрица RTM приняты.\n"
        f"⚙️ <b>Следующий шаг:</b> Синхронизация с Qase TMS и генерация кода автотестов..."
    )
    return send_telegram(text)


def notify_gate2_waiting(issue_key: str, score: int, verdict: str, summary: str):
    icon = "🛡️" if verdict == "ACCEPT" else "⚠️"
    text = (
        f"{icon} <b>[QUALITY GATE 2] Независимый AI-аудит автотестов</b>\n\n"
        f"📌 <b>Задача:</b> <code>{issue_key}</code>\n"
        f"🤖 <b>Вердикт AI-Аудитора:</b> <b>{verdict}</b> (Оценка: {score}/100)\n"
        f"📋 <b>Резюме:</b> {summary}\n"
        f"⏳ <b>Статус:</b> Ожидание подтверждения QA Lead на промоушн в проект.\n\n"
        f"👉 <i>Для утверждения промоушена отправьте ❤️ в комментарий задачи</i>"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "❤️ Согласовать промоушн в Jira", "url": f"https://romeo-timony.atlassian.net/browse/{issue_key}"}]
        ]
    }
    return send_telegram(text, reply_markup=markup)


def notify_gate2_approved(issue_key: str, approver: str = "QA Lead"):
    text = (
        f"❤️ <b>[QUALITY GATE 2] Промоушн согласован</b>\n\n"
        f"📌 <b>Задача:</b> <code>{issue_key}</code>\n"
        f"👤 <b>Подтвердил:</b> {approver}\n"
        f"✅ <b>Результат:</b> Автотесты перенесены в боевую ветку проекта.\n"
        f"🚀 <b>Следующий шаг:</b> Демон фиксирует коммит в ветке qa/{issue_key.lower()} и запускает CI/CD."
    )
    return send_telegram(text)


def notify_cicd_started(issue_key: str, branch: str, commit_sha: str = ""):
    text = (
        f"⚡ <b>[CI/CD PIPELINE] Запуск автотестов в GitHub Actions</b>\n\n"
        f"📌 <b>Задача:</b> <code>{issue_key}</code>\n"
        f"🌿 <b>Ветка:</b> <code>{branch}</code>\n"
        f"📦 <b>Коммит:</b> <code>{commit_sha[:7]}</code>\n"
        f"🔄 <b>Прогон:</b> Backend API & Frontend Playwright тесты в изолированном контейнере..."
    )
    markup = {
        "inline_keyboard": [
            [{"text": "🐙 GitHub Actions Run", "url": "https://github.com/Romeo-Timony/juice-qa/actions"}]
        ]
    }
    return send_telegram(text, reply_markup=markup)


def notify_pipeline_completed(issue_key: str, success: bool, summary: str, run_url: str = ""):
    if success:
        text = (
            f"🎉 <b>[УСПЕХ] Пайплайн успешно завершен!</b>\n\n"
            f"📌 <b>Задача:</b> <code>{issue_key}</code>\n"
            f"🏁 <b>Финальный статус Jira:</b> <code>Автотесты пройдены</code> (10048)\n"
            f"📊 <b>Результаты тестов:</b>\n{summary}\n\n"
            f"🏆 <i>Все 8 этапов сквозного QA-цикла успешно выполнены!</i>"
        )
    else:
        text = (
            f"❌ <b>[СБОЙ] Пайплайн завершился с ошибкой</b>\n\n"
            f"📌 <b>Задача:</b> <code>{issue_key}</code>\n"
            f"⚠️ <b>Проблема:</b> {summary}\n\n"
            f"🔍 <i>Требуется анализ логов CI/CD и перезапуск.</i>"
        )
    
    buttons = [{"text": "🔗 Открыть в Jira", "url": f"https://romeo-timony.atlassian.net/browse/{issue_key}"}]
    if run_url:
        buttons.append({"text": "📊 Allure / Actions Report", "url": run_url})
    
    markup = {"inline_keyboard": [buttons]}
    return send_telegram(text, reply_markup=markup)


def notify_error(issue_key: str, stage_name: str, error_details: str):
    text = (
        f"🚨 <b>[ОШИБКА ПАЙПЛАЙНА] Сбой на этапе: {stage_name}</b>\n\n"
        f"📌 <b>Задача:</b> <code>{issue_key}</code>\n"
        f"💥 <b>Детали ошибки:</b>\n<pre>{error_details[:500]}</pre>\n\n"
        f"⚠️ <i>Пайплайн приостановлен для диагностики.</i>"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "🔗 Перейти в Jira", "url": f"https://romeo-timony.atlassian.net/browse/{issue_key}"}]
        ]
    }
    return send_telegram(text, reply_markup=markup)


if __name__ == "__main__":
    cid = get_or_detect_chat_id()
    if cid:
        send_telegram("👋 <b>Привет! Telegram-бот QApower успешно подключен к QA Automation Pipeline!</b>\n\nГотов к отправке уведомлений по всем этапам и Quality Gates.")
    else:
        print("Бот ожидает сообщения. Откройте @QApower_bot в Telegram и нажмите /start.")
