#!/usr/bin/env bash
# Lance Appium puis la suite sur l'emulateur demarre par android-emulator-runner.
set -uo pipefail

appium --allow-insecure=uiautomator2:adb_shell --log appium.log &
APPIUM_PID=$!
trap 'kill $APPIUM_PID 2>/dev/null' EXIT

for _ in $(seq 1 30); do
  curl -sf http://127.0.0.1:4723/status >/dev/null && break
  sleep 1
done

adb shell settings put global window_animation_scale 0
DEVICE_PROFILE=android_ci pytest -m "${SUITE:-smoke}" --reruns 1
