"""Socle des Page Objects : attentes explicites, gestes, helpers multi-plateformes."""
from __future__ import annotations

import logging

from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webdriver import WebDriver
from appium.webdriver.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from framework.locator import Locator

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15


class BasePage:
    def __init__(self, driver: WebDriver, timeout: int = DEFAULT_TIMEOUT):
        self.driver = driver
        self.timeout = timeout
        self.platform = driver.capabilities["platformName"].lower()

    @property
    def is_android(self) -> bool:
        return self.platform == "android"

    @property
    def is_ios(self) -> bool:
        return self.platform == "ios"

    # --- recherche -------------------------------------------------------

    def _wait(self, timeout: int | None = None) -> WebDriverWait:
        return WebDriverWait(self.driver, timeout or self.timeout, poll_frequency=0.3)

    def find(self, locator: Locator, timeout: int | None = None) -> WebElement:
        strategy = locator.for_platform(self.platform)
        try:
            return self._wait(timeout).until(EC.presence_of_element_located(strategy))
        except TimeoutException as exc:
            raise TimeoutException(f"Element introuvable : {locator.name or strategy}") from exc

    def find_visible(self, locator: Locator, timeout: int | None = None) -> WebElement:
        strategy = locator.for_platform(self.platform)
        try:
            return self._wait(timeout).until(EC.visibility_of_element_located(strategy))
        except TimeoutException as exc:
            raise TimeoutException(f"Element non visible : {locator.name or strategy}") from exc

    def find_all(self, locator: Locator) -> list[WebElement]:
        return self.driver.find_elements(*locator.for_platform(self.platform))

    def is_displayed(self, locator: Locator, timeout: int = 3) -> bool:
        try:
            return self.find_visible(locator, timeout).is_displayed()
        except (TimeoutException, NoSuchElementException):
            return False

    def wait_gone(self, locator: Locator, timeout: int | None = None) -> None:
        strategy = locator.for_platform(self.platform)
        self._wait(timeout).until(EC.invisibility_of_element_located(strategy))

    # --- actions ---------------------------------------------------------

    def tap(self, locator: Locator, timeout: int | None = None) -> None:
        strategy = locator.for_platform(self.platform)
        log.info("tap %s", locator.name or strategy)
        self._wait(timeout).until(EC.element_to_be_clickable(strategy)).click()

    def type_text(self, locator: Locator, text: str, clear: bool = True) -> None:
        element = self.find_visible(locator)
        element.click()
        if clear:
            element.clear()
        element.send_keys(text)

    def text_of(self, locator: Locator) -> str:
        element = self.find_visible(locator)
        # iOS expose le texte via "label" plus fiablement que .text sur certains types
        return element.text if self.is_android else (element.get_attribute("label") or element.text)

    def hide_keyboard(self) -> None:
        try:
            if self.is_ios:
                self.driver.execute_script("mobile: hideKeyboard", {"keys": ["return"]})
            elif self.driver.is_keyboard_shown():
                self.driver.hide_keyboard()
        except Exception:  # clavier deja ferme : pas grave
            pass

    # --- scroll ----------------------------------------------------------

    def android_scroll_into_view(self, selector: str) -> WebElement:
        return self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f"new UiScrollable(new UiSelector().scrollable(true).instance(0)).scrollIntoView({selector})",
        )

    def scroll_to_text(self, text: str, starts_with: bool = False) -> WebElement:
        """Scrolle jusqu'a un texte puis renvoie l'element (implementation native par OS)."""
        if self.is_android:
            matcher = "textStartsWith" if starts_with else "text"
            return self.android_scroll_into_view(f'new UiSelector().{matcher}("{text}")')

        op = "BEGINSWITH" if starts_with else "=="
        pred = f'label {op} "{text}" AND type == "XCUIElementTypeStaticText"'
        for _ in range(6):
            elements = self.driver.find_elements(AppiumBy.IOS_PREDICATE, pred)
            visible = [e for e in elements if e.is_displayed()]
            if visible:
                return visible[0]
            self.driver.execute_script("mobile: swipe", {"direction": "up"})
        raise NoSuchElementException(f"Texte '{text}' introuvable apres scroll")
