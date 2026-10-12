# Setup Android (telephone physique, Linux / macOS / Windows)

## 1. Outils

```bash
# Node 20.19+ (nvm conseille) puis Appium 3 et son driver Android
npm install -g appium
appium driver install uiautomator2
appium driver doctor uiautomator2      # diagnostic officiel du driver

# SDK Android : platform-tools suffit pour un vrai telephone
# (via Android Studio ou les cmdline-tools)
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$ANDROID_HOME/platform-tools:$PATH
# JDK 17
```

Debian : `sudo apt install adb` fonctionne aussi pour `adb`, mais UiAutomator2 veut
`ANDROID_HOME` pointant sur un SDK avec `platform-tools` et `build-tools`.

## 2. Telephone

1. Parametres > A propos > appuyer 7 fois sur "Numero de build" => Options developpeur.
2. Options developpeur : activer **Debogage USB**.
   - Xiaomi / Redmi : activer aussi **Debogage USB (parametres de securite)** et **Installer via USB**.
   - Oppo / Realme / OnePlus : desactiver **Optimisation des autorisations**.
3. Brancher en USB, accepter la popup **"Autoriser le debogage USB"** (cocher "toujours").
4. `adb devices` doit afficher `XXXXXXXX  device` (et non `unauthorized`).
5. Recommande : Options developpeur > echelles d'animation a 0 (moins de flakiness).

Linux : si `adb devices` affiche `no permissions`, ajouter une regle udev
(`/etc/udev/rules.d/51-android.rules`) ou installer le paquet `android-sdk-platform-tools-common`.

## 3. Lancer

```bash
./tools/fetch_apps.sh
cp .env.example .env            # renseigner ANDROID_UDID (sortie de adb devices)
appium --allow-insecure=uiautomator2:adb_shell   # terminal 1
python tools/doctor.py          # terminal 2 : tout doit etre [OK]
pytest -m smoke --device android_real
pytest --device android_real --video          # campagne complete, videos des echecs
allure serve reports/allure-results
```

## 4. Wi-Fi (sans cable, Android 11+)

Options developpeur > **Debogage sans fil** > Associer avec un code :
```bash
adb pair IP:PORT_APPAIRAGE      # saisir le code
adb connect IP:PORT
```
Puis `ANDROID_UDID=IP:PORT`. Pratique pour tester l'app pendant qu'on manipule un equipement.

## 5. Inspecter l'UI

[Appium Inspector](https://github.com/appium/appium-inspector) avec les capabilities du profil
`android_real` (copier depuis `config/devices.yaml`). En ligne de commande :
`adb shell uiautomator dump && adb pull /sdcard/window_dump.xml`.
