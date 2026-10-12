"""Creation du driver Appium selon la plateforme du profil."""
from __future__ import annotations

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from appium.webdriver.webdriver import WebDriver

from framework.config import RunConfig


def create_driver(config: RunConfig) -> WebDriver:
    options = UiAutomator2Options() if config.is_android else XCUITestOptions()
    options.load_capabilities(config.capabilities)
    driver = webdriver.Remote(config.appium_url, options=options)
    driver.implicitly_wait(0)
    return driver
