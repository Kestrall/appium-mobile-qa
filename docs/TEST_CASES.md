# Cas de test

Format directement importable dans Xray / TestLink. La colonne **Auto** pointe
vers le test pytest ; le marqueur `@pytest.mark.tc("MQA-xx")` relie le resultat
au cas dans Jira lors de l'import JUnit.

| ID | Titre | Priorite | Plateformes | Auto |
|---|---|---|---|---|
| MQA-1 | Lancement : l'app s'ouvre sur le catalogue | P1 | A / I | `test_smoke.py::test_app_launches_on_catalog` |
| MQA-2 | Demarrage a froid < 10 s | P2 | A / I | `test_smoke.py::test_cold_start_is_fast_enough` |
| MQA-3 | Panier vide au premier lancement | P2 | A / I | `test_smoke.py::test_empty_cart_from_fresh_start` |
| MQA-10 | Connexion valide | P1 | A / I | `test_login.py::test_login_success_lands_on_catalog` |
| MQA-11 | Validation des champs de connexion | P2 | A / I | `test_login.py::test_login_validation_errors` |
| MQA-12 | Compte verrouille refuse | P1 | A / I | `test_login.py::test_locked_user_is_rejected` |
| MQA-13 | Deconnexion avec confirmation | P2 | A | `test_login.py::test_logout_requires_confirmation` |
| MQA-20 | Ajout d'un produit au panier | P1 | A / I | `test_cart.py::test_add_single_product` |
| MQA-21 | Ajout avec quantite | P2 | A / I | `test_cart.py::test_add_product_with_quantity` |
| MQA-22 | Quantite 0 : ajout au panier impossible (valeur limite) | P2 | A / I | `test_cart.py::test_zero_quantity_cannot_be_added` |
| MQA-23 | Panier multi-produits | P2 | A / I | `test_cart.py::test_cart_accumulates_different_products` |
| MQA-25 | Chaque produit du catalogue s'ouvre | P1 | A / I | `test_cart.py::test_every_product_detail_opens` |
| MQA-24 | Suppression du dernier article | P2 | A / I | `test_cart.py::test_remove_last_item_empties_cart` |
| MQA-30 | Refus de la permission camera | P1 | A / I | `test_device_interactions.py::test_camera_permission_denied_is_handled` |
| MQA-31 | Acceptation camera : apercu affiche | P1 | A / I (reel) | `test_device_interactions.py::test_camera_permission_granted_shows_preview` |
| MQA-32 | Etat conserve apres passage en arriere-plan | P1 | A / I | `test_device_interactions.py::test_cart_survives_background` |
| MQA-34 | Restauration apres mort du process en arriere-plan | P1 | A | `test_device_interactions.py::test_app_restores_after_process_death` |
| MQA-33 | Un crash est detecte dans les traces | P2 | A | `test_device_interactions.py::test_crash_is_detected_in_logcat` |

---

## Detail de deux cas (format redactionnel)

### MQA-12 : Compte verrouille refuse

- **Exigence** : un compte desactive ne doit donner acces a aucune fonctionnalite.
- **Preconditions** : app installee, utilisateur deconnecte, compte `alice@example.com` a l'etat verrouille.
- **Etapes**
  1. Ouvrir le menu, choisir "Log In".
  2. Saisir `alice@example.com` / `10203040`.
  3. Valider.
- **Resultat attendu** : message "Sorry this user has been locked out.", l'utilisateur reste sur l'ecran de connexion.
- **Statut** : OK Android, **KO iOS** => MQA-BUG-1.

### MQA-32 : Etat conserve apres passage en arriere-plan

- **Exigence** : une interruption (appel, notification, retour accueil) ne fait pas perdre l'action en cours.
- **Preconditions** : un article dans le panier.
- **Etapes**
  1. Ajouter "Sauce Labs Backpack" au panier.
  2. Envoyer l'app en arriere-plan 5 s.
  3. Revenir dans l'app, ouvrir le panier.
- **Resultat attendu** : l'app revient au premier plan sans redemarrer, le panier contient 1 article.
- **Transposition app client** : appel interphone recu pendant que l'utilisateur gere ses badges.
