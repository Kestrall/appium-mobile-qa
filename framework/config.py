"""Chargement des profils d'execution (config/devices.yaml + variables d'environnement)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

_ENV_PATTERN = re.compile(r"\$\{(\w+)\}")

# Valeurs par defaut raisonnables pour les variables optionnelles
_ENV_DEFAULTS = {
    "ANDROID_AVD": "Pixel_8_API_35",
    "IOS_BUNDLE_ID": "com.saucelabs.mydemo.app.ios",
    "IOS_SIM_NAME": "iPhone 16",
    "IOS_SIM_VERSION": "18.5",
    "XCODE_SIGNING_ID": "Apple Development",
}


def _expand(value):
    if not isinstance(value, str):
        return value
    return _ENV_PATTERN.sub(lambda m: os.getenv(m.group(1)) or _ENV_DEFAULTS.get(m.group(1), ""), value)


@dataclass
class RunConfig:
    profile: str
    capabilities: dict
    appium_url: str
    explicit_wait: int
    new_command_timeout: int
    extra: dict = field(default_factory=dict)

    @property
    def platform(self) -> str:
        return self.capabilities["platformName"].lower()

    @property
    def is_android(self) -> bool:
        return self.platform == "android"

    @property
    def is_ios(self) -> bool:
        return self.platform == "ios"

    @property
    def is_real_device(self) -> bool:
        return self.profile.endswith("_real")

    @property
    def app_id(self) -> str:
        caps = self.capabilities
        return caps.get("appium:appPackage") or caps.get("appium:bundleId") or "com.saucelabs.mydemo.app.ios"


def load_config(profile: str | None = None) -> RunConfig:
    profile = profile or os.getenv("DEVICE_PROFILE", "android_real")
    data = yaml.safe_load((ROOT / "config" / "devices.yaml").read_text())
    if profile not in data["profiles"]:
        raise ValueError(f"Profil inconnu '{profile}'. Dispos : {', '.join(data['profiles'])}")

    caps = {}
    for key, value in data["profiles"][profile].items():
        value = _expand(value)
        if value == "":
            continue  # variable non renseignee : on laisse Appium choisir (ex. udid)
        if key == "appium:app" and value.startswith("./"):
            value = str(ROOT / value[2:])
        caps[key] = value

    defaults = data["defaults"]
    caps.setdefault("appium:newCommandTimeout", defaults["new_command_timeout"])

    return RunConfig(
        profile=profile,
        capabilities=caps,
        appium_url=os.getenv("APPIUM_URL", "http://127.0.0.1:4723"),
        explicit_wait=defaults["explicit_wait"],
        new_command_timeout=defaults["new_command_timeout"],
    )
