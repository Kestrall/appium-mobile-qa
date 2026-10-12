"""Scanner QR : ecran camera. Analogue direct de l'appel video interphone cote app."""
from __future__ import annotations

from framework.base_page import BasePage
from framework.locator import Locator, acc, android_id


class QrScannerPage(BasePage):
    SCREEN = Locator(android=android_id("qrCodeTV"), ios=acc("QrCodeScanner-screen"), name="ecran QR")
    CAMERA_PREVIEW = Locator(android=android_id("previewView"), ios=acc("QrCodeScanner-screen"), name="preview camera")

    def camera_preview_visible(self, timeout: int = 10) -> bool:
        return self.is_displayed(self.CAMERA_PREVIEW, timeout=timeout)
