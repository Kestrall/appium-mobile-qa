"""Preuves attachees au rapport Allure en cas d'echec : capture, arbre UI, video, logs."""
from __future__ import annotations

import base64

import allure
from appium.webdriver.webdriver import WebDriver


def start_video(driver: WebDriver) -> None:
    try:
        driver.start_recording_screen(timeLimit="300", bitRate="2000000", forceRestart=True)
    except Exception:
        pass  # pas bloquant : certaines configs (iOS reel sans ffmpeg) ne le supportent pas


def stop_video(driver: WebDriver, attach: bool) -> None:
    try:
        payload = driver.stop_recording_screen()
    except Exception:
        return
    if attach and payload:
        allure.attach(base64.b64decode(payload), "video", allure.attachment_type.MP4)


def attach_failure_evidence(driver: WebDriver) -> None:
    try:
        allure.attach(driver.get_screenshot_as_png(), "screenshot", allure.attachment_type.PNG)
        allure.attach(driver.page_source, "ui-tree", allure.attachment_type.XML)
    except Exception:
        pass  # session morte (crash app / WDA) : on garde au moins les logs


def attach_logs(name: str, text: str) -> None:
    allure.attach(text or "<vide>", name, allure.attachment_type.TEXT)
