# 📊 Flux et Architecture - Fonctionnalités Rendez-vous

## 🔄 Flux Patient (Accès via Téléphone)

```
┌─────────────────────────────────────────────────────────────┐
│                    PATIENT (Non connecté)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ /verify-phone/   │
                    │ Formulaire       │
                    │ Numéro Téléphone │
                    └──────────────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
                    ▼                    ▼
            Numéro Valide         Numéro Invalide
                    │                    │
                    ▼                    ▼
            ✅ Trouvé DB          ❌ Erreur
                    │                    │
                    ▼                    │
          Token session créé             │
          (expiration 1h)                │
                    │                    │
                    ▼                    │
        ┌─────────────────────┐         │
        │ /my-appointments/   │         │
        │ Liste RDV Patient   │         │
        └─────────────────────┘         │
                    │                    │
          ┌─────────┼─────────┐         │
          │         │         │         │
          ▼         ▼         ▼         │
      Modifier  Supprime Déconnex      │
          │         │         │         │
          ▼         ▼         ▼         │
    /edit/{id}  /delete/{id}  │        │
          │         │         │         │
          ▼         ▼         ▼         │
       Validation & Confirmation       │
       (Si succès)                      │
          │         │         │         │
          ▼         ▼         ▼         │
       Retour /my-appointments/        │
          │         │         │         │
          └─────────┴─────────┘         │
                    │                    │
                    ▼                    ▼
          ✅ RDV Mis à Jour   ❌ Afficher
                                      Erreur
```

---

## 👨‍⚕️ Flux Staff (Validation et Email)

```
┌──────────────────────────────────────┐
│   STAFF (Docteur - Authentifié)      │
└──────────────────────────────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │ /staff/dashboard/    │
        │ Tableau de Bord      │
        └──────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
   RDV en Attente      RDV Confirmés
   (badge jaune)       (badge vert)
        │                       │
        ▼                       ▼
   [Valider]            [Modifier]
   [Modifier]           [Supprimer]
   [Supprimer]
        │                       │
        ├───────────┬───────────┤
        │           │           │
        ▼           ▼           ▼
    Valider     Modifier     Supprimer
        │           │           │
        ▼           ▼           ▼
  /validate/   /edit/      /delete/
        │           │           │
        ▼           ▼           ▼
 ┌──────────┐ ┌──────────┐ ┌──────────┐
 │ Formulaire Validation         │ Confirm?
 │ Affiche Patient    Modifier   │ page
 │ Date/Heure/Motif  Date/Heure  │
 │ [Accepter]        [Sauvegarder]│ Supprime
 └──────────┘ └──────────┘ └──────────┘
        │           │           │
        ▼           ▼           ▼
  ✅ Accepté   ✅ Mis à Jour  ✅ Supprimé
        │           │           │
        ▼           │           │
   📧 EMAIL          │           │
   ENVOYÉ           │           │
        │           │           │
        └───────────┴───────────┘
                    │
                    ▼
        Retour /staff/dashboard/
        (RDV mis à jour)
```

---

## 📧 Flux Email (Validation Staff)

```
┌────────────────────────────────────────────┐
│ Staff valide RDV et coche "Accepter"       │
└────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ _send_appointment     │
        │ _confirmation_email() │
        └───────────────────────┘
                    │
        ┌───────────┴──────────────┐
        │                          │
        ▼                          ▼
    Récupérer                  Vérifier
    Patient Email         Patient existe?
        │                    (si pas → retour)
        │                          │
        ├──────────────────────────┤
        │                          │
        ▼                          ▼
    render_to_string()      EmailMultiAlternatives
    - HTML template              │
    - TXT template               ▼
        │                    attach_alternative()
        │                    (HTML)
        ├──────────────────────────┤
        │                          │
        ▼                          ▼
    Contexte Email:         Email Object
    - patient_name          (subject, body,
    - doctor_name            from, to)
    - date
    - time                       │
    - department                 ▼
    - reason                 email.send()
        │                        │
        └────────────────────────┤
                                 ▼
                    ┌────────────────────┐
                    │ CONSOLE BACKEND    │
                    │ (développement)    │
                    │ ou                 │
                    │ SMTP SERVER        │
                    │ (production)       │
                    └────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────┐
                    │ PATIENT REÇOIT     │
                    │ EMAIL              │
                    │ avec détails RDV   │
                    └────────────────────┘
```

---

## 📋 Architecture Globale

```
┌──────────────────────────────────────────────────────────────┐
│                        Django Project                        │
│                     while_health/backend                     │
└──────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
    ┌────────┐            ┌──────┐           ┌──────────┐
    │PATIENTS│            │STAFF │           │APPOINTMENT
    │        │            │      │           │          │
    │ Models │            │Models│           │  Models  │
    │ Views  │            │Views │           │  Forms   │
    │ Forms  │            │Forms │           │          │
    └────────┘            └──────┘           └──────────┘
        │                     │                     │
        │ phone_verify        │ dashboard           │ validate
        │ appointments_list   │ validate            │ modify
        │ edit                │ modify              │ delete
        │ delete              │ delete              │
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
                    ▼                    ▼
            ┌──────────────┐      ┌──────────────┐
            │  TEMPLATES   │      │   FORMS &    │
            │              │      │  VALIDATION  │
            │ patient/     │      │              │
            │ staff/       │      │  - Phone     │
            │              │      │  - Apt Edit  │
            │ email/       │      │  - Apt Val   │
            └──────────────┘      └──────────────┘
                    │                    │
                    └─────────────────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
                    ▼                    ▼
            ┌──────────────┐      ┌──────────────┐
            │   DATABASE   │      │    EMAIL     │
            │              │      │   SERVICE    │
            │ Patients     │      │              │
            │ Appointments │      │ Console/SMTP │
            │ Staff        │      │ Templates    │
            └──────────────┘      └──────────────┘
```

---

## 🔐 Flux de Sécurité

### **Patient**
```
Request → Check Session Token
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
   Token OK      Token Missing/Expired
      │             │
      ▼             ▼
  Allow Access   Redirect to
  to /my-appts/  /verify-phone/
      │
      ▼
  Check Patient
  Ownership
      │
  ┌───┴───┐
  │       │
  ▼       ▼
Owner  Not Owner
  │       │
  ▼       ▼
Allow  PermissionDenied
```

### **Staff**
```
Request → @login_required
              │
      ┌───────┴────────┐
      │                │
      ▼                ▼
  Authenticated     Not Authenticated
      │                │
      ▼                ▼
  Check staff_       Redirect to
  profile exists     login page
      │
      ▼
  Check Staff
  Ownership of
  Appointment
      │
  ┌───┴───┐
  │       │
  ▼       ▼
Owner  Not Owner
  │       │
  ▼       ▼
Allow  PermissionDenied
```

---

## 📡 Endpoints API REST (Optionnel)

```
Patient Endpoints :
GET    /verify-phone/                       Formulaire
POST   /verify-phone/                       Vérifier
GET    /my-appointments/                    Liste
GET    /appointment/{id}/edit/              Formulaire
POST   /appointment/{id}/edit/              Mettre à jour
GET    /appointment/{id}/delete/            Confirmation
POST   /appointment/{id}/delete/            Supprimer

Staff Endpoints :
GET    /staff/dashboard/                    Dashboard
GET    /staff/appointment/{id}/validate/    Validation Form
POST   /staff/appointment/{id}/validate/    Valider + Email
GET    /staff/appointment/{id}/edit/        Edit Form
POST   /staff/appointment/{id}/edit/        Mettre à jour
GET    /staff/appointment/{id}/delete/      Confirmation
POST   /staff/appointment/{id}/delete/      Supprimer
```

---

## 💾 Modèle de Données

```
┌──────────────────────────────────────────────┐
│              Appointment                     │
├──────────────────────────────────────────────┤
│ id (PK)                                      │
│ patient (FK → Patients)                      │
│ staff (FK → Staff)                           │
│ time_service (FK → TimeService)              │
│ date (DateField)                             │
│ time (TimeField)                             │
│ raison (TextField) ← NOUVEAU                 │
│ accept (BooleanField, default=False)         │
│ created_at (DateTimeField, auto_now_add)     │
└──────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
    Patients        Staff         TimeService
      ├──────┐   ├───────┐       ├──────────┐
      │ id   │   │ id    │       │ id       │
      │ name │   │ name  │       │ staff_id │
      │...   │   │...    │       │ day      │
      └──────┘   └───────┘       │ open_time│
                                 │close_time│
                                 └──────────┘
```

---

## 🎨 Flux UI/UX

### **Patient**
```
Accueil
    ↓
[Lien] Accéder à mes rendez-vous
    ↓
Formulaire Téléphone
    ↓
    ├─→ Erreur → Message
    │
    └─→ Succès
        ↓
    Liste Rendez-vous
        ├─→ Vide → "Aucun rendez-vous"
        │
        └─→ Avec RDV
            ├─ [Modifier] → Formulaire → Succès/Erreur
            ├─ [Annuler]  → Confirmation → Succès/Erreur
            └─ [Logout]   → Redirection
```

### **Staff**
```
Login
    ↓
Dashboard
    ├─ Stats Cards (Nombre RDV)
    │
    ├─ RDV en Attente
    │  ├─ [Valider] → Validation Form → Email
    │  ├─ [Modifier] → Edit Form
    │  └─ [Supprimer] → Confirmation
    │
    └─ RDV Confirmés
       ├─ [Modifier] → Edit Form
       └─ [Supprimer] → Confirmation
```

---

## 📱 Cas d'Usage Utilisateur

### **Scénario Patient**
```
1. Visite site While Health
2. Cherche "Accéder à mes rendez-vous"
3. Clique sur le lien
4. Arrive sur /verify-phone/
5. Entre numéro de téléphone
6. Voit sa liste de rendez-vous
7. Peut modifier (date/heure/motif)
8. Peut annuler un rendez-vous
9. Session expire après 1 heure
10. Doit se re-identifier pour continuer
```

### **Scénario Staff**
```
1. Docteur se connecte (login Django)
2. Clique sur "Mon Dashboard" ou va à /staff/dashboard/
3. Voir ses rendez-vous du jour/semaine
4. Voir les RDV en attente (section spéciale)
5. Clique "Valider & Confirmer" sur un RDV
6. Revoit les détails du patient
7. Peut modifier date/heure/motif
8. Coche "Accepter ce rendez-vous"
9. Envoie (automatiquement)
10. Email reçu par le patient
11. RDV passe au statut "Confirmé"
12. Peut modifier ou supprimer des RDV
```

---

## 🔄 États d'un Rendez-vous

```
┌──────────────┐
│    CRÉÉ      │
│ accept=False │
└──────────────┘
       │
       ▼
┌──────────────────┐
│    EN ATTENTE    │ (Patient ou Staff peut modifier/supprimer)
│ accept=False     │
└──────────────────┘
       │
       ├─→ MODIFIÉ → retour à EN ATTENTE
       │
       ├─→ SUPPRIMÉ → Suppression DB
       │
       └─→ VALIDÉ
           (par Staff)
           │
           ▼
       ┌──────────────┐
       │ CONFIRMÉ     │ (Email envoyé au patient)
       │ accept=True  │
       └──────────────┘
               │
               ├─→ MODIFIÉ (raison, date, heure)
               │
               └─→ SUPPRIMÉ
```

---

## 📊 Tableau de Résumé

| Aspect | Patient | Staff |
|--------|---------|-------|
| Authentification | Téléphone | Login Django |
| Session | 1 heure | Standard Django |
| Créer RDV | Via formulaire existant | Via Admin |
| Voir RDV | Liste personnelle | Dashboard |
| Modifier RDV | Date/Heure/Motif | Date/Heure/Motif |
| Supprimer RDV | Oui (confirmation) | Oui (confirmation) |
| Valider RDV | ❌ Non | ✅ Oui (+ email) |
| Email | Reçoit confirmation | Envoie confirmation |
| Permissions | Ses propres RDV | Ses propres RDV |

---

**Diagramme créé le :** 7 mai 2026
**Statut :** ✅ Complet
**Révision :** 1.0
