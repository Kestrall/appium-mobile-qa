# Setup iOS (iPhone physique)

> **Prerequis non negociable : un Mac avec Xcode.** Appium pilote iOS via
> WebDriverAgent (WDA), une app de test XCTest compilee et signee par `xcodebuild`.
> Depuis Linux, les options sont : un Mac (meme un Mac mini d'occasion), un runner
> macOS en CI (simulateur, cf. workflow), ou un device farm (BrowserStack, Sauce Labs).

## 1. Outils (sur le Mac)

```bash
xcode-select --install          # + Xcode complet depuis l'App Store
npm install -g appium
appium driver install xcuitest
appium driver doctor xcuitest
brew install ffmpeg             # enregistrement video des tests (optionnel)
```

## 2. iPhone

1. Brancher l'iPhone, **"Faire confiance a cet ordinateur"**.
2. iOS 16+ : Reglages > Confidentialite et securite > **Mode developpeur** > activer, redemarrer.
3. Reglages > Developpeur > **Enable UI Automation** : activer.
4. Recuperer l'UDID : `xcrun xctrace list devices` (ou `idevice_id -l`).

## 3. Compiler l'app sous test avec ton compte Apple

L'IPA publiee par Sauce Labs est signee avec leur certificat : elle ne s'installe pas
sur ton iPhone. On la recompile (compte Apple gratuit suffisant, profils valables 7 jours) :

```bash
git clone https://github.com/saucelabs/my-demo-app-ios && cd my-demo-app-ios
open "My Demo App.xcworkspace"
```
Dans Xcode : cible **My Demo App** > Signing & Capabilities > Team = ton compte,
Bundle Identifier = un identifiant unique, ex. `fr.kestrall.mydemoapp`. Selectionner
l'iPhone, **Run**. Au premier lancement : Reglages > General > VPN et gestion de
l'appareil > faire confiance au developpeur.

Puis dans `.env` :
```
IOS_UDID=00008110-XXXXXXXXXXXXXXXX
IOS_BUNDLE_ID=fr.kestrall.mydemoapp
XCODE_ORG_ID=ABCDE12345           # Team ID (Xcode > Settings > Accounts)
WDA_BUNDLE_ID=fr.kestrall.WebDriverAgentRunner
```

## 4. Signer WebDriverAgent

Appium compile WDA automatiquement avec `xcodeOrgId` / `updatedWDABundleId`.
Si ca coince (cas frequent la premiere fois), le faire a la main une fois :
```bash
open ~/.appium/node_modules/appium-xcuitest-driver/node_modules/appium-webdriveragent/WebDriverAgent.xcodeproj
```
Cible **WebDriverAgentRunner** > Signing > ta Team + bundle id unique > Product > Test
sur l'iPhone. Accepter le certificat sur le telephone. Ensuite Appium le reutilise.

## 5. Lancer

```bash
appium
python tools/doctor.py --device ios_real
pytest -m smoke --device ios_real
```

## Pieges connus

| Symptome | Cause / remede |
|---|---|
| `xcodebuild failed with code 65` | Signature WDA : refaire l'etape 4, verifier la Team |
| WDA se lance puis l'iPhone se verrouille | Reglages > Luminosite > Verrouillage auto = Jamais |
| `Could not find a device` | Mode developpeur inactif ou "Faire confiance" non accepte |
| Popups systeme non detectees | `autoAcceptAlerts` a false volontairement : on les teste (MQA-30) |
| Tests lents au 1er run | Normal : compilation WDA (~2 min), les runs suivants reutilisent le build |
