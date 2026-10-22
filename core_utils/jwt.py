"""
Утилиты для работы с JWT токенами в AQA фреймворке.
"""
import json
import base64
from typing import Dict, Any

def decode_jwt_payload(token: str) -> Dict[str, Any]:
    """
    Декодирует payload JWT токена без валидации криптографической подписи.
    Корректно обрабатывает padding base64.
    """
    if not token or not isinstance(token, str):
        return {}
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    payload_b64 = parts[1]
    payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
    try:
        decoded_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(decoded_bytes.decode("utf-8"))
    except Exception:
        return {}
