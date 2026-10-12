from __future__ import annotations

import re

from framework.base_page import BasePage
from framework.locator import Locator, acc, android_id, predicate


class CartPage(BasePage):
    EMPTY_STATE = Locator(
        android=android_id("noItemTitleTV"),
        ios=predicate('type == "XCUIElementTypeStaticText" AND label == "No Items"'),
        name="panier vide",
    )
    TOTAL_ITEMS = Locator(
        android=android_id("itemsTV"),
        ios=predicate('type == "XCUIElementTypeStaticText" AND label ENDSWITH " Items"'),
        name="nombre d'articles",
    )
    REMOVE = Locator(
        android=acc("Removes product from cart"),
        ios=predicate('type == "XCUIElementTypeButton" AND label == "Remove Item"'),
        name="retirer article",
    )
    GO_SHOPPING = Locator(android=android_id("shoppingBt"), ios=acc("GoShopping"), name="go shopping")

    def item_count(self) -> int:
        """Total d'articles affiche ("3 Items"). 0 si panier vide."""
        if self.is_displayed(self.EMPTY_STATE, timeout=2):
            return 0
        match = re.search(r"(\d+)", self.text_of(self.TOTAL_ITEMS))
        return int(match.group(1)) if match else 0

    def is_empty(self) -> bool:
        return self.is_displayed(self.EMPTY_STATE)

    def remove_first_item(self) -> None:
        self.tap(self.REMOVE)
