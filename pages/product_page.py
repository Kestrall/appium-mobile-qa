from __future__ import annotations

from framework.base_page import BasePage
from framework.locator import Locator, acc, android_id, predicate


class ProductPage(BasePage):
    SCREEN = Locator(
        android=android_id("colorRV"),  # propre a l'ecran detail, en haut de page
        ios=acc("ProductDetails-screen"),
        name="ecran produit",
    )
    PLUS = Locator(android=acc("Increase item quantity"), ios=acc("AddPlus Icons"), name="quantite +")
    MINUS = Locator(android=acc("Decrease item quantity"), ios=acc("SubtractMinus Icons"), name="quantite -")
    QUANTITY = Locator(android=android_id("noTV"), ios=acc("Amount"), name="quantite")
    ADD_TO_CART = Locator(
        android=acc("Tap to add product to cart"),
        ios=predicate('type == "XCUIElementTypeButton" AND (name == "AddToCart" OR label == "Add To Cart")'),
        name="ajouter au panier",
    )

    def wait_loaded(self) -> "ProductPage":
        self.find_visible(self.SCREEN)
        return self

    def _reveal_cart_controls(self) -> None:
        # Android : quantite et "Add to cart" sont sous la ligne de flottaison sur
        # les ecrans courts (constate sur Huawei P20 Lite) et absents de l'arbre UI tant
        # qu'ils ne sont pas affiches
        if self.is_android:
            self.android_scroll_into_view('new UiSelector().description("Tap to add product to cart")')

    def quantity(self) -> int:
        self._reveal_cart_controls()
        return int(self.text_of(self.QUANTITY))

    def decrease(self) -> None:
        self._reveal_cart_controls()
        self.tap(self.MINUS)

    def try_add_to_cart(self) -> None:
        """Tap brut, sans attendre que le bouton soit actif : pour verifier qu'un bouton
        desactive ne fait rien. (iOS desactive via isUserInteractionEnabled, donc
        l'attribut 'enabled' reste a true : seul le comportement fait foi.)"""
        self._reveal_cart_controls()
        self.find(self.ADD_TO_CART).click()

    def set_quantity(self, target: int) -> None:
        current = self.quantity()
        button = self.PLUS if target > current else self.MINUS
        for _ in range(abs(target - current)):
            self.tap(button)

    def add_to_cart(self, quantity: int = 1) -> None:
        if quantity != 1:
            self.set_quantity(quantity)
        self._reveal_cart_controls()
        self.tap(self.ADD_TO_CART)
