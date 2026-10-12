#!/usr/bin/env bash
# Telecharge les binaires de l'app sous test (Sauce Labs My Demo App, natives Android + iOS).
set -euo pipefail

DEST="$(cd "$(dirname "$0")/.." && pwd)/apps"
ANDROID_VERSION="2.3.0"
ANDROID_APK="mda-2.3.0-27.apk"
IOS_VERSION="2.3.0"

mkdir -p "$DEST"

echo ">> APK Android $ANDROID_VERSION"
curl -fL -o "$DEST/$ANDROID_APK" \
  "https://github.com/saucelabs/my-demo-app-android/releases/download/$ANDROID_VERSION/$ANDROID_APK"

echo ">> Build simulateur iOS $IOS_VERSION (pour Mac / CI macOS)"
curl -fL -o "$DEST/SauceLabs-Demo-App.Simulator.zip" \
  "https://github.com/saucelabs/my-demo-app-ios/releases/download/$IOS_VERSION/SauceLabs-Demo-App.Simulator.zip"

echo
echo "iPhone physique : l'IPA publiee est signee par Sauce Labs, elle ne s'installe pas"
echo "telle quelle. Compiler depuis les sources avec ton Team ID : voir docs/SETUP_IOS.md"
