"""Interactions avec l'OS : permissions, interruptions, crash.

C'est la partie la plus proche du metier "app qui pilote du materiel" :
camera (video interphone), app mise en arriere-plan par un appel,
et capacite a detecter un crash depuis les traces device.
"""
import allure
import pytest

from framework.app import AppState
from pages.catalog_page import CatalogPage
from pages.crash_page import CrashPage
from pages.qr_scanner_page import QrScannerPage
from tests.data import BACKPACK


@allure.feature("Permissions")
@pytest.mark.regression
@pytest.mark.tc("MQA-30")
@pytest.mark.known_issue("MQA-BUG-4")
def test_camera_permission_denied_is_handled(app, catalog, nav, driver, platform, request):
    """Refus camera : un seul refus suffit, l'app ne redemande pas et reste utilisable.

    Android : la permission est redemandee immediatement apres le refus (MQA-BUG-4).
    """
    if platform == "android":
        request.applymarker(pytest.mark.xfail(reason="MQA-BUG-4 : popup redemandee apres refus", strict=True))
    app.reset_camera_permission()
    catalog.wait_loaded()
    nav.open_menu_item("qr")
    if not app.answer_permission(allow=False):
        pytest.skip("Pas de popup : permission deja tranchee sur ce device (reinstaller l'app)")

    # la popup est une activite systeme : l'app ne repasse au premier plan qu'apres sa fermeture
    assert app.wait_for_state(AppState.RUNNING_FOREGROUND, timeout=5), "Popup de permission redemandee"
    assert not app.answer_permission(allow=False, timeout=3), "Popup de permission redemandee"
    if platform == "android":
        # comportement specifie Android : retour au catalogue
        assert CatalogPage(driver).is_loaded(timeout=10)


@allure.feature("Permissions")
@pytest.mark.regression
@pytest.mark.real_device_only
@pytest.mark.tc("MQA-31")
def test_camera_permission_granted_shows_preview(app, catalog, nav, driver):
    app.reset_camera_permission()
    catalog.wait_loaded()
    nav.open_menu_item("qr")
    app.answer_permission(allow=True)
    assert QrScannerPage(driver).camera_preview_visible()


@allure.feature("Robustesse")
@pytest.mark.regression
@pytest.mark.tc("MQA-32")
def test_cart_survives_background(app, catalog, product, nav, cart):
    """Interruption type 'appel entrant' : l'etat utilisateur doit etre conserve."""
    catalog.open_product(BACKPACK)
    product.wait_loaded().add_to_cart()

    app.send_to_background(5)

    assert app.state() == AppState.RUNNING_FOREGROUND
    nav.open_cart()
    assert cart.item_count() == 1


@allure.feature("Traces")
@pytest.mark.regression
@pytest.mark.android_only
@pytest.mark.expects_crash
@pytest.mark.tc("MQA-33")
def test_crash_is_detected_in_logcat(app, catalog, nav, driver, run_config):
    """Valide la chaine de qualification : crash provoque => detecte dans logcat."""
    from framework.device_logs import DeviceLogCollector

    logs = DeviceLogCollector(driver, run_config.app_id)
    nav.open_menu_item("crash")
    CrashPage(driver).trigger_java_crash()

    # Pas d'assertion sur l'etat de l'app : Android relance souvent l'activite
    # precedente apres un crash. La preuve fiable, ce sont les traces.
    report = logs.collect_until(lambda r: r.has_crash, timeout=10)
    assert report.has_crash, "Le crash n'a pas ete retrouve dans logcat"
    assert any("You clicked on the wrong button!" in line for line in report.lines)


@allure.feature("Robustesse")
@pytest.mark.regression
@pytest.mark.android_only
@pytest.mark.expects_crash
@pytest.mark.known_issue("MQA-BUG-5")
@pytest.mark.tc("MQA-34")
@pytest.mark.xfail(reason="MQA-BUG-5 : crash a la restauration (constructeur de Fragment manquant)", strict=True)
def test_app_restores_after_process_death(app, catalog, driver, run_config):
    """Retour dans l'app apres que l'OS a tue le process en arriere-plan."""
    from framework.device_logs import DeviceLogCollector

    logs = DeviceLogCollector(driver, run_config.app_id)
    logs.flush()
    app.simulate_process_death()

    assert CatalogPage(driver).is_loaded(timeout=10), "Catalogue absent apres restauration"
    report = logs.collect_until(lambda r: r.has_crash, timeout=3)
    assert not report.has_crash, report.summary()
