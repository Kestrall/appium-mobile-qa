"""Authentification : parcours critique numero 1 d'une app de controle d'acces."""
import allure
import pytest

from pages.dialogs import AndroidAlert
from tests.data import LOCKED_USER, VALID_USER


@pytest.fixture
def on_login_screen(catalog, nav, login_page):
    nav.open_menu_item("login")
    return login_page.wait_loaded()


@allure.feature("Authentification")
@pytest.mark.smoke
@pytest.mark.tc("MQA-10")
def test_login_success_lands_on_catalog(on_login_screen, driver):
    from pages.catalog_page import CatalogPage

    on_login_screen.login(*VALID_USER)
    assert CatalogPage(driver).is_loaded(timeout=10)


@allure.feature("Authentification")
@pytest.mark.regression
@pytest.mark.tc("MQA-11")
@pytest.mark.parametrize(
    "username, password, expected",
    [
        ("", "10203040", "Username is required"),
        ("bob@example.com", "", {"android": "Enter Password", "ios": "Password is required"}),
    ],
    ids=["identifiant-vide", "mot-de-passe-vide"],
)
def test_login_validation_errors(on_login_screen, platform, username, password, expected):
    on_login_screen.login(username, password)
    expected = expected[platform] if isinstance(expected, dict) else expected
    assert on_login_screen.error_message() == expected
    on_login_screen.dismiss_error()


@allure.feature("Authentification")
@pytest.mark.regression
@pytest.mark.tc("MQA-12")
@pytest.mark.known_issue("MQA-BUG-1")
def test_locked_user_is_rejected(on_login_screen, platform, request):
    """Un compte verrouille ne doit jamais acceder a l'app.

    Ecart de parite constate : iOS laisse passer le compte verrouille
    (voir docs/DEFECTS.md, MQA-BUG-1). xfail strict : si iOS est corrige,
    le test passera en XPASS et fera echouer la campagne pour qu'on retire le marqueur.
    """
    if platform == "ios":
        request.applymarker(pytest.mark.xfail(reason="MQA-BUG-1 : compte verrouille accepte sur iOS", strict=True))

    on_login_screen.login(*LOCKED_USER)
    assert on_login_screen.error_message() == "Sorry this user has been locked out."


@allure.feature("Authentification")
@pytest.mark.regression
@pytest.mark.android_only
@pytest.mark.tc("MQA-13")
def test_logout_requires_confirmation(on_login_screen, nav, driver):
    on_login_screen.login(*VALID_USER)
    nav.open_menu_item("logout")

    dialog = AndroidAlert(driver)
    assert dialog.message() == "Are you sure you want to logout"
    dialog.confirm()

    # Pas d'alerte "You are Successfully logged out." : son affichage est commente
    # dans LoginFragment. On verifie l'effet reel : retour au login, session fermee.
    on_login_screen.wait_loaded()
    nav.open_menu_item("login")  # n'existe que si l'utilisateur est deconnecte
