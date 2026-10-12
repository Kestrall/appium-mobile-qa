# Anomalies relevees

Ecarts trouves en ecrivant la campagne, rediges comme je les remonterais dans Jira.
Elles sont verifiables dans les sources publiques des deux apps.

---

## MQA-BUG-1 : iOS accepte la connexion d'un compte verrouille

| Champ | Valeur |
|---|---|
| Severite | **Majeure** (securite : contournement d'un blocage de compte) |
| Priorite | P1 |
| Plateforme | iOS uniquement, Android conforme |
| Version | My Demo App iOS 2.3.0 |
| Cas de test | MQA-12 |

**Etapes**
1. Lancer l'app, menu "More" > "Login".
2. Toucher `alice@example.com` (le mot de passe se remplit), valider.

**Attendu** : refus avec "Sorry this user has been locked out." (comportement Android).
**Obtenu** : connexion acceptee, redirection vers le catalogue.

**Analyse** : `LoginViewController.LoginButton` (iOS) ne verifie que la presence
des champs ; aucun equivalent de la branche `username.contains("alice@example.com")`
de `LoginFragment.loginWithEmail` (Android). La regle metier est implementee cote
client et dupliquee par plateforme : **recommandation**, porter la decision de
blocage cote serveur pour qu'aucun client ne puisse la contourner.

**Dans la campagne** : `xfail(strict=True)` sur iOS. Quand le bug sera corrige,
le test passera en XPASS, ce qui fait echouer le run : on est force de retirer
le marqueur, on ne garde pas un xfail mort.

---

## MQA-BUG-2 : libelles d'erreur differents entre iOS et Android

| Champ | Valeur |
|---|---|
| Severite | Mineure (coherence / i18n) |
| Plateforme | Android et iOS |
| Cas de test | MQA-11 |

**Constat** : mot de passe vide => Android affiche "Enter Password" (texte force dans
le code alors que le layout declare "Password is required"), iOS affiche "Password is
required" dans une alerte. Forme differente (inline vs popup) acceptable si specifiee,
**libelle different non**.

**Recommandation** : centraliser les libelles (fichier de traduction commun) et
les reference dans la spec ; le test MQA-11 porte un attendu par plateforme en
attendant l'arbitrage Produit.

---

## MQA-BUG-3 : crash a l'ouverture de certains produits du catalogue (Android)

| Champ | Valeur |
|---|---|
| Severite | **Bloquante** (crash) |
| Plateforme | Android, constate sur Huawei P20 Lite (Android 9 / EMUI 9.1) |
| Cas de test | MQA-25 |
| Detection | garde-fou logcat du framework, pendant MQA-23 |

**Etapes** : catalogue > toucher "Sauce Labs Bike Light" (ou tout produit au-dela du 6e, ou le 2e).
**Obtenu** : fermeture de l'app.

```
E AndroidRuntime: FATAL EXCEPTION: main
E AndroidRuntime: java.lang.ArrayIndexOutOfBoundsException: length=6; index=6
E AndroidRuntime:   at ...ProductCatalogFragment.lambda$setAdapter$0(ProductCatalogFragment.java:156)
```

**Analyse** : `setAdapter()` indexe un tableau `meta` de 6 cases par la position du produit,
alors que le catalogue en compte davantage ; la case 1 vaut `null` (NPE sur `intValue()`). Bug volontairement seme par
Sauce Labs pour les demos, mais exactement le type d'erreur (tableau de metadonnees
desynchronise de la liste) qu'on retrouve en vrai.

---

## MQA-BUG-4 : la permission camera est redemandee immediatement apres un refus (Android)

| Champ | Valeur |
|---|---|
| Severite | Majeure (UX, et Google Play penalise ce harcelement de permission) |
| Plateforme | Android 9 |
| Cas de test | MQA-30 |

**Etapes** : menu > QR Code Scanner > "REFUSER".
**Attendu** : retour au catalogue, pas de nouvelle demande.
**Obtenu** : la popup revient aussitot (avec "Ne plus demander") ; il faut refuser deux fois.

**Analyse** : `QRFragment.onResume()` relance `requestPermissions()` si la permission
n'est pas accordee ; or la fermeture de la popup systeme declenche justement `onResume`.
**Recommandation** : tracer le refus, et expliquer dans l'app comment reactiver
(lien vers les parametres). Transposition interphone : refus du micro / de la camera
pendant un appel entrant.

---

## MQA-BUG-5 : crash au retour dans l'app apres que le systeme a tue le process (Android)

| Champ | Valeur |
|---|---|
| Severite | **Bloquante** (crash, reproductible 100 %) |
| Plateforme | Android ; particulierement exposee sur Huawei / Xiaomi / Samsung (gestion batterie agressive) |
| Cas de test | MQA-34 |

**Etapes**
1. Ouvrir l'app, revenir a l'accueil du telephone.
2. Le systeme tue le process (reproduit par `adb shell am kill com.saucelabs.mydemoapp.android`).
3. Rouvrir l'app depuis l'icone ou les apps recentes.

**Obtenu**
```
E AndroidRuntime: Caused by: androidx.fragment.app.Fragment$InstantiationException:
  Unable to instantiate fragment ...ProductCatalogFragment: could not find Fragment constructor
E AndroidRuntime: Caused by: java.lang.NoSuchMethodException: <init> []
```

**Analyse** : `ProductCatalogFragment` n'a qu'un constructeur avec parametre. Android
recree les fragments par reflexion avec le constructeur vide lors d'une restauration.
**Recommandation** : constructeur vide + parametres via `arguments` (Bundle) ; ajouter
"Ne pas conserver les activites" (options developpeur) a la checklist de test manuel.
**Pourquoi c'est important pour une app d'interphone** : l'utilisateur ouvre l'app sur
une notification d'appel apres des heures en arriere-plan, soit exactement ce scenario.

---

## Note d'environnement : popup "Trousseau d'acces" Huawei

Pas un bug de l'app, mais un piege du parc reel : apres un login, le service d'autofill
Huawei (`com.huawei.securitymgr`) affiche "Enregistrer nom d'utilisateur/mot de passe"
au-dessus de l'app, et tous les tests suivants echouent en cascade. Gere par
`framework/app.py::SYSTEM_INTERRUPTIONS`, liste a enrichir a chaque nouveau constructeur.
