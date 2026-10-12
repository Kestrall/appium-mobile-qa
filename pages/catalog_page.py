from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from framework.base_page import BasePage
from framework.locator import Locator, acc, android_id, predicate

PKG = "com.saucelabs.mydemoapp.android"


class CatalogPage(BasePage):
    SCREEN = Locator(
        android=android_id("productRV"),
        ios=acc("Catalog-screen"),
        name="ecran catalogue",
    )
    PRODUCT_TITLES = Locator(
        android=android_id("titleTV"),
        ios=predicate('name == "Product Name"'),
        name="titres produits",
    )

    def wait_loaded(self, timeout: int = 30) -> "CatalogPage":
        # timeout large : premier lancement = splash + install
        self.find_visible(self.SCREEN, timeout=timeout)
        return self

    def is_loaded(self, timeout: int = 5) -> bool:
        return self.is_displayed(self.SCREEN, timeout=timeout)

    def visible_product_names(self) -> list[str]:
        return [
            e.text if self.is_android else e.get_attribute("label")
            for e in self.find_all(self.PRODUCT_TITLES)
        ]

    def open_product(self, name_prefix: str) -> None:
        """Ouvre un produit par le debut de son nom.

        Les libelles different selon l'OS ("Sauce Labs Backpack" vs
        "Sauce Labs Backpack - Black") : on matche donc sur le prefixe.
        """
        title = self.scroll_to_text(name_prefix, starts_with=True)
        if self.is_ios:
            title.click()
            return
        # Android : seule l'image de la carte produit est cliquable, pas le titre
        image = self.driver.find_element(
            AppiumBy.XPATH,
            f'//*[@resource-id="{PKG}:id/titleTV" and starts-with(@text, "{name_prefix}")]'
            f'/preceding-sibling::*[@resource-id="{PKG}:id/productIV"][1]',
        )
        image.click()
