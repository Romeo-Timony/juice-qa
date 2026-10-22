"""
Unit-тесты для моделей данных фреймворка (data/users.py).
Проверяют контракты тестовых персон, иммутабельность датакласса и граничные значения.
Время выполнения: < 10 мс (без сетевых вызовов).
"""
import pytest
import allure
from data.users import UserPersonas, UserPersona

@allure.epic("AQA Framework")
@allure.feature("Unit Testing: Data Models")
@pytest.mark.unit
class TestUserModelsUnit:

    def test_admin_persona_contract(self):
        """Проверка контракта и полей персоны Администратора."""
        admin = UserPersonas.ADMIN
        assert admin.role == "admin"
        assert admin.email == "admin@juice-sh.op"
        assert len(admin.password) >= 5
        assert "@xI98PxDO+06!" in admin.security_answer

    def test_customer_with_money_contract(self):
        """Проверка контракта персоны с деньгами (Jim)."""
        jim = UserPersonas.CUSTOMER_WITH_MONEY
        assert jim.role == "customer"
        assert jim.wallet_balance == 100
        assert jim.email == "jim@juice-sh.op"

    def test_customer_without_money_contract(self):
        """Проверка контракта персоны без денег (Bender)."""
        bender = UserPersonas.CUSTOMER_WITHOUT_MONEY
        assert bender.role == "customer"
        assert bender.wallet_balance == 0
        assert bender.email == "bender@juice-sh.op"

    def test_immutability_of_user_persona(self):
        """Проверка защиты от мутаций: UserPersona объявлен как frozen=True."""
        admin = UserPersonas.ADMIN
        with pytest.raises(Exception):  # FrozenInstanceError
            admin.role = "hacked"
