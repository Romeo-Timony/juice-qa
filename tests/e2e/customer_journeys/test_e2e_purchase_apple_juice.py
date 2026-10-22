"""
====================================================================================================
OWASP Juice Shop - End-to-End (E2E) Test Suite
Domaine:        E2E Customer Journey (Playwright UI)
Scénario:       Authentification et achat complet de jus de pomme (Apple Juice)
Architecture:   Page Object Model (Playwright) + Pytest + BDD Gherkin + Allure TestOps
====================================================================================================
"""
import pytest
import allure
from playwright.sync_api import Page, expect

from pages.login_page import LoginPage
from pages.catalog_page import CatalogPage
from pages.checkout_page import CheckoutPage
from data.users import UserPersonas


@allure.epic("OWASP Juice Shop")
@allure.feature("E2E User Journeys: Customer Checkout")
@allure.story("Authentification et achat de jus de pomme (Apple Juice) de bout en bout")
@pytest.mark.e2e
@pytest.mark.ui
class TestE2EPurchaseAppleJuice:
    """Suite de tests E2E couvrant l'authentification et le parcours d'achat complet dans le navigateur."""

    @allure.title("E2E: Connexion utilisateur, ajout de jus de pomme au panier et validation de commande")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_login_and_buy_apple_juice(self, page: Page, base_url: str, isolate_wallet_state):
        """
        GIVEN: Un utilisateur enregistré (Jim) accède à la page de connexion et s'authentifie
        WHEN:  L'utilisateur ajoute une bouteille d'Apple Juice au panier depuis le catalogue
        AND:   L'utilisateur valide les étapes de livraison et de paiement (Checkout)
        THEN:  La commande est confirmée et l'écran de remerciement s'affiche avec succès
        """
        login_page = LoginPage(page, base_url)
        catalog_page = CatalogPage(page, base_url)
        checkout_page = CheckoutPage(page, base_url)
        user = UserPersonas.CUSTOMER_WITH_MONEY

        # -------------------------------------------------------------------------
        # ÉTAPE 1: Authentification de l'utilisateur
        # -------------------------------------------------------------------------
        with allure.step(f"1. GIVEN: Authentification de l'utilisateur {user.name} ({user.email})"):
            login_page.open()
            login_page.login(email=user.email, password=user.password)
            page.wait_for_timeout(1000)
            token = login_page.get_token_from_storage()
            assert token is not None and token.startswith("ey"), (
                "L'authentification a échoué: aucun JWT valide trouvé dans localStorage"
            )

        # -------------------------------------------------------------------------
        # ÉTAPE 2: Navigation dans le catalogue et ajout du jus de pomme au panier
        # -------------------------------------------------------------------------
        with allure.step("2. WHEN: Recherche et ajout du produit 'Apple Juice' au panier"):
            catalog_page.open()
            catalog_page.add_product_to_basket("Apple Juice")
            # Attente de la confirmation visuelle (snack-bar ou mise à jour du panier)
            page.wait_for_timeout(1000)

        # -------------------------------------------------------------------------
        # ÉTAPE 3: Accès au panier et début du processus de paiement
        # -------------------------------------------------------------------------
        with allure.step("3. AND: Accès au panier et initialisation du Checkout"):
            catalog_page.go_to_basket()
            page.wait_for_timeout(1000)
            checkout_page.start_checkout_from_basket()

        # -------------------------------------------------------------------------
        # ÉTAPE 4: Sélection de l'adresse de livraison
        # -------------------------------------------------------------------------
        with allure.step("4. AND: Sélection de l'adresse de livraison"):
            page.wait_for_timeout(1000)
            checkout_page.select_address_and_proceed()

        # -------------------------------------------------------------------------
        # ÉTAPE 5: Choix du mode de livraison
        # -------------------------------------------------------------------------
        with allure.step("5. AND: Choix de la vitesse de livraison"):
            page.wait_for_timeout(1000)
            checkout_page.select_delivery_speed_and_proceed()

        # -------------------------------------------------------------------------
        # ÉTAPE 6: Sélection du moyen de paiement
        # -------------------------------------------------------------------------
        with allure.step("6. AND: Sélection du moyen de paiement (Wallet ou Carte)"):
            page.wait_for_timeout(1000)
            checkout_page.select_payment_and_proceed()

        # -------------------------------------------------------------------------
        # ÉTAPE 7: Récapitulatif et validation finale de la commande
        # -------------------------------------------------------------------------
        with allure.step("7. AND: Vérification du récapitulatif et passage de commande"):
            page.wait_for_timeout(1000)
            checkout_page.place_order()

        # -------------------------------------------------------------------------
        # ÉTAPE 8: Confirmation finale de l'achat
        # -------------------------------------------------------------------------
        with allure.step("8. THEN: Confirmation de la commande et affichage du message de succès"):
            checkout_page.verify_order_completion()
            assert "/order-completion" in page.url, (
                f"L'URL finale attendue devait contenir '/order-completion', URL reçue: {page.url}"
            )
