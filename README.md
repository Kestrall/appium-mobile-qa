# appium-mobile-qa

Framework d'automatisation de tests **mobiles natifs iOS + Android** avec Appium 3,
Python et pytest. Un seul code de test pour les deux OS, joue sur **vrais telephones**,
emulateur / simulateur en CI, avec qualification automatique des anomalies par les
traces device (logcat / syslog).

App sous test : [Sauce Labs My Demo App](https://github.com/saucelabs/my-demo-app-android),
une app open source **native** (Kotlin / Swift, pas de web responsive) disponible sur les deux OS.

> La demarche (choix d'outil, parcours critiques, matrice de devices, transposition a
> une app qui pilote des equipements connectes) est dans [docs/STRATEGY.md](docs/STRATEGY.md).

## Ce que le projet montre

| Besoin | Implementation |
|---|---|
| Un test, deux OS | `Locator(android=..., ios=...)` resolu a l'execution (`framework/locator.py`) |
| Tests stables | attentes explicites seulement, etat d'app reinitialise a chaque test |
| Popups systeme (camera, permissions) | `framework/app.py` : reponse Android / iOS, FR / EN, reset de permission |
| Interruptions (appel, arriere-plan) | `MQA-32`, `background_app` + verification d'etat |
| Analyse des traces | logcat / syslog collectes **a chaque test**, signatures crash / ANR detectees, un crash fait echouer le test meme si l'UI semblait OK |
| Preuves d'anomalie | capture, arbre UI, logs et video attaches au rapport Allure en cas d'echec |
| Ecarts de parite iOS / Android | 2 anomalies reelles trouvees et documentees ([docs/DEFECTS.md](docs/DEFECTS.md)) |
| Jira / Xray | `@pytest.mark.tc("MQA-12")` => propriete JUnit `test_key` => `tools/xray_import.py` |
| CI | GitHub Actions : unitaires, Android sur emulateur, iOS sur simulateur macOS |

## Structure

```
config/devices.yaml       profils : android_real, android_ci, android_emulator, ios_real, ios_simulator
framework/
  config.py               chargement profil + .env
  driver_factory.py       UiAutomator2Options / XCUITestOptions
  locator.py              locators multi-plateformes
  base_page.py            attentes, gestes, scroll natif par OS
  app.py                  cycle de vie, etat de l'app, permissions
  device_logs.py          collecte + analyse logcat / syslog
  evidence.py             captures, arbre UI, video -> Allure
pages/                    Page Objects (catalogue, produit, panier, login, scanner QR...)
tests/                    campagnes e2e + tests unitaires de l'analyseur de logs
tools/
  doctor.py               verifie Appium, drivers, devices, binaires avant une campagne
  fetch_apps.sh           telecharge l'APK et le build simulateur iOS
  xray_import.py          pousse le resultat JUnit dans une Test Execution Xray
docs/                     strategie, cas de test, anomalies, setup Android / iOS
```

## Demarrage rapide (Android, telephone en USB)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install -g appium && appium driver install uiautomator2
./tools/fetch_apps.sh
cp .env.example .env              # ANDROID_UDID = sortie de `adb devices`

appium --allow-insecure=uiautomator2:adb_shell   # autre terminal (adb_shell : test MQA-34)
python tools/doctor.py
pytest -m smoke --device android_real
pytest --device android_real --video
allure serve reports/allure-results
```

iPhone : necessite un Mac + Xcode, voir [docs/SETUP_IOS.md](docs/SETUP_IOS.md).
Android en detail : [docs/SETUP_ANDROID.md](docs/SETUP_ANDROID.md).

## Selection des tests

```bash
pytest -m smoke                         # parcours critiques (gate de CI)
pytest -m regression                    # campagne complete
pytest -k login --device ios_real       # un domaine, une cible
pytest tests/unit                       # sans device
```

Les tests `android_only`, `ios_only` et `real_device_only` sont ignores
automatiquement quand la cible ne correspond pas.

## Ecrire un test

```python
@pytest.mark.smoke
@pytest.mark.tc("MQA-20")
def test_add_single_product(catalog, product, nav, cart):
    catalog.open_product("Sauce Labs Backpack")
    product.wait_loaded().add_to_cart()
    nav.open_cart()
    assert cart.item_count() == 1
```

Les differences d'implementation (locators, gestes, popups) vivent dans les Page Objects.
Les tests ne distinguent les OS que lorsque le **comportement attendu** differe (ex. MQA-12).
