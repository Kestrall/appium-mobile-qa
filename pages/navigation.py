"""Navigation globale : header Android (menu burger + panier) / tab bar iOS."""
from __future__ import annotations

from framework.base_page import BasePage
from framework.locator import Locator, acc, android_id, ui_selector


class Navigation(BasePage):
    MENU = Locator(android=acc("View menu"), ios=acc("More-tab-item"), name="menu")
    CART = Locator(android=acc("View cart"), ios=acc("Cart-tab-item"), name="panier")
    CATALOG_TAB = Locator(ios=acc("Catalog-tab-item"), name="onglet catalogue")
    CART_BADGE = Locator(android=android_id("cartTV"), name="badge panier")

    # Entrees du menu. Android : UiSelector sur la RecyclerView ; iOS : identifiants dedies.
    _MENU_ITEMS = {
        "catalog": ('new UiSelector().text("Catalog")', None),
        "qr": ('new UiSelector().text("QR Code Scanner")', "QrCodeScanner-menu-item"),
        "crash": ('new UiSelector().text("Crash app (debug)")', "CrashTheApp-menu-item"),
        "reset": ('new UiSelector().text("Reset App State")', "ResetAppState-menu-item"),
        "login": ('new UiSelector().description("Login Menu Item")', "LogOut-menu-item"),
        "logout": ('new UiSelector().description("Logout Menu Item")', "LogOut-menu-item"),
    }

    def open_menu(self) -> None:
        self.tap(self.MENU)

    def open_menu_item(self, key: str) -> None:
        android_selector, ios_id = self._MENU_ITEMS[key]
        self.open_menu()
        if self.is_android:
            # le menu Android est une liste scrollable : on amene l'item a l'ecran
            self.android_scroll_into_view(android_selector)
        item = Locator(
            android=ui_selector(android_selector),
            ios=acc(ios_id) if ios_id else None,
            name=f"menu/{key}",
        )
        self.tap(item)

    def open_cart(self) -> None:
        self.tap(self.CART)

    def open_catalog(self) -> None:
        if self.is_ios:
            self.tap(self.CATALOG_TAB)
        else:
            self.open_menu_item("catalog")

    def cart_badge_count(self) -> int:
        """Compteur du panier dans le header (Android). 0 si le badge est masque."""
        if self.is_ios:
            raise NotImplementedError("Badge iOS non expose : utiliser CartPage.item_count()")
        if not self.is_displayed(self.CART_BADGE, timeout=2):
            return 0
        return int(self.text_of(self.CART_BADGE) or 0)
