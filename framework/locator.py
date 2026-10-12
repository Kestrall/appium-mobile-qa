"""Locator multi-plateforme : un seul objet, une strategie par OS.

Priorite des strategies (de la plus stable a la plus fragile) :
  accessibility id > resource-id / name > predicate / UiSelector > XPath (dernier recours)
"""
from __future__ import annotations

from dataclasses import dataclass

from appium.webdriver.common.appiumby import AppiumBy

Strategy = tuple[str, str]


@dataclass(frozen=True)
class Locator:
    android: Strategy | None = None
    ios: Strategy | None = None
    name: str = ""

    def for_platform(self, platform: str) -> Strategy:
        strategy = self.android if platform == "android" else self.ios
        if strategy is None:
            raise NotImplementedError(f"Locator '{self.name}' non defini pour {platform}")
        return strategy


def android_id(resource_id: str) -> Strategy:
    return AppiumBy.ID, f"com.saucelabs.mydemoapp.android:id/{resource_id}"


def acc(value: str) -> Strategy:
    return AppiumBy.ACCESSIBILITY_ID, value


def ui_selector(expr: str) -> Strategy:
    return AppiumBy.ANDROID_UIAUTOMATOR, expr


def predicate(expr: str) -> Strategy:
    return AppiumBy.IOS_PREDICATE, expr


def class_chain(expr: str) -> Strategy:
    return AppiumBy.IOS_CLASS_CHAIN, expr
