"""Boites de dialogue applicatives (pas les popups de permission systeme)."""
from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from framework.base_page import BasePage
from framework.locator import Locator


class AndroidAlert(BasePage):
    MESSAGE = Locator(android=(AppiumBy.ID, "android:id/message"), name="message dialog")
    POSITIVE = Locator(android=(AppiumBy.ID, "android:id/button1"), name="bouton positif")
    NEGATIVE = Locator(android=(AppiumBy.ID, "android:id/button2"), name="bouton negatif")

    def message(self) -> str:
        return self.text_of(self.MESSAGE)

    def confirm(self) -> None:
        self.tap(self.POSITIVE)

    def cancel(self) -> None:
        self.tap(self.NEGATIVE)
