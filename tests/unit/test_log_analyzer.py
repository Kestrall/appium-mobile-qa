"""Tests unitaires de l'analyseur de traces (sans device, tournent en CI Linux)."""
from framework.device_logs import analyze

APP = "com.saucelabs.mydemoapp.android"

LOGCAT_CRASH = [
    "10-12 09:14:02.101  4321  4321 I ActivityTaskManager: Displayed com.saucelabs.mydemoapp.android/.view.activities.MainActivity",
    "10-12 09:14:05.882  4321  4321 E AndroidRuntime: FATAL EXCEPTION: main",
    f"10-12 09:14:05.882  4321  4321 E AndroidRuntime: Process: {APP}, PID: 4321",
    "10-12 09:14:05.882  4321  4321 E AndroidRuntime: java.lang.RuntimeException: You clicked on the wrong button!",
]


def test_detects_java_crash_of_app_under_test():
    report = analyze(LOGCAT_CRASH, "android", APP)
    assert report.has_crash
    assert len(report.findings["crash"]) == 2


def test_ignores_crash_of_another_app():
    lines = ["E AndroidRuntime: Process: com.other.app, PID: 99"]
    assert not analyze(lines, "android", APP).has_crash


def test_detects_anr():
    report = analyze([f"E ActivityManager: ANR in {APP} (MainActivity)"], "android", APP)
    assert "anr" in report.findings


def test_clean_log_has_no_findings():
    report = analyze(LOGCAT_CRASH[:1], "android", APP)
    assert not report.findings
    assert report.summary() == "Aucune signature d'erreur detectee."


def test_ios_fatal_error():
    lines = ["My Demo App[512] <Notice>: Fatal error: Unexpectedly found nil while unwrapping an Optional value"]
    assert analyze(lines, "ios").has_crash
