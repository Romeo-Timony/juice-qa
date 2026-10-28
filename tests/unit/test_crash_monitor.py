"""
Unit tests for core_utils/crash_monitor.py.
"""

import sys
from unittest.mock import patch
from core_utils.crash_monitor import init_sentry, install_global_crash_hook, notify_crash_to_telegram


def test_init_sentry_without_dsn():
    with patch("os.getenv", return_value=""):
        res = init_sentry()
        assert res is False


def test_install_global_crash_hook():
    orig = sys.excepthook
    try:
        install_global_crash_hook("Test Runner")
        assert sys.excepthook != orig
    finally:
        sys.excepthook = orig


def test_notify_crash_ignores_keyboard_interrupt():
    res = notify_crash_to_telegram(KeyboardInterrupt, KeyboardInterrupt(), None)
    assert res is False


def test_notify_crash_formats_message():
    try:
        raise ValueError("Simulated pipeline failure")
    except ValueError as e:
        exc_type, exc_val, exc_tb = sys.exc_info()
        with patch("scripts.telegram_notifier.send_telegram") as mock_send:
            mock_send.return_value = True
            res = notify_crash_to_telegram(exc_type, exc_val, exc_tb, component="TestComponent")
            assert res is True
            assert mock_send.called
            sent_text = mock_send.call_args[0][0]
            assert "TestComponent" in sent_text
            assert "ValueError" in sent_text
            assert "Simulated pipeline failure" in sent_text
