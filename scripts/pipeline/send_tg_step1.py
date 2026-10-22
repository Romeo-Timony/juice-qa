import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from scripts.telegram_notifier import notify_pipeline_started, notify_gate1_waiting

notify_pipeline_started("JS-16", "[Frontend] ТЗ: Разработка интерфейса, форм регистрации/логина и профиля пользователя")
notify_gate1_waiting("JS-16", bdd_count=12, rtm_count=12)
print("Telegram notifications sent successfully!")
