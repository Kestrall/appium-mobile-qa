"""Fixtures communes.

Strategie de cycle de vie :
- une session Appium par run (installer l'app a chaque test coute trop cher sur device reel) ;
- avant chaque test : app tuee puis relancee => etat memoire propre (panier, login) ;
- apres chaque test : logs device analyses + preuves attachees au rapport si echec.
"""
from __future__ import annotations

import logging

import pytest

from framework.app import AppController, AppState
from framework.config import RunConfig, load_config
from framework.device_logs import DeviceLogCollector
from framework.driver_factory import create_driver
from framework.evidence import attach_failure_evidence, attach_logs, start_video, stop_video
from pages.cart_page import CartPage
from pages.catalog_page import CatalogPage
from pages.login_page import LoginPage
from pages.navigation import Navigation
from pages.product_page import ProductPage

log = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption("--device", action="store", default=None,
                     help="Profil de config/devices.yaml (sinon DEVICE_PROFILE)")
    parser.addoption("--video", action="store_true", help="Enregistrer l'ecran de chaque test")


# --- selection des tests selon la cible ---------------------------------

def pytest_collection_modifyitems(config, items):
    if all(item.path.parent.name == "unit" for item in items):
        return  # tests unitaires seuls : aucune cible device necessaire
    run = load_config(config.getoption("--device"))
    for item in items:
        if "android_only" in item.keywords and not run.is_android:
            item.add_marker(pytest.mark.skip(reason="Android uniquement"))
        if "ios_only" in item.keywords and not run.is_ios:
            item.add_marker(pytest.mark.skip(reason="iOS uniquement"))
        if "real_device_only" in item.keywords and not run.is_real_device:
            item.add_marker(pytest.mark.skip(reason="Necessite un telephone physique"))
        # identifiant de cas de test => propriete JUnit lue par l'import Xray
        for mark in item.iter_markers("tc"):
            item.user_properties.append(("test_key", mark.args[0]))
        item.user_properties.append(("tags", run.platform))


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    setattr(item, f"rep_{report.when}", report)
    return report


# --- session ------------------------------------------------------------

@pytest.fixture(scope="session")
def run_config(request) -> RunConfig:
    cfg = load_config(request.config.getoption("--device"))
    log.info("Profil %s -> %s", cfg.profile, cfg.capabilities)
    return cfg


@pytest.fixture(scope="session")
def driver(run_config):
    drv = create_driver(run_config)
    yield drv
    drv.quit()


@pytest.fixture(scope="session")
def platform(run_config) -> str:
    return run_config.platform


# --- par test -----------------------------------------------------------

@pytest.fixture
def app(driver, run_config) -> AppController:
    return AppController(driver, run_config.app_id)


@pytest.fixture(autouse=True)
def _fresh_app_and_evidence(request, run_config):
    if request.node.path.parent.name == "unit":
        yield
        return

    driver = request.getfixturevalue("driver")
    controller = AppController(driver, run_config.app_id)
    logs = DeviceLogCollector(driver, run_config.app_id)
    record_video = request.config.getoption("--video")

    controller.restart()
    logs.flush()
    if record_video:
        start_video(driver)

    yield

    failed = getattr(request.node, "rep_call", None) is not None and request.node.rep_call.failed
    report = logs.collect()
    attach_logs(f"{logs.log_type}-analyse", report.summary())
    if failed:
        attach_failure_evidence(driver)
        attach_logs(logs.log_type, report.as_text())
    if record_video:
        stop_video(driver, attach=failed)

    # Garde-fou : un crash dans les logs fait echouer le test meme si l'UI semblait OK
    expects_crash = request.node.get_closest_marker("expects_crash") is not None
    if report.has_crash and not expects_crash:
        attach_logs(logs.log_type, report.as_text())
        pytest.fail(f"Crash detecte dans les logs device :\n{report.summary()}")

    if controller.state() == AppState.NOT_RUNNING and not expects_crash:
        pytest.fail("L'app n'est plus en cours d'execution a la fin du test")


# --- pages --------------------------------------------------------------

@pytest.fixture
def nav(driver) -> Navigation:
    return Navigation(driver)


@pytest.fixture
def catalog(driver) -> CatalogPage:
    return CatalogPage(driver).wait_loaded()


@pytest.fixture
def product(driver) -> ProductPage:
    return ProductPage(driver)


@pytest.fixture
def cart(driver) -> CartPage:
    return CartPage(driver)


@pytest.fixture
def login_page(driver) -> LoginPage:
    return LoginPage(driver)
