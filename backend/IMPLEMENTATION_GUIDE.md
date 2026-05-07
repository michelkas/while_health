# 📋 Guide de Configuration - Fonctionnalités Rendez-vous While Health

## 🎯 Aperçu des Fonctionnalités Implémentées

### 1. **Côté Patient** - Accès aux rendez-vous via Numéro de Téléphone
- Accès **sans authentification** via numéro de téléphone unique
- Liste des rendez-vous valides (à venir, non annulés)
- Modification de la date, heure, ou motif
- Suppression (annulation) de rendez-vous
- Authentification temporaire sécurisée via token de session (1 heure)

### 2. **Côté Staff** - Tableau de Bord, Validation et Emails
- **Dashboard** affichant :
  - L'emploi du temps (rendez-vous à venir)
  - Rendez-vous en attente de validation
  - Rendez-vous confirmés
- **Validation** des rendez-vous avec envoi d'email au patient
- **Modification** et **suppression** de rendez-vous
- **Email de confirmation** avec template HTML/TXT

---

## 🔧 Configuration Requise

### 1. **Configuration Email**

#### **En Développement (Console Backend)**
Les emails sont affichés dans la console (déjà configuré par défaut avec `DEBUG=True`).

#### **En Production (SMTP)**
Ajoutez les variables d'environnement dans votre `.env` :

```env
# Email Configuration
DEBUG=False
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@whilehealth.cd
SERVER_EMAIL=server@whilehealth.cd
```

**Options de fournisseurs :**
- **Gmail** : `smtp.gmail.com:587`
- **SendGrid** : `smtp.sendgrid.net:587`
- **AWS SES** : `email-smtp.region.amazonaws.com:587`

### 2. **Variables d'Environnement (.env)**

Assurez-vous que votre fichier `.env` contient :

```env
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1

# Session Configuration
SESSION_COOKIE_AGE=3600  # 1 heure pour patient phone access

# Email (Development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Email (Production - uncomment below)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
```

---

## 📁 Structure des Fichiers Modifiés/Créés

### **Modèles**
- `appointment/models.py` - Ajout du champ `raison`

### **Formulaires**
- `appointment/forms.py` - Mise à jour AppointmentForm
- `patients/forms.py` - Ajout PatientPhoneVerificationForm, PatientAppointmentEditForm
- `staff/forms.py` - Ajout StaffAppointmentValidationForm, StaffAppointmentEditForm

### **Vues**
- `patients/views.py` - 4 nouvelles vues pour accès patient
- `staff/views.py` - 4 nouvelles vues pour staff + fonction email

### **Templates**
```
templates/
├── patients/
│   ├── phone_verification.html
│   ├── appointments_list.html
│   ├── appointment_edit.html
│   ├── appointment_delete.html
└── staff/
    ├── dashboard.html
    ├── appointment_validate.html
    ├── appointment_edit.html
    ├── appointment_delete.html
    └── email/
        ├── appointment_confirmation.html
        └── appointment_confirmation.txt
```

### **URLs**
- `patients/urls.py` - 4 nouvelles routes
- `staff/urls.py` - 4 nouvelles routes

### **Migrations**
- `appointment/migrations/0004_add_raison_field.py` - Migration appliquée ✅

---

## 🚀 Utilisation

### **👤 Côté Patient**

#### Étape 1 : Vérifier le numéro de téléphone
- URL : `/verify-phone/`
- L'utilisateur entre son numéro de téléphone
- Un token est créé et stocké en session (valide 1 heure)

#### Étape 2 : Consulter les rendez-vous
- URL : `/my-appointments/`
- Affiche la liste des rendez-vous à venir
- Boutons : **Modifier** et **Supprimer**

#### Étape 3 : Modifier un rendez-vous
- URL : `/appointment/{id}/edit/`
- Permet de changer : date, heure, motif
- Validation des créneaux disponibles

#### Étape 4 : Annuler un rendez-vous
- URL : `/appointment/{id}/delete/`
- Demande confirmation avant suppression

### **👨‍⚕️ Côté Staff (Docteur)**

#### Étape 1 : Se connecter
- L'utilisateur doit être authentifié (système Django standard)
- Accéder au dashboard : `/staff/dashboard/`

#### Étape 2 : Consulter le dashboard
- Affiche :
  - Rendez-vous en attente de validation (onglet "En Attente")
  - Rendez-vous confirmés (onglet "Confirmés")
  - Statistiques (nombre total, etc.)

#### Étape 3 : Valider un rendez-vous
- URL : `/staff/appointment/{id}/validate/`
- Affiche la fiche patient
- Permet de modifier : date, heure, motif
- Case à cocher : **"Accepter et confirmer ce rendez-vous"**
- En cochant, un email est automatiquement envoyé au patient

#### Étape 4 : Modifier un rendez-vous confirmé
- URL : `/staff/appointment/{id}/edit/`
- Permet de mettre à jour les détails

#### Étape 5 : Supprimer un rendez-vous
- URL : `/staff/appointment/{id}/delete/`
- Demande confirmation avant suppression

---

## 📧 Configuration des Emails

### **Template Email Utilisé**

L'email de confirmation contient :

```
✓ Confirmation de Rendez-vous

Bonjour [Patient Name],

DÉTAILS :
- Date : [appointment_date]
- Heure : [appointment_time]
- Département : [department]
- Motif : [reason]

VOTRE DOCTEUR :
- Dr. [doctor_name]
- Spécialité : [doctor_specialty]

Important : Arrivez 10 minutes avant votre rendez-vous
```

### **Tester les Emails en Développement**

1. **Console Backend :**
   - Les emails s'affichent dans le terminal Django
   - Vérifiez la sortie console du serveur

2. **Fichier Console :**
   - Configurer EmailBackend avec fichier :
   ```python
   # settings.py (test)
   if DEBUG:
       EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
       EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'
   ```

3. **Mailtrap/MailHog :**
   - Service SMTP de test gratuit
   - Voir tous les emails envoyés

### **Tester les Emails en Production**

```python
# Tester depuis Django shell
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test Email',
    'Test body',
    'from@whilehealth.cd',
    ['patient@example.com'],
    fail_silently=False,
)
```

---

## 🔐 Sécurité

### **Côté Patient**
- ✅ Token temporaire en session (1 heure)
- ✅ Validation du numéro de téléphone
- ✅ Protection CSRF sur tous les formulaires
- ✅ Vérification d'appartenance (patient ne peut modifier que ses propres RDV)

### **Côté Staff**
- ✅ `@login_required` sur toutes les vues
- ✅ Vérification que le staff est assigné au rendez-vous
- ✅ Impossible de modifier les RDV d'autres staff
- ✅ Validation des données entrantes

### **Bonnes Pratiques**
- ✅ Échappement des contenus HTML
- ✅ Validation des données côté serveur
- ✅ Pas de données sensibles en session client
- ✅ Configuration sécurisée en production (HTTPS, cookies secure, etc.)

---

## 📊 Modèle de Données

### **Appointment - Champs**
```python
patient        : ForeignKey(Patients)
staff          : ForeignKey(Staff)
time_service   : ForeignKey(TimeService)
date           : DateField
time           : TimeField
raison         : TextField (NOUVEAU)
accept         : BooleanField (default=False)
created_at     : DateTimeField (auto)
```

---

## ✅ Tests Recommandés

### **Tests Manuels - Patient**
1. Entrer un numéro de téléphone invalide → erreur
2. Entrer un numéro inexistant → erreur
3. Entrer un numéro valide → redirection vers liste RDV
4. Modifier un RDV (date/heure/motif)
5. Vérifier que le créneau n'est pas disponible → erreur
6. Supprimer un RDV → confirmation

### **Tests Manuels - Staff**
1. Accéder au dashboard sans authentification → redirection login
2. Valider un RDV → voir email en console
3. Modifier date/heure → vérifier les conflits
4. Vérifier que staff ne voit que ses RDV
5. Tester suppression

---

## 🐛 Dépannage

### **Problème : "PermissionDenied" côté patient**
```
Solution : 
- Vérifier que le numéro de téléphone existe dans la base
- Vérifier le format du numéro (+243 vs 243, etc.)
```

### **Problème : Email non envoyé**
```
Solution :
1. Vérifier DEBUG=False en production
2. Vérifier EMAIL_BACKEND est configuré
3. Vérifier les credentials SMTP
4. Tester : python manage.py shell + send_mail()
5. Vérifier les logs d'erreur
```

### **Problème : Token expiré en patient**
```
Solution :
- SESSION_COOKIE_AGE = 3600 (1 heure)
- Modifier dans settings.py si besoin
- Patient doit retourner à /verify-phone/ pour nouvelle session
```

### **Problème : CSRF token invalide**
```
Solution :
- {% csrf_token %} présent dans tous les formulaires POST
- Vérifier CSRF_TRUSTED_ORIGINS dans settings.py
- Vérifier que DEBUG=True en dev
```

---

## 📚 Fichiers à Consulter

| Fichier | Description |
|---------|-------------|
| `config/settings.py` | Configuration email |
| `appointment/models.py` | Modèle Appointment avec raison |
| `patients/views.py` | Vues patient sans auth |
| `staff/views.py` | Vues staff + envoi email |
| `appointment/forms.py` | Formulaires |
| `patients/forms.py` | Formulaires patient |
| `staff/forms.py` | Formulaires staff |

---

## 📞 Support

Pour toute question ou problème, consultez :
- Documentation Django : https://docs.djangoproject.com/
- Django Email : https://docs.djangoproject.com/en/stable/topics/email/
- django-phonenumber-field : https://github.com/stefanfoulis/django-phonenumber-field
