"""Cycle de vie de l'app et interactions systeme (permissions, arriere-plan)."""
from __future__ import annotations

import time
from enum import IntEnum

from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException


# Popups systeme / constructeur qui passent devant l'app sans lien avec le test.
# (package, resource-id du bouton qui refuse sans effet de bord)
# Ajouter ici chaque nouvelle interruption rencontree sur le parc de test.
SYSTEM_INTERRUPTIONS = [
    # Huawei EMUI : trousseau d'acces (autofill) apres un login -> "NE JAMAIS ENREGISTRER"
    ("com.huawei.securitymgr", "android:id/button2"),
    # Autofill Android standard (Google) : "Non merci"
    ("android", "android:id/autofill_save_no"),
]


def dismiss_system_interruptions(driver: WebDriver) -> list[str]:
    """Ferme les popups systeme connues. Renvoie les packages fermes (pour le rapport)."""
    if driver.capabilities["platformName"].lower() != "android":
        return []
    dismissed = []
    for package, button_id in SYSTEM_INTERRUPTIONS:
        xpath = f'//*[@package="{package}" and @resource-id="{button_id}"]'
        for button in driver.find_elements(AppiumBy.XPATH, xpath):
            button.click()
            dismissed.append(package)
    return dismissed


class AppState(IntEnum):
    NOT_INSTALLED = 0
    NOT_RUNNING = 1
    RUNNING_BACKGROUND_SUSPENDED = 2
    RUNNING_BACKGROUND = 3
    RUNNING_FOREGROUND = 4


class AppController:
    def __init__(self, driver: WebDriver, app_id: str):
        self.driver = driver
        self.app_id = app_id
        self.platform = driver.capabilities["platformName"].lower()

    def state(self) -> AppState:
        return AppState(self.driver.query_app_state(self.app_id))

    def wait_for_state(self, expected: AppState, timeout: float = 10) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.state() == expected:
                return True
            time.sleep(0.5)
        return False

    def restart(self) -> None:
        dismiss_system_interruptions(self.driver)
        self.driver.terminate_app(self.app_id)
        self.driver.activate_app(self.app_id)

    def simulate_process_death(self) -> None:
        """L'app passe en arriere-plan puis l'OS tue son process (memoire, batterie).

        Cas tres frequent sur les surcouches agressives (Huawei, Xiaomi, Samsung) :
        au retour, Android recree l'activite a partir de l'etat sauvegarde.
        Necessite Appium lance avec --allow-insecure=uiautomator2:adb_shell.
        """
        if self.platform != "android":
            raise NotImplementedError("Mort de process simulee : Android uniquement")
        self.driver.press_keycode(3)  # HOME
        time.sleep(1)
        self.driver.execute_script("mobile: shell", {"command": "am", "args": ["kill", self.app_id]})
        time.sleep(1)
        self.driver.activate_app(self.app_id)  # comme un tap sur l'icone : restauration de la tache

    def send_to_background(self, seconds: int) -> None:
        """Simule une interruption (appel entrant, notif, retour accueil)."""
        self.driver.background_app(seconds)

    def reset_camera_permission(self) -> None:
        """Remet la permission camera a 'jamais demandee' pour rejouer la popup systeme.

        Revoquer une permission tue le process : on relance donc l'app derriere.
        """
        try:
            if self.platform == "android":
                self.driver.execute_script("mobile: changePermissions", {
                    "permissions": ["android.permission.CAMERA"],
                    "appPackage": self.app_id,
                    "action": "revoke",
                })
            else:
                # XCUIApplication.resetAuthorizationStatus : simulateur et device reel
                self.driver.execute_script("mobile: resetPermission", {"service": "camera"})
        finally:
            self.restart()

    # --- popups de permission ------------------------------------------

    def answer_permission(self, allow: bool, timeout: float = 8) -> bool:
        """Repond a la popup systeme. Renvoie False si aucune popup n'est apparue."""
        if self.platform == "ios":
            return self._answer_ios_alert(allow, timeout)
        return self._answer_android_permission(allow, timeout)

    def _answer_android_permission(self, allow: bool, timeout: float) -> bool:
        # Les ids varient selon la version d'Android / la surcouche constructeur
        allow_ids = [
            "com.android.permissioncontroller:id/permission_allow_foreground_only_button",
            "com.android.permissioncontroller:id/permission_allow_one_time_button",
            "com.android.permissioncontroller:id/permission_allow_button",
            "com.android.packageinstaller:id/permission_allow_button",
        ]
        deny_ids = [
            "com.android.permissioncontroller:id/permission_deny_button",
            "com.android.permissioncontroller:id/permission_deny_and_dont_ask_again_button",
            "com.android.packageinstaller:id/permission_deny_button",
        ]
        candidates = allow_ids if allow else deny_ids
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for res_id in candidates:
                buttons = self.driver.find_elements(AppiumBy.ID, res_id)
                if buttons:
                    buttons[0].click()
                    return True
            time.sleep(0.5)
        return False

    def _answer_ios_alert(self, allow: bool, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                buttons = self.driver.execute_script("mobile: alert", {"action": "getButtons"})
            except WebDriverException:
                time.sleep(0.5)
                continue
            # Libelles possibles FR / EN selon la langue du telephone
            wanted = ("OK", "Allow", "Autoriser") if allow else ("Don’t Allow", "Don't Allow", "Ne pas autoriser", "Refuser")
            label = next((b for b in buttons if b in wanted), None)
            self.driver.execute_script(
                "mobile: alert",
                {"action": "accept" if allow else "dismiss", **({"buttonLabel": label} if label else {})},
            )
            return True
        return False
