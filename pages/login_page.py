from __future__ import annotations

import time

from framework.app import dismiss_system_interruptions
from framework.base_page import BasePage
from framework.locator import Locator, android_id, class_chain, predicate


class LoginPage(BasePage):
    USERNAME = Locator(
        android=android_id("nameET"),
        ios=class_chain("**/XCUIElementTypeTextField[1]"),
        name="champ identifiant",
    )
    PASSWORD = Locator(
        android=android_id("passwordET"),
        ios=class_chain("**/XCUIElementTypeSecureTextField[1]"),
        name="champ mot de passe",
    )
    SUBMIT = Locator(
        android=android_id("loginBtn"),
        ios=predicate('type == "XCUIElementTypeButton" AND label == "Login"'),
        name="bouton login",
    )
    # Android : erreurs inline sous les champs ; iOS : UIAlertController "Validation Error!"
    USERNAME_ERROR = Locator(android=android_id("nameErrorTV"), name="erreur identifiant")
    PASSWORD_ERROR = Locator(android=android_id("passwordErrorTV"), name="erreur mot de passe")
    IOS_ALERT_MESSAGE = Locator(
        ios=class_chain("**/XCUIElementTypeAlert/**/XCUIElementTypeStaticText[2]"),
        name="message alerte",
    )

    def wait_loaded(self) -> "LoginPage":
        self.find_visible(self.USERNAME)
        return self

    def login(self, username: str, password: str) -> None:
        if username:
            self.type_text(self.USERNAME, username)
            # petits ecrans : le clavier masque le champ suivant (constate sur Huawei P20 Lite)
            self.hide_keyboard()
        if password:
            self.type_text(self.PASSWORD, password)
        self.hide_keyboard()
        self.tap(self.SUBMIT)
        if username and password:
            # l'autofill constructeur (ex. trousseau Huawei) propose d'enregistrer les identifiants
            time.sleep(1)  # la popup arrive apres la transition d'ecran, pas d'element de l'app a attendre
            dismiss_system_interruptions(self.driver)

    def error_message(self) -> str:
        """Message d'erreur affiche, quelle que soit sa forme selon l'OS."""
        if self.is_ios:
            return self.text_of(self.IOS_ALERT_MESSAGE)
        for locator in (self.USERNAME_ERROR, self.PASSWORD_ERROR):
            if self.is_displayed(locator, timeout=2):
                return self.text_of(locator)
        return ""

    def dismiss_error(self) -> None:
        if self.is_ios:
            self.driver.execute_script("mobile: alert", {"action": "accept"})
