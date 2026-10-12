# Strategie de test : app mobile native qui pilote des equipements connectes

Ce document est la demarche que je deroulerais en arrivant sur une app native
iOS / Android qui pilote des equipements (interphone video, centrale d'acces,
badges), avec une automatisation **quasi inexistante a construire**. Le repo
en est la demonstration sur une app publique.

## 1. Choix de l'outil

| Critere | Appium | Espresso / XCUITest | Maestro / Detox |
|---|---|---|---|
| Un seul code pour iOS + Android | oui | non (2 codebases) | oui / RN only |
| Langage de l'equipe QA (Python) | oui | Kotlin / Swift | YAML / JS |
| Teste le binaire de prod, sans toucher au code app | oui | non (instrumentation) | oui / non |
| Acces systeme (permissions, arriere-plan, logs device) | oui | partiel | partiel |
| Vitesse / stabilite | moyenne | excellente | bonne |

**Choix : Appium 3 + Python + pytest.** Raisons : une equipe QA, deux OS, un
langage deja utilise pour les scripts d'outillage (MQTT, SSH, SQL) : les tests
mobiles et les tests equipements partagent le meme socle et le meme rapport.
Espresso / XCUITest restent le bon choix pour les tests ecrits *par les devs*
(composants, ecrans isoles) : complementaires, pas concurrents.

## 2. Pyramide et perimetre de l'automatisation

```
          /  E2E Appium  \        parcours critiques, sur vrais telephones
         /  API / MQTT    \       logique metier, cloud, etats equipements (Python)
        / unit (devs)       \     Kotlin / Swift, dans le repo de l'app
```

On n'automatise **pas tout en E2E**. Regles :
- E2E Appium = parcours critiques + ce qui depend vraiment du telephone
  (permissions, camera, notifications, arriere-plan, BLE / NFC).
- Le reste (droits d'acces, regles d'horaires, liste des residents) se verifie
  plus vite et plus fiablement au niveau API.
- Chaque bug corrige en prod donne un test de non-regression, au bon niveau.

## 3. Parcours critiques (ordre de priorite)

Classement risque = impact x probabilite. Pour une app de controle d'acces, le
pire scenario n'est pas un bug d'affichage : c'est **une porte qui ne s'ouvre pas
pour un resident, ou qui s'ouvre pour quelqu'un qui n'a plus les droits**.

| # | Parcours (app client) | Equivalent dans ce repo | Pourquoi critique |
|---|---|---|---|
| 1 | Connexion / session / compte desactive | `test_login.py` (MQA-10..13) | un ex-locataire ne doit plus entrer |
| 2 | Appel interphone video entrant, app en arriere-plan ou tuee | `test_cart_survives_background` (MQA-32) | coeur du produit, contraintes OS fortes |
| 3 | Permissions camera / micro / notifications / BLE refusees | MQA-30, MQA-31 | refus = fonctionnalite morte, pas un crash |
| 4 | Ouverture de porte a distance (commande -> equipement -> retour etat) | a construire : Appium + verif MQTT | boucle app / cloud / materiel |
| 5 | Gestion des badges (ajout, perte, desactivation) | `test_cart.py` (etat partage, compteurs) | coherence des donnees entre ecrans |
| 6 | Crash / ANR silencieux | MQA-33 + garde-fou logcat sur **chaque** test | qualifier sans rejouer |

## 4. Test bout en bout app + equipement (cible)

Le framework est pense pour brancher la verification cote equipement :

```python
def test_remote_door_opening(app_page, mqtt):
    with mqtt.expect("site/42/door/1/cmd", timeout=5) as cmd:
        app_page.open_door("Hall A")          # action Appium
    assert cmd.payload["action"] == "unlock"  # la commande est bien partie
    mqtt.publish("site/42/door/1/state", {"state": "open"})  # simulateur d'equipement
    assert app_page.door_status("Hall A") == "Ouverte"        # l'app reflete l'etat
```

- **Simulateur d'equipement** (Python, MQTT) pour les cas limites impossibles a
  provoquer sur du vrai materiel : timeout, reponse en double, equipement hors ligne.
- **Banc avec vrai materiel** pour la campagne de validation de release.
- Correlation des traces : horodatage commun entre logcat / syslog, logs broker
  MQTT, logs equipement (SSH) pour qualifier "qui a perdu le message".

## 5. Matrice de devices

Pas besoin de 30 telephones. On couvre les axes de risque :

| Axe | Android | iOS |
|---|---|---|
| Version OS | min supportee, N-1, N | N-1, N |
| Surcouche constructeur (gestion batterie agressive) | Samsung, Xiaomi | - |
| Taille ecran | petit + grand | SE + Pro Max |
| Usage reel du parc client (bailleurs sociaux) | Android d'entree de gamme | iPhone anciens |

Le dernier point compte : la population des logements sociaux a beaucoup de
telephones Android d'entree de gamme, un peu anciens. **C'est la que les
notifications d'appel interphone sont tuees par l'economiseur de batterie.**

## 6. Integration continue

1. PR : tests unitaires + smoke sur emulateur Android (rapide, bloquant).
2. Nuit : regression complete Android emulateur + iOS simulateur.
3. Release candidate : regression sur le banc de **vrais telephones** + equipements,
   resultat pousse dans Xray (`tools/xray_import.py`) rattache au Test Plan de la version.

## 7. Lutter contre la flakiness

- Attentes explicites uniquement (`implicit_wait = 0`), jamais de `sleep`.
- Locators par accessibility id ; demander aux devs d'en ajouter (c'est aussi un
  gain d'accessibilite pour les utilisateurs malvoyants).
- Etat propre a chaque test (app tuee / relancee), donnees de test dediees.
- `--reruns 1` en CI **uniquement** pour absorber l'infra ; un test qui ne passe
  qu'au rerun est trace et traite comme une anomalie de test.
- Un test instable est mis en quarantaine (marqueur) sous 24 h, pas laisse rouge.
