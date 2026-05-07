# 🧪 Quick Test Checklist - Fonctionnalités Rendez-vous

## 📝 Avant de Commencer

- [ ] Base de données migée : `python manage.py migrate`
- [ ] Serveur en cours d'exécution : `python manage.py runserver`
- [ ] Création de données de test (patients et staff)

---

## 👤 Test 1 : Accès Patient via Téléphone

### A. Vérification du Téléphone

```
URL : http://localhost:8000/verify-phone/
```

- [ ] Page se charge correctement
- [ ] Formulaire visible avec champ "contact"
- [ ] Placeholder téléphone visible
- [ ] Bouton "Vérifier" présent

**Test 1A - Téléphone Valide ✓**
```
Action : Entrer +243 85 123 4567 (numéro valide existant)
Résultat attendu : Redirection vers /my-appointments/
Messages : "Session créée avec succès"
```

- [ ] Redirection fonctionnelle
- [ ] Message de succès affiché
- [ ] Session créée (cookie visible dans DevTools)

**Test 1B - Téléphone Invalide ✗**
```
Action : Entrer 12345 (numéro invalide)
Résultat attendu : Message d'erreur
```

- [ ] Message d'erreur clair
- [ ] Formulaire réaffichage
- [ ] Session non créée

---

## 📋 Test 2 : Liste des Rendez-vous Patient

### URL
```
/my-appointments/
```

### Affichage

- [ ] Titre "Mes Rendez-vous" visible
- [ ] Numero patient affiché
- [ ] Liste des RDV affichée
- [ ] Pas de RDV → message "Aucun rendez-vous"

### RDV Futurs

Pour chaque RDV futur :
- [ ] Badge de statut (En attente/Confirmé) visible
- [ ] Date affichée correctement
- [ ] Heure affichée correctement
- [ ] Nom du docteur affiché
- [ ] Motif affiché
- [ ] Boutons [Modifier] et [Annuler] présents

### RDV Passés

- [ ] Ne s'affichent PAS (filtrage correct)

### Actions

**Test 2A - Bouton Modifier**
```
Action : Cliquer [Modifier] sur un RDV
URL attendue : /appointment/{id}/edit/
```
- [ ] Redirection correcte
- [ ] Formulaire de modification chargé

**Test 2B - Bouton Annuler**
```
Action : Cliquer [Annuler] sur un RDV
URL attendue : /appointment/{id}/delete/
```
- [ ] Page de confirmation affichée
- [ ] Détails du RDV visibles

---

## ✏️ Test 3 : Modification du Rendez-vous (Patient)

### URL
```
/appointment/{id}/edit/
```

### Formulaire

- [ ] Champ Date pré-rempli
- [ ] Champ Heure pré-rempli
- [ ] Champ Motif pré-rempli
- [ ] Bouton "Sauvegarder" visible
- [ ] Bouton "Annuler" visible

### Test 3A - Modification Valide

```
Action : Changer la date et/ou l'heure
         Modifier le motif
         Cliquer "Sauvegarder"
```

- [ ] Redirection vers /my-appointments/
- [ ] Message de succès affiché
- [ ] Données mises à jour en BD

### Test 3B - Créneau Non Disponible

```
Action : Essayer de modifier vers un créneau occupé
         (même docteur, même date/heure)
```

- [ ] Message d'erreur "Créneau non disponible"
- [ ] RDV non modifié
- [ ] Formulaire réaffichage

### Test 3C - Date dans le Passé

```
Action : Essayer de modifier vers une date passée
```

- [ ] Message d'erreur "Date invalide"
- [ ] RDV non modifié

---

## 🗑️ Test 4 : Suppression du Rendez-vous (Patient)

### URL
```
/appointment/{id}/delete/
```

### Page de Confirmation

- [ ] Titre "Confirmation d'Annulation" visible
- [ ] Détails RDV affichés (date, heure, docteur)
- [ ] Message d'avertissement visible
- [ ] Bouton "Oui, Annuler" visible
- [ ] Bouton "Non, Retour" visible

### Test 4A - Confirmation Suppression

```
Action : Cliquer "Oui, Annuler"
```

- [ ] RDV supprimé de la BD
- [ ] Redirection vers /my-appointments/
- [ ] Message "Rendez-vous annulé"
- [ ] RDV plus visible dans la liste

### Test 4B - Annuler Suppression

```
Action : Cliquer "Non, Retour"
```

- [ ] Redirection vers /my-appointments/
- [ ] RDV toujours visible dans la liste

---

## 🔐 Test 5 : Sécurité Session

### Test 5A - Expiration Session

```
Action : Vérifier le téléphone
         Attendre 1 heure (ou manipuler le cookie)
         Essayer d'accéder à /my-appointments/
```

- [ ] Redirection vers /verify-phone/
- [ ] Message "Session expirée"

### Test 5B - Session Token

```
Action : Vérifier le téléphone
         Vérifier le cookie "patient_phone_token" dans DevTools
```

- [ ] Cookie présent
- [ ] Valeur plausible
- [ ] Expiration visible

### Test 5C - Propriété RDV

```
Action : Modifier l'URL pour accéder au RDV d'un autre patient
         http://localhost:8000/appointment/999/delete/
```

- [ ] Erreur 404 ou "Non trouvé"
- [ ] Accès dénié

---

## 👨‍⚕️ Test 6 : Dashboard Staff

### Authentification

```
Action : Aller sur /staff/dashboard/
```

- [ ] Si non connecté → Redirection vers /admin/login/
- [ ] Si connecté → Dashboard chargé

### Page Dashboard

- [ ] Titre "Tableau de Bord" visible
- [ ] Nom du docteur affiché
- [ ] Statistiques affichées :
  - [ ] Nombre RDV en attente
  - [ ] Nombre RDV confirmés
  - [ ] Nombre RDV total

### Sections

**RDV en Attente (Jaune)**
- [ ] Sous-titre visible
- [ ] Chaque RDV affiche :
  - [ ] Nom patient
  - [ ] Date et heure
  - [ ] Motif
  - [ ] Badge "En attente"
  - [ ] Boutons [Valider] [Modifier] [Supprimer]

**RDV Confirmés (Vert)**
- [ ] Sous-titre visible
- [ ] Chaque RDV affiche :
  - [ ] Nom patient
  - [ ] Date et heure
  - [ ] Motif
  - [ ] Badge "Confirmé"
  - [ ] Boutons [Modifier] [Supprimer]

---

## ✅ Test 7 : Validation de Rendez-vous (Staff)

### URL
```
/staff/appointment/{id}/validate/
```

### Formulaire

- [ ] Info du patient affichée (nom, contact)
- [ ] Champ Date pré-rempli
- [ ] Champ Heure pré-rempli
- [ ] Champ Motif pré-rempli
- [ ] Checkbox "Accepter ce rendez-vous" visible
- [ ] Bouton "Sauvegarder" visible
- [ ] Bouton "Annuler" visible

### Test 7A - Validation Succès

```
Action : Laisser les données par défaut
         Cocher "Accepter ce rendez-vous"
         Cliquer "Sauvegarder"
```

- [ ] Redirection vers /staff/dashboard/
- [ ] Message "Rendez-vous validé et confirmé"
- [ ] RDV passe à "Confirmé"
- [ ] Email envoyé (vérifier console)

### Test 7B - Validation sans Accepter

```
Action : Laisser checkbox décochée
         Cliquer "Sauvegarder"
```

- [ ] Redirection vers /staff/dashboard/
- [ ] RDV reste "En attente"
- [ ] Pas d'email envoyé

### Test 7C - Créneau Non Disponible

```
Action : Changer date/heure vers un créneau occupé
         Cocher "Accepter"
         Cliquer "Sauvegarder"
```

- [ ] Message d'erreur "Créneau non disponible"
- [ ] RDV non modifié

---

## 📧 Test 8 : Email de Confirmation

### Configuration

```
Setting : EMAIL_BACKEND en mode console
```

**Dans settings.py**
```python
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Test 8A - Email Envoyé

```
Action : Staff valide un RDV avec "Accepter" cochée
Vérifier : Console du serveur Django
```

- [ ] Événement "Voici le message email que vous avez envoyé :"
- [ ] Destinataire : email du patient
- [ ] Sujet : "Confirmation de votre rendez-vous"
- [ ] Corps : Détails RDV (date, heure, docteur, motif)

### Test 8B - Contenu Email

```
Vérifier le corps de l'email pour :
```

- [ ] Salutation personnalisée : "Bonjour [Patient]"
- [ ] Motif du RDV : "[Motif]"
- [ ] Date formatée : "14 mai 2026"
- [ ] Heure formatée : "14:30"
- [ ] Nom docteur : "Dr. [Nom]"
- [ ] Département : "[Dept]"
- [ ] Message d'accueil professionnel

---

## ✏️ Test 9 : Modification RDV (Staff)

### URL
```
/staff/appointment/{id}/edit/
```

### Formulaire

- [ ] Données pré-remplies
- [ ] Champ Date modifiable
- [ ] Champ Heure modifiable
- [ ] Champ Motif modifiable
- [ ] Pas de checkbox "Accepter"
- [ ] Bouton "Sauvegarder"

### Test 9A - Modification Simple

```
Action : Modifier le motif uniquement
         Cliquer "Sauvegarder"
```

- [ ] Redirection vers /staff/dashboard/
- [ ] Message de succès
- [ ] RDV mis à jour
- [ ] Pas d'email envoyé

### Test 9B - Modification Date/Heure

```
Action : Modifier date et/ou heure vers un créneau libre
         Cliquer "Sauvegarder"
```

- [ ] RDV mis à jour
- [ ] Pas d'email de confirmation

---

## 🗑️ Test 10 : Suppression RDV (Staff)

### URL
```
/staff/appointment/{id}/delete/
```

### Page de Confirmation

- [ ] Détails du patient affichés
- [ ] Détails du RDV affichés
- [ ] Message de confirmation "Êtes-vous sûr?"
- [ ] Bouton "Oui, Supprimer" (rouge)
- [ ] Bouton "Non, Annuler"

### Test 10A - Suppression

```
Action : Cliquer "Oui, Supprimer"
```

- [ ] RDV supprimé de la BD
- [ ] Redirection vers /staff/dashboard/
- [ ] Message de succès
- [ ] RDV plus visible

### Test 10B - Annuler

```
Action : Cliquer "Non, Annuler"
```

- [ ] Redirection vers /staff/dashboard/
- [ ] RDV toujours visible

---

## 🔐 Test 11 : Sécurité Staff

### Test 11A - Login Requis

```
Action : Logout
         Essayer d'accéder directement :
         /staff/dashboard/
```

- [ ] Redirection vers /admin/login/

### Test 11B - Propriété RDV

```
Action : Se connecter comme Staff A
         Essayer de modifier RDV d'une autre Staff B
```

- [ ] Erreur PermissionDenied ou "Non autorisé"

### Test 11C - CSRF Protection

```
Action : Vérifier le token CSRF dans les formulaires
```

- [ ] Token {% csrf_token %} présent dans tous les formulaires POST

---

## 🎨 Test 12 : Design & Responsive

### Mobile (320px)
- [ ] Tous les éléments visibles
- [ ] Pas de débordement horizontal
- [ ] Boutons cliquables

### Tablet (768px)
- [ ] Layout adapté
- [ ] Lisibilité correcte
- [ ] Formulaires fonctionnels

### Desktop (1920px)
- [ ] Design optimal
- [ ] Espacement correct
- [ ] Couleurs bien visibles

---

## 📊 Test 13 : Validation Côté Serveur

### Test 13A - Données Manquantes

```
Action : Envoyer formulaire avec champs vides
         (via console : supprimer champs HTML)
```

- [ ] Message d'erreur serveur
- [ ] Données non sauvegardées

### Test 13B - Format Données

```
Action : Essayer d'entrer du texte dans champ Date
```

- [ ] Message d'erreur de validation
- [ ] Données non acceptées

### Test 13C - Injection SQL

```
Action : Entrer : ' OR '1'='1
```

- [ ] Pas de faille visible
- [ ] Django ORM protection active

---

## 📝 Checklist Finale

### Avant Déploiement

- [ ] Tous les tests "À faire" ✓
- [ ] Aucun message d'erreur 500
- [ ] Aucun warning console
- [ ] Aucun SQL error
- [ ] Base de données intègre
- [ ] Emails configurés
- [ ] Permissions correctes

### Configuration Production

- [ ] DEBUG = False dans settings.py
- [ ] ALLOWED_HOSTS configuré
- [ ] CSRF_TRUSTED_ORIGINS configuré
- [ ] EMAIL_BACKEND = smtp (production)
- [ ] Credentials SMTP sécurisées (.env)
- [ ] SECRET_KEY changée
- [ ] DATABASES configurée (PostgreSQL)

---

## 🐛 Dépannage Rapide

| Problème | Solution |
|----------|----------|
| "Numéro non trouvé" | Vérifier le numéro en BD (via admin) |
| "Session expirée" | Revalider le numéro (durée 1h) |
| "Email non reçu" | Vérifier console Django (DEBUG=True) |
| "PermissionDenied" | Vérifier login et propriété RDV |
| "Créneau indisponible" | Vérifier si créneau libre en BD |

---

## 📞 Support

Pour plus d'informations :
- Documentation : [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- Architecture : [ARCHITECTURE.md](ARCHITECTURE.md)
- Résumé : [SUMMARY.md](SUMMARY.md)

---

**Testé le :** [Date]
**Statut :** [✅ Succès / ⚠️ Avertissement / ❌ Échoué]
**Testeur :** [Nom]
**Commentaires :**

```
[Commentaires ici]
```
