"""Collecte et analyse des traces device (logcat Android / syslog iOS).

Objectif : qualifier une anomalie sans rejouer le test. A chaque test on
recupere les logs produits pendant son execution, on les attache au rapport
et on cherche les signatures de crash / ANR / exception non geree.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from appium.webdriver.webdriver import WebDriver

# Signatures recherchees. Volontairement simples et lisibles : c'est la base
# a enrichir avec les tags propres a l'app (ex. tags BLE / MQTT de l'app client).
ANDROID_SIGNATURES = {
    "crash": re.compile(r"FATAL EXCEPTION|AndroidRuntime: Process: (?P<pkg>[\w.]+)"),
    "anr": re.compile(r"ANR in (?P<pkg>[\w.]+)"),
    "native_crash": re.compile(r"Fatal signal \d+ \(SIG\w+\)"),
    "strict_mode": re.compile(r"StrictMode policy violation"),
}

IOS_SIGNATURES = {
    "crash": re.compile(r"Fatal error|EXC_BAD_ACCESS|EXC_CRASH|Terminating app due to uncaught exception"),
    "watchdog": re.compile(r"0x8badf00d|scene-update watchdog"),
}


@dataclass
class LogReport:
    platform: str
    lines: list[str] = field(default_factory=list)
    findings: dict[str, list[str]] = field(default_factory=dict)

    @property
    def has_crash(self) -> bool:
        return any(k in self.findings for k in ("crash", "anr", "native_crash", "watchdog"))

    def as_text(self) -> str:
        return "\n".join(self.lines)

    def summary(self) -> str:
        if not self.findings:
            return "Aucune signature d'erreur detectee."
        parts = []
        for kind, hits in self.findings.items():
            parts.append(f"[{kind}] {len(hits)} occurrence(s)\n  " + "\n  ".join(hits[:5]))
        return "\n".join(parts)


class DeviceLogCollector:
    def __init__(self, driver: WebDriver, app_id: str):
        self.driver = driver
        self.app_id = app_id
        self.platform = driver.capabilities["platformName"].lower()
        self.log_type = "logcat" if self.platform == "android" else "syslog"

    def flush(self) -> None:
        """Vide le buffer : les logs suivants concerneront uniquement le test courant."""
        try:
            self.driver.get_log(self.log_type)
        except Exception:
            pass

    def collect(self) -> LogReport:
        try:
            entries = self.driver.get_log(self.log_type)
        except Exception as exc:  # syslog parfois indisponible selon la config iOS
            return LogReport(self.platform, [f"<logs indisponibles : {exc}>"])
        lines = [e.get("message", "") for e in entries]
        return analyze(lines, self.platform, self.app_id)


    def collect_until(self, predicate, timeout: float = 8) -> LogReport:
        """Accumule les logs jusqu'a ce que predicate(report) soit vrai (ou timeout)."""
        import time

        lines: list[str] = []
        deadline = time.monotonic() + timeout
        while True:
            lines.extend(self.collect().lines)
            report = analyze(lines, self.platform, self.app_id)
            if predicate(report) or time.monotonic() > deadline:
                return report
            time.sleep(0.5)


def analyze(lines: list[str], platform: str, app_id: str | None = None) -> LogReport:
    """Analyse pure (testable sans device, cf. tests/unit)."""
    signatures = ANDROID_SIGNATURES if platform == "android" else IOS_SIGNATURES
    report = LogReport(platform, lines)
    for line in lines:
        for kind, pattern in signatures.items():
            match = pattern.search(line)
            if not match:
                continue
            pkg = match.groupdict().get("pkg")
            if app_id and pkg and pkg != app_id:
                continue  # crash d'une autre app : bruit
            report.findings.setdefault(kind, []).append(line.strip())
    return report
