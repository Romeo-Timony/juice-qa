"""
Centralized Crash & Error Monitoring for QAOps and SDET.
Combines:
1. Sentry SDK (Free Tier / Self-hosted / Cloud) for deep exception telemetry.
2. Autonomous Emergency Telegram Dispatcher via sys.excepthook (Zero external dependency).
3. Correlation ID tracking across process boundaries.
"""

import logging
import os
import sys
import traceback
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("crash_monitor")

SENTRY_DSN = os.getenv("SENTRY_DSN", "").strip()


def init_sentry() -> bool:
    """Initializes Sentry SDK if SENTRY_DSN is configured."""
    if not SENTRY_DSN:
        logger.info("Sentry DSN is not configured. Running in autonomous Telegram crash hook mode.")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[sentry_logging],
            traces_sample_rate=1.0,
            environment=os.getenv("ENVIRONMENT", "local"),
            release="juice-qa@1.0.0",
        )
        logger.info("✅ Sentry SDK successfully initialized!")
        return True
    except Exception as exc:
        logger.warning("Failed to initialize Sentry SDK: %s", exc)
        return False


def notify_crash_to_telegram(exc_type, exc_value, exc_traceback, component: str = "QA Daemon") -> bool:
    """Dispatches a structured crash report to Telegram."""
    if issubclass(exc_type, KeyboardInterrupt):
        return False

    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    full_tb = "".join(tb_lines)

    # Extract last call site
    tb_summary = traceback.extract_tb(exc_traceback)
    last_frame = tb_summary[-1] if tb_summary else None
    location = f"{last_frame.filename}:{last_frame.lineno} in {last_frame.name}" if last_frame else "Unknown"

    text = (
        f"🚨 <b>[PROCESS CRASH ALERT] Аварийное падение в {component}</b>\n\n"
        f"📍 <b>Локация:</b> <code>{location}</code>\n"
        f"💥 <b>Тип:</b> <code>{exc_type.__name__}</code>\n"
        f"💬 <b>Ошибка:</b> <code>{str(exc_value)[:300]}</code>\n\n"
        f"📜 <b>Traceback:</b>\n"
        f"<pre>{full_tb[-2000:]}</pre>"
    )

    try:
        from scripts.telegram_notifier import send_telegram
        return send_telegram(text)
    except Exception as exc:
        logger.error("Failed to dispatch Telegram crash alert: %s", exc)
        return False


def install_global_crash_hook(component: str = "QA Agent Daemon") -> None:
    """Installs sys.excepthook to capture any unhandled python crash."""
    init_sentry()
    orig_hook = sys.__excepthook__

    def crash_handler(exc_type, exc_value, exc_tb):
        try:
            if SENTRY_DSN:
                try:
                    import sentry_sdk
                    sentry_sdk.capture_exception(exc_value)
                except Exception:
                    pass
            notify_crash_to_telegram(exc_type, exc_value, exc_tb, component=component)
        except Exception:
            pass
        finally:
            orig_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = crash_handler
    logger.info("✅ Global crash hook installed for [%s]", component)
