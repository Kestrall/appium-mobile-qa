from __future__ import annotations

from framework.base_page import BasePage
from framework.locator import Locator, android_id


class CrashPage(BasePage):
    """Ecran de debug Android qui declenche volontairement des crashs."""

    UNCAUGHT = Locator(android=android_id("cause_uncaught_exception_button"), name="crash java")
    NATIVE = Locator(android=android_id("cause_native_crash_button"), name="crash natif")

    def trigger_java_crash(self) -> None:
        self.tap(self.UNCAUGHT)
