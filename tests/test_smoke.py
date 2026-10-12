"""Smoke : l'app demarre, le catalogue s'affiche, la navigation principale repond.

A jouer sur chaque build avant toute autre campagne (gate de CI).
"""
import allure
import pytest

from framework.app import AppState


@allure.feature("Demarrage")
@pytest.mark.smoke
@pytest.mark.tc("MQA-1")
def test_app_launches_on_catalog(app, catalog):
    assert app.state() == AppState.RUNNING_FOREGROUND
    assert catalog.visible_product_names(), "Aucun produit affiche au demarrage"


@allure.feature("Demarrage")
@pytest.mark.smoke
@pytest.mark.tc("MQA-2")
def test_cold_start_is_fast_enough(driver, app, run_config):
    """Temps de demarrage a froid : indicateur simple de regression perf."""
    import time

    from pages.catalog_page import CatalogPage

    driver.terminate_app(run_config.app_id)
    start = time.monotonic()
    driver.activate_app(run_config.app_id)
    CatalogPage(driver).wait_loaded(timeout=30)
    elapsed = time.monotonic() - start

    allure.attach(f"{elapsed:.2f}s", "cold-start", allure.attachment_type.TEXT)
    # seuil large : mesure "boite noire" via Appium, sert a detecter une derive, pas a benchmarker
    assert elapsed < 10, f"Demarrage a froid trop long : {elapsed:.1f}s"


@allure.feature("Navigation")
@pytest.mark.smoke
@pytest.mark.tc("MQA-3")
def test_empty_cart_from_fresh_start(catalog, nav, cart):
    nav.open_cart()
    assert cart.is_empty()
    assert cart.item_count() == 0
