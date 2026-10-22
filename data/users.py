"""
Тестовые персоны и профили пользователей OWASP Juice Shop.
Сидируются из data/static/users.yml при старте приложения.
"""
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class UserPersona:
    """Модель тестового пользователя для автотестов."""
    name: str
    email: str
    password: str
    role: str
    wallet_balance: int
    security_question: str
    security_answer: str
    description: str

    def __repr__(self) -> str:
        return f"<UserPersona {self.name} ({self.role}) balance={self.wallet_balance}>"


class UserPersonas:
    """
    Каталог предопределенных тестовых персон OWASP Juice Shop:
    1. ADMIN - администратор с правами 'admin' (доступ к /#/administration, audit logs).
    2. CUSTOMER_WITH_MONEY (Jim) - покупатель с балансом $100 и сохраненными картами/адресами.
    3. CUSTOMER_WITHOUT_MONEY (Bender) - покупатель с балансом $0 для негативных тестов и BVA.
    """

    ADMIN = UserPersona(
        name="Administrator",
        email="admin@juice-sh.op",
        password="admin123",
        role="admin",
        wallet_balance=0,
        security_question="Mother's maiden name?",
        security_answer="@xI98PxDO+06!",
        description="Администратор системы: роль 'admin', доступ к /#/administration, просмотр пользователей, аудит отзывов"
    )

    CUSTOMER_WITH_MONEY = UserPersona(
        name="Jim",
        email="jim@juice-sh.op",
        password="ncc-1701",
        role="customer",
        wallet_balance=100,
        security_question="Your eldest sibling's middle name?",
        security_answer="Samuel",
        description="Покупатель с деньгами: баланс $100, сохраненные карты и адреса. Идеален для Happy Path чекаута и Deluxe"
    )

    CUSTOMER_WITHOUT_MONEY = UserPersona(
        name="Bender",
        email="bender@juice-sh.op",
        password="OhG0dPlease1nsertLiquor!",
        role="customer",
        wallet_balance=0,
        security_question="Your favorite book?",
        security_answer="Stop'n'Drop",
        description="Покупатель без денег: нулевой баланс. Используется для негативных сценариев, BVA и Top-up пополнения"
    )

    ALL: List[UserPersona] = [ADMIN, CUSTOMER_WITH_MONEY, CUSTOMER_WITHOUT_MONEY]
    CUSTOMERS: List[UserPersona] = [CUSTOMER_WITH_MONEY, CUSTOMER_WITHOUT_MONEY]
