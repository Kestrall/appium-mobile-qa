"""Panier : etat partage entre ecrans, coherence des compteurs."""
import allure
import pytest

from tests.data import BACKPACK, BACKPACK_ORANGE, BIKE_LIGHT


@allure.feature("Panier")
@pytest.mark.smoke
@pytest.mark.tc("MQA-20")
def test_add_single_product(catalog, product, nav, cart, platform):
    catalog.open_product(BACKPACK)
    product.wait_loaded().add_to_cart()

    if platform == "android":
        assert nav.cart_badge_count() == 1
    nav.open_cart()
    assert cart.item_count() == 1


@allure.feature("Panier")
@pytest.mark.regression
@pytest.mark.tc("MQA-21")
@pytest.mark.parametrize("quantity", [2, 5])
def test_add_product_with_quantity(catalog, product, nav, cart, quantity):
    catalog.open_product(BACKPACK)
    product.wait_loaded()
    product.set_quantity(quantity)
    assert product.quantity() == quantity
    product.add_to_cart()

    nav.open_cart()
    assert cart.item_count() == quantity


@allure.feature("Panier")
@pytest.mark.regression
@pytest.mark.tc("MQA-22")
def test_zero_quantity_cannot_be_added(catalog, product, nav, cart):
    """Valeur limite : la quantite peut descendre a 0 (choix produit, identique
    iOS / Android) mais l'ajout au panier doit alors etre impossible."""
    catalog.open_product(BACKPACK)
    product.wait_loaded()
    product.decrease()
    assert product.quantity() == 0
    product.try_add_to_cart()

    nav.open_cart()
    assert cart.is_empty()


@allure.feature("Panier")
@pytest.mark.regression
@pytest.mark.tc("MQA-23")
def test_cart_accumulates_different_products(catalog, product, nav, cart, platform):
    for name in (BACKPACK, BACKPACK_ORANGE[platform]):
        nav.open_catalog()
        catalog.wait_loaded()
        catalog.open_product(name)
        product.wait_loaded().add_to_cart()

    nav.open_cart()
    assert cart.item_count() == 2


@allure.feature("Panier")
@pytest.mark.regression
@pytest.mark.tc("MQA-24")
def test_remove_last_item_empties_cart(catalog, product, nav, cart):
    catalog.open_product(BACKPACK)
    product.wait_loaded().add_to_cart()
    nav.open_cart()

    cart.remove_first_item()
    assert cart.is_empty()


@allure.feature("Catalogue")
@pytest.mark.regression
@pytest.mark.tc("MQA-25")
@pytest.mark.known_issue("MQA-BUG-3")
@pytest.mark.expects_crash
def test_every_product_detail_opens(catalog, product, platform, request):
    """Un produit au-dela du 6e de la liste doit s'ouvrir comme les autres.

    Android : ArrayIndexOutOfBoundsException dans ProductCatalogFragment (MQA-BUG-3).
    """
    if platform == "android":
        request.applymarker(pytest.mark.xfail(reason="MQA-BUG-3 : crash index >= 6", strict=True))
    catalog.open_product(BIKE_LIGHT)
    product.wait_loaded()
