#!/usr/bin/env python3
"""Verifie l'environnement avant une campagne : serveur Appium, drivers, devices, binaires.

Usage : python tools/doctor.py [--device android_real]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from framework.config import load_config  # noqa: E402

OK, KO, WARN = "\033[32m[OK]\033[0m", "\033[31m[KO]\033[0m", "\033[33m[!!]\033[0m"


def run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def check_appium(url: str) -> bool:
    try:
        status = requests.get(f"{url}/status", timeout=3).json()
        version = status["value"]["build"]["version"]
        print(f"{OK} Serveur Appium {version} sur {url}")
        return True
    except Exception:
        print(f"{KO} Appium injoignable sur {url} -> lancer : appium")
        return False


def check_drivers(platform: str) -> bool:
    wanted = "uiautomator2" if platform == "android" else "xcuitest"
    listing = run(["appium", "driver", "list", "--installed"]) + run(
        ["appium", "driver", "list", "--installed", "--json"])
    if wanted in listing:
        print(f"{OK} Driver Appium '{wanted}' installe")
        return True
    print(f"{KO} Driver '{wanted}' absent -> appium driver install {wanted}")
    return False


def check_android(udid: str | None) -> bool:
    if not shutil.which("adb"):
        print(f"{KO} adb introuvable (Android platform-tools + ANDROID_HOME)")
        return False
    lines = [l for l in run(["adb", "devices"]).splitlines()[1:] if l.strip()]
    ready = [l.split()[0] for l in lines if l.endswith("device")]
    unauthorized = [l.split()[0] for l in lines if "unauthorized" in l]
    for serial in unauthorized:
        print(f"{KO} {serial} non autorise : accepter la popup 'Debogage USB' sur le telephone")
    if not ready:
        print(f"{KO} Aucun device Android pret")
        return False
    for serial in ready:
        model = run(["adb", "-s", serial, "shell", "getprop", "ro.product.model"])
        version = run(["adb", "-s", serial, "shell", "getprop", "ro.build.version.release"])
        print(f"{OK} Android {serial} : {model} (Android {version})")
    if udid and udid not in ready:
        print(f"{KO} ANDROID_UDID={udid} n'est pas dans la liste")
        return False
    return True


def check_ios(udid: str | None) -> bool:
    if sys.platform != "darwin":
        print(f"{KO} iOS necessite macOS + Xcode (WebDriverAgent est compile par xcodebuild)")
        return False
    devices = run(["xcrun", "xctrace", "list", "devices"])
    print(f"{OK} Devices iOS visibles :\n    " + "\n    ".join(devices.splitlines()[:8]))
    if udid and udid not in devices:
        print(f"{KO} IOS_UDID={udid} introuvable (cable, 'Faire confiance', mode developpeur active ?)")
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    cfg = load_config(args.device)
    print(f"Profil : {cfg.profile} ({cfg.platform})\n")

    results = [check_appium(cfg.appium_url), check_drivers(cfg.platform)]
    if cfg.is_android:
        results.append(check_android(cfg.capabilities.get("appium:udid")))
    else:
        results.append(check_ios(cfg.capabilities.get("appium:udid")))

    app_path = cfg.capabilities.get("appium:app")
    if app_path:
        if Path(app_path).exists():
            print(f"{OK} Binaire present : {app_path}")
        else:
            print(f"{KO} Binaire absent : {app_path} -> ./tools/fetch_apps.sh")
            results.append(False)

    print()
    if all(results):
        print(f"{OK} Environnement pret.")
        return 0
    print(f"{KO} Corriger les points ci-dessus avant de lancer la campagne.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
