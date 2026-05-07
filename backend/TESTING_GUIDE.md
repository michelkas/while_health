# 🧪 Guide de Test - Fonctionnalités Rendez-vous While Health

## 📋 Checklist de Test Fonctionnel

### **Test 1 : Accès Patient via Téléphone**

#### 1.1 - Page de Vérification
```
✅ Naviguer vers http://localhost:8000/verify-phone/
✅ Formulaire affiche : "Numéro de téléphone"
✅ Bouton : "Vérifier & Accéder à mes rendez-vous"
```

#### 1.2 - Cas d'erreur
```
✅ Entrer un numéro invalide → Erreur "Numéro de téléphone invalide"
✅ Entrer un numéro inexistant → Erreur "Aucun patient trouvé..."
✅ Laisser vide → Erreur "Veuillez entrer un numéro..."
```

#### 1.3 - Succès
```
✅ Entrer un numéro valide → Redirection vers /my-appointments/
✅ Session token créé (vérifier dans Django shell)
✅ Cookie de session visible dans DevTools
```

#### 1.4 - Liste des Rendez-vous
```
✅ Page affiche : Nom, Téléphone, Email du patient
✅ Chaque RDV affiche : Date, Heure, Docteur, Département
✅ Boutons : Modifier, Annuler pour chaque RDV
✅ Statut : "Confirmé" ou "En attente"
```

#### 1.5 - Modification d'un Rendez-vous
```
✅ Cliquer sur "Modifier"
✅ Formulaire pré-rempli avec date/heure actuelles
✅ Changer date et heure
✅ Changer le motif
✅ Soumettre → "Rendez-vous modifié avec succès"
✅ Retour à la liste avec changements appliqués
```

#### 1.6 - Suppression d'un Rendez-vous
```
✅ Cliquer sur "Annuler"
✅ Page de confirmation affiche les détails du RDV
✅ Message d'avertissement : "Action irréversible"
✅ Cliquer "Oui, Annuler le rendez-vous"
✅ RDV disparu de la liste
✅ Message : "Rendez-vous annulé avec succès"
```

#### 1.7 - Sécurité de Session
```
✅ Session expire après 1 heure
✅ Actualiser la page après 1h → Redirection vers /verify-phone/
✅ Accéder à /my-appointments/ sans session → Redirection
```

---

### **Test 2 : Dashboard Staff**

#### 2.1 - Authentification
```
✅ Non connecté → Accéder à /staff/dashboard/ → Redirection login
✅ Connecté → /staff/dashboard/ → Dashboard visible
✅ Affiche "Bienvenue, Dr. [Nom du docteur]"
```

#### 2.2 - Statistiques
```
✅ Card affiche : "En Attente" (nombre)
✅ Card affiche : "Confirmés" (nombre)
✅ Card affiche : "Total" (nombre)
✅ Les nombres correspondent aux RDV filtrés par staff
```

#### 2.3 - Rendez-vous en Attente
```
✅ Section "Rendez-vous en Attente" visible
✅ Chaque RDV affiche :
   - Date et heure
   - Nom du patient et téléphone
   - Motif
   - Badge "En Attente" (jaune)
✅ Boutons : "Valider & Confirmer", "Modifier", "Supprimer"
```

#### 2.4 - Rendez-vous Confirmés
```
✅ Section "Rendez-vous Confirmés" visible
✅ Statut : Badge "Confirmé" (vert)
✅ Boutons : "Modifier", "Supprimer"
✅ Pas de bouton "Valider" pour les confirmés
```

---

### **Test 3 : Validation et Email**

#### 3.1 - Page de Validation
```
✅ Cliquer sur "Valider & Confirmer"
✅ Page affiche :
   - Informations du patient (nom, téléphone, email)
   - Formulaire de modification (date, heure, motif)
   - Case à cocher : "Accepter et confirmer ce rendez-vous"
```

#### 3.2 - Modification avant Validation
```
✅ Changer date/heure → Vérifier les conflits
✅ Essayer un créneau occupé → Erreur "Créneau non disponible"
✅ Changer le motif
✅ Soumettre sans cocher "Accepter" → RDV mis à jour (pas confirmé)
```

#### 3.3 - Validation et Envoi Email
```
✅ Cocher "Accepter et confirmer ce rendez-vous"
✅ Cliquer "Enregistrer & Confirmer"
✅ Message : "Rendez-vous confirmé et email envoyé au patient"
✅ Email visible en console Django (en développement)
   Contenu du mail devrait inclure :
   - "Confirmation de Rendez-vous"
   - Nom du patient
   - Nom du docteur
   - Date et heure
   - Département
   - Motif
```

#### 3.4 - Contenu de l'Email
```
✅ Sujet : "Confirmation de votre rendez-vous - While Health"
✅ De : "noreply@whilehealth.cd" (ou configuré)
✅ À : Email du patient
✅ Format HTML et texte

Template HTML devrait contenir :
✅ Header avec gradient bleu-violet
✅ "✓ Confirmation de Rendez-vous"
✅ Salutation personnalisée
✅ Boîte de détails (date, heure, département, motif)
✅ Informations du docteur
✅ Message important (arriver 10 min avant)
✅ Footer avec logo et contact
```

---

### **Test 4 : Modification et Suppression (Staff)**

#### 4.1 - Modification
```
✅ Cliquer sur "Modifier" depuis le dashboard
✅ Formulaire pré-rempli
✅ Changer date/heure
✅ Soumettre → "Rendez-vous modifié avec succès"
✅ Vérifier les changements au retour au dashboard
```

#### 4.2 - Suppression
```
✅ Cliquer sur "Supprimer" depuis le dashboard
✅ Page de confirmation affiche :
   - Détails du RDV
   - Message d'avertissement (action irréversible)
✅ Cliquer "Oui, Supprimer"
✅ Message : "Rendez-vous supprimé avec succès"
✅ RDV disparu du dashboard
```

---

### **Test 5 : Sécurité**

#### 5.1 - Permissions Patient
```
✅ Patient A ne peut pas modifier RDV de Patient B
   Tester : Modifier l'URL /appointment/AUTRE_ID/edit/
   Résultat : PermissionDenied (404 ou message d'erreur)
✅ Patient ne peut voir que ses propres RDV
```

#### 5.2 - Permissions Staff
```
✅ Staff A ne peut pas modifier RDV de Staff B
   Tester : Modifier l'URL avec RDV d'autre staff
   Résultat : PermissionDenied (404 ou message d'erreur)
✅ Staff non connecté → Redirection login
```

#### 5.3 - Protection CSRF
```
✅ Tous les formulaires POST incluent {% csrf_token %}
✅ Soumettre sans token → Erreur CSRF
✅ Soumettre avec token → Succès
```

#### 5.4 - Validation des Données
```
✅ Entrer date passée → Erreur
✅ Entrer heure invalide → Erreur
✅ Entrer créneau occupé → Erreur "Créneau non disponible"
✅ Entrer numéro de téléphone vide → Erreur
```

---

## 🐛 Tests de Dépannage

### **Test Email Console**
```python
# django shell
python manage.py shell

from django.core.mail import send_mail
result = send_mail(
    'Test Subject',
    'Test message',
    'from@whilehealth.cd',
    ['to@example.com'],
    fail_silently=False,
)
print(f"Email sent: {result}")  # Devrait afficher 1
```

### **Test Session Token Patient**
```python
# django shell
from django.contrib.sessions.models import Session
from django.utils import timezone
import json

# Voir les sessions actives
sessions = Session.objects.filter(expire_date__gte=timezone.now())
for session in sessions:
    data = session.get_decoded()
    if 'patient_phone_token' in data:
        print(f"Patient ID: {data['patient_id']}")
        print(f"Token: {data['patient_phone_token'][:10]}...")
```

### **Test Appointments par Staff**
```python
# django shell
from appointment.models import Appointment
from staff.models import Staff

staff = Staff.objects.first()
appointments = Appointment.objects.filter(staff=staff)
print(f"Staff {staff.user.get_full_name()} has {appointments.count()} appointments")

for apt in appointments:
    print(f"- {apt.date} {apt.time} : {apt.patient.full_name} ({'Confirmé' if apt.accept else 'En attente'})")
```

---

## 📊 Cas de Test Combinés

### **Scénario 1 : Patient Complet**
```
1. Aller à /verify-phone/
2. Entrer numéro de téléphone valide
3. Voir la liste de ses RDV
4. Modifier un RDV (date/heure)
5. Voir le RDV modifié dans la liste
6. Annuler un autre RDV
7. Voir le RDV supprimé (404 si accès direct)
8. Vérifier que session expire après 1h
```

### **Scénario 2 : Staff Complet**
```
1. Se connecter (login Django)
2. Aller à /staff/dashboard/
3. Voir ses RDV (en attente et confirmés)
4. Cliquer "Valider & Confirmer" sur un RDV en attente
5. Modifier la date/heure si nécessaire
6. Cocher "Accepter et confirmer"
7. Voir l'email en console
8. Retour au dashboard - RDV maintenant dans "Confirmés"
9. Cliquer "Modifier" sur un RDV confirmé
10. Cliquer "Supprimer" et confirmer
11. RDV disparu du dashboard
```

### **Scénario 3 : Edge Cases**
```
1. Patient : Essayer d'accéder /my-appointments/ sans session
   → Redirection vers /verify-phone/
2. Staff : Essayer d'accéder /staff/dashboard/ non connecté
   → Redirection vers login
3. Patient : Essayer de modifier RDV d'autre patient
   → Erreur PermissionDenied
4. Staff : Essayer de modifier RDV d'autre staff
   → Erreur PermissionDenied ou 404
5. Entrer créneau occupé
   → Erreur "Créneau non disponible"
```

---

## ✅ Checklist Final

- [ ] Tous les tests fonctionnels passent
- [ ] Aucune erreur dans les logs
- [ ] Emails reçus correctement (console ou SMTP)
- [ ] Permissions respectées
- [ ] Sessions fonctionnent
- [ ] CSRF tokens présents
- [ ] Messages flash affichent correctement
- [ ] Design responsive (desktop/mobile)
- [ ] Migrations appliquées
- [ ] `python manage.py check` : 0 issues
- [ ] Documentation complète

---

## 📞 Erreurs Communes

| Erreur | Cause | Solution |
|--------|-------|----------|
| "Aucun patient trouvé" | Numéro invalide/inexistant | Utiliser numéro enregistré |
| "PermissionDenied" | Patient/staff non autorisé | Vérifier les permissions |
| "Email non envoyé" | EMAIL_BACKEND non configuré | Vérifier settings.py |
| "Créneau non disponible" | Slot occupé | Choisir un autre créneau |
| "Session expirée" | Token > 1h | Retourner à /verify-phone/ |
| "CSRF token missing" | Formulaire sans {% csrf_token %} | Ajouter token au template |

