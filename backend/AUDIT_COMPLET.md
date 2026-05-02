# 🔍 AUDIT TECHNIQUE COMPLET - PROJET WHILE HEALTH

**Date:** 1 mai 2026  
**Expert:** Senior Django Developer  
**Version Django:** 6.0.2 LTS  
**Système:** While Health - Gestion Hospitalière  

---

## 📋 RÉSUMÉ EXÉCUTIF

### Fichiers analysés:
- `config/settings.py` - Configuration Django
- `patients/models.py` - Modèles Patients, VitalSign, Consultation, Prescription
- `patients/views.py` - Vues principales patients
- `patients/forms.py` - Formulaires patients
- `patients/admin.py` - Configuration admin
- `core/models.py` - Modèle User personnalisé
- `core/views.py` - Vues principales core
- `core/forms.py` - Formulaires core
- `staff/models.py` - Modèles Staff, TimeService, Departement
- `appointment/models.py` - Modèle Appointment
- `appointment/forms.py` - Formulaires appointment
- Templates: appointment.html, patient_message.html

### Technologies identifiées:
- **Backend:** Django 6.0.2 avec DRF + JWT
- **Database:** PostgreSQL (avec Redis pour cache)
- **Frontend:** Django Templates + JavaScript vanilla
- **Security:** JWT, authentification Django, permissions

---

## 🚨 PROBLÈMES CRITIQUES IDENTIFIÉS

### 1. SÉCURITÉ (CRITICAL - RISQUE RGPD/HIPAA)

#### S1: Duplication views avec permissions manquées
**Fichier:** `core/views.py` (lignes ~260-350)  
**Impact:** CRITIQUE - Données médicales exposées sans authentification

Le fichier `core/views.py` contient des copies des vues de `patients/views.py` **SANS** les décorateurs de sécurité:

```python
# PROBLÈME: core/views.py - Appointment SANS sécurité
def appointment(request):
    # ❌ PAS de @login_required
    # ❌ PAS de @permission_required
    doctors = Staff.objects...  # Accessible anonymement
```

对比 `patients/views.py`:
```python
# ✅ CORRECT: patients/views.py - Appointment AVEC sécurité
@login_required
@require_POST  
@csrf_protect
def appointment(request):
    # ✅ Authentifié
```

**Action:** Supprimer les doublons de `core/views.py` OU ajouter tous les décorateurs.

---

#### S2: patient_lookup en GET au lieu de POST
**Fichier:** `core/views.py` ligne ~210  
**Impact:** CRITIQUE - Données patient dans URL/logs serveur

```python
# PROBLÈME: core/views.py
@require_GET  # ❌ INCORRECT - données dans logs
def patient_lookup(request):
    patient = _find_existing_patient(request.GET)  # ❌ GET expose données
    return JsonResponse({"patient": _serialize_patient(patient)})  # ❌ données complètes
```

**Problèmes:**
1. `request.GET` expose données patient dans URL et logs serveur
2. `_serialize_patient()` retourne TOUTES les données (email, address, phone)
3. Pas de `@login_required`

**Code sécurisé dans patients/views.py:**
```python
# ✅ CORRECT
@login_required
@require_POST
@csrf_protect
def patient_lookup(request):
    patient = _find_existing_patient(request.POST)
    return JsonResponse({"patient": _serialize_patient_minimal(patient)})  # données minimales
```

**Action:** 
1. Convertir GET → POST
2. Ajouter @login_required + @csrf_protect
3. Utiliser _serialize_patient_minimal()

---

#### S3: get_available_slots sans authentification
**Fichier:** `core/views.py` ligne ~240  
**Impact:** HIGH - Exposition planning médical

```python
# PROBLÈME
def get_available_slots(request):
    # ❌ Pas de @login_required
    staff_id = request.GET.get("staff_id")  # ❌ GET expose staff_id
    # ❌ Pas de vérification permission
```

**Risque:** Un attaquant peut mapper tous les médecins et leurs créneaux.

**Action:** Ajouter `@login_required`

---

#### S4: patient_message sans permission
**Fichier:** `core/views.py` ligne ~290  
**Impact:** CRITIQUE - Dossier médical complet exposé

```python
# PROBLÈME
def patient_message(request, pk):
    # ❌ Pas de @login_required
    # ❌ Pas de vérification que user est le médecin traitant
    patient = get_object_or_404(Patients, pk=pk)  # ❌ Tout le monde peut voir
    # Retourne TOUTES les données
```

**Action:** Ajouter `@login_required` + vérification permission médecin

---

### 2. PERFORMANCE (HIGH - RISQUE TIMEOUT)

#### P1: Dashboard - Requêtes N+1
**Fichier:** `core/views.py` dashboard()  
**Impact:** 7+ requêtes DB au lieu de 1

```python
# PROBLÈME: core/views.py dashboard()
stats = patients_qs.aggregate(...)  # ✅ Correct (1 requête)
# MAIS:
recent_patients = patients_qs.order_by("-registered_at")[:6]  # ❌ Requête séparée
recent_appointments = appointments_qs[:5]  # ❌ Requête séparée
transferred_count = Patients.objects.filter(transfered=True).count()  # ❌ count() séparé
active_count = Patients.objects.filter(transfered=False).count()  # ❌ count() séparé
```

**Solution dans settings.py:** Cache configuré mais non utilisé.

**Action:** Utiliser le cache Django avec `cache.set()` / `cache.get()`

---

#### P2: Cache Redis non utilisé
**Fichier:** `config/settings.py`  
**Impact:** PERFORMANCE - Temps de réponse lent

```python
# settings.py - Cache configuré ✅
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        ...
    }
}

# MAIS dans core/views.py - JAMAIS utilisé ❌
def dashboard(request):
    # Pas de cache.get() ou cache.set()
```

**Action:** Implémenter:
```python
from django.core.cache import cache

stats_cache = cache.get('dashboard_stats')
if stats_cache is None:
    # calculer
    cache.set('dashboard_stats', context, 300)  # 5 min
```

---

#### P3: get_available_slots - Boucle Python lourde
**Fichier:** `patients/views.py` et `core/views.py`  
**Impact:** 100+ itérations Python par requête

```python
# PROBLÈME: Calculer tous les slots en Python
while current_date <= end_date:
    for ts in day_services:
        while slot_time < ts.close_time:
            # 7 jours * ~16 slots = 112+ itérations
```

**Solution:** 
1. Pré-calculer les slots au niveau DB
2. Stocker en cache avec invalidation sur nouveau RDV

---

#### P4: Missing select_related/prefetch_related
**Fichier:**Plusieurs vues  
**Impact:**N+1 queries

```python
# PROBLÈME: core/views.py patient_list()
patients = Patients.objects.all()  # ❌ Pas de select_related
# Pour chaque patient: accès aux vital_signs = N+1
```

**Action:** Ajouter:
```python
patients = Patients.objects.prefetch_related('vital_signs', 'consultations')
```

---

### 3. BUGS LOGIQUE MÉTIER (MEDIUM)

#### M1: Typos dans forms.py
**Fichier:** `patients/forms.py` ligne ~70  
**Impact:** Formulaire ne fonctionne pas

```python
# PROBLÈME: ConsultationForm
weidgets = {  # ❌ TYPO - devrait être 'widgets'
    'reason_for_consultation': forms.TextArea(...),
}
```

**Correction:**
```python
# ✅ CORRECT
widgets = {
    'reason_for_consultation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
    'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
}
```

---

#### M2: Incohérence nom de champ
**Fichier:** `patients/models.py` vs `patients/forms.py`  
**Impact:** Confusion, bugs potentiels

```python
# models.py
adress = models.CharField("Adresse", ...)  # 'adress' (sans 's' à la fin)

# forms.py
'address': forms.TextInput(...)  # 'address' (avec 's')
```

**Problème:** Widget ne correspond pas au champ du modèle.

**Action:** Uniformiser en `address` (orthographecorrecte)

---

#### M3: Patient lookup email case-sensitive
**Fichier:** `core/views.py`  
**Impact:** Recherche incomplète

```python
# PROBLÈME: Email case-sensitive
patient = Patients.objects.filter(email__iexact=email)  # ✅ iexact

# MAIS dans core/views.py
patient = Patients.objects.filter(email=email)  # ❌ sensitive
```

---

#### M4: DRY violé - Code dupliqué
**Fichier:** `patients/views.py` et `core/views.py`  
**Impact:** Maintenance difficiles, bugs

```python
# Dupliqué:
# - _find_existing_patient()
# - _serialize_patient()
# - _serialize_patient_minimal()
# - appointment()
# - get_available_slots()
# - patient_message()
```

**Solution:** Créer `patients/services.py` pour centraliser.

---

### 4. BONNES PRATIQUES (LOW)

#### B1: Champs non utilisés
**Fichier:** `patients/models.py`  
**Impact:** Confusion

```python
# PROBLÈME: Patients.name existe mais pas utilisé
first_name = models.CharField(...)
last_name = models.CharField(...)
# name = models.CharField(...)  # Redondant avec first_name + last_name
```

**Action:** Utiliser uniquement `first_name` + `last_name` (supprimer `name`)

---

#### B2: Consultation.save() incomplet
**Fichier:** `patients/models.py` Consultation  
**Impact:** Code mort

```python
# Code mort - ne fait rien
def save(self, *args, **kwargs):
    if not self.doctor:
        pass  # ❌ Ne fait rien
    super().save(*args, **kwargs)
```

---

#### B3: TimeService.clean() restrictif
**Fichier:** `staff/models.py`  
**Impact:** Mise à jour difficile

```python
# Empêche la modification après création
def clean(self):
    if self.pk:
        return  # Bloque les updates
    
    today_index = timezone.localdate().weekday()
    allowed_days = {...}
    if self.service_day not in allowed_days:
        raise ValidationError(...)
```

**Risque:** Impossibilité de modifier planning.

---

## 📊 TABLEAU RÉCAPITULATIF

| ID | Catégorie | Problème | Fichier | Gravité | Temps Fix |
|----|-----------|----------|---------|---------|-----------|
| S1 | Sécurité | Duplication views sans permissions | core/views.py | CRITICAL | 30min |
| S2 | Sécurité | patient_lookup GET | core/views.py | CRITICAL | 15min |
| S3 | Sécurité | get_available_slots sans login | core/views.py | HIGH | 15min |
| S4 | Sécurité | patient_message sans login | core/views.py | CRITICAL | 15min |
| P1 | Perf | N+1 queries dashboard | core/views.py | HIGH | 1h |
| P2 | Perf | Cache non utilisé | core/views.py | HIGH | 2h |
| P3 | Perf | Boucle Python slots | patients/views.py | MEDIUM | 2h |
| P4 | Perf | Missing prefetch | Plusieurs | MEDIUM | 1h |
| M1 | Bug | Typo weidgets | patients/forms.py | LOW | 5min |
| M2 | Bug | incohérence address | patients/* | LOW | 15min |
| M3 | Bug | Email case-sensitive | core/views.py | LOW | 10min |
| M4 | Maintenance | DRY violé | patients/core | MEDIUM | 2h |
| B1 | Best practices | Champ name unused | patients/models | LOW | 30min |
| B2 | Best practices | Code mort | patients/models | LOW | 10min |

---

## ✅ CORRECTIONS RECOMMANDÉES

### Phase 1: SÉCURITÉ (Priorité CRITICAL)

#### 1.1 Supprimer doublons core/views.py
```python
# core/views.py - Supprimer les fonctionsDUPLIQUÉES:
# - appointment()
# - patient_lookup()
# - get_available_slots()
# - patient_message()
# - _find_existing_patient()
# - _serialize_patient()
# - _serialize_patient_minimal()

# OU les sécuriser:
@login_required
@require_POST
@csrf_protect
def patient_lookup(request):
    ...
```

#### 1.2 Convertir patient_lookup en POST
```python
# AVANT
@require_GET
def patient_lookup(request):
    patient = _find_existing_patient(request.GET)

# APRÈS
@login_required
@require_POST
@csrf_protect
def patient_lookup(request):
    patient = _find_existing_patient(request.POST)
```

#### 1.3 Utiliser sérialisation minimale
```python
# core/views.py - patient_lookup
return JsonResponse({
    "found": True,
    "patient": _serialize_patient_minimal(patient),  # Au lieu de _serialize_patient()
})
```

---

### Phase 2: PERFORMANCE

#### 2.1 Implémenter cacheDashboard
```python
from django.core.cache import cache

CACHE_KEYS = {
    'dashboard_stats': 'dashboard_stats',
}

def dashboard(request):
    stats_cache = cache.get(CACHE_KEYS['dashboard_stats'])
    if stats_cache is not None:
        context = stats_cache
    else:
        # calculer
        cache.set(CACHE_KEYS['dashboard_stats'], context, 300)
```

#### 2.2 Ajouter select_related/prefetch_related
```python
# Avant
patients = Patients.objects.all()

# Après
patients = Patients.objects.prefetch_related(
    'vital_signs',
    'consultations',
    'consultations__prescriptions'
)
```

#### 2.3 Pagination
```python
from django.core.paginator import Paginator

paginator = Paginator(patients, 25)
page_obj = paginator.get_page(request.GET.get('page'))
```

---

### Phase 3: BUGS

#### 3.1 Corriger typo weidgets
```python
# patients/forms.py - ConsultationForm
widgets = {  # ❌ weidgets → widgets
    'reason_for_consultation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
    'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
}
```

#### 3.2 Uniformiser address
```python
# models.py
address = models.CharField("Adresse", ...)  # address (avec 's')

# forms.py  
'address': forms.TextInput(...)  # address
```

---

## 📈 IMPACT ESTIMÉ

| Correction | Difficulté | Impact |
|------------|------------|--------|
| Supprimer doublons core/views.py | Easy | 🔴 CRITICAL |
| patient_lookup POST | Easy | 🔴 CRITICAL |
| Cache Redis dashboard | Medium | 🟢 10x plus rapide |
| select_related | Easy | 🟢 5x plus rapide |
| Pagination | Medium | 🟢 50x plus rapide |
| Fix typos | Easy | 🟡 Low |

---

## 🎯 ORDRE D'IMPLÉMENTATION

### Jour 1: SÉCURITÉ
1. [30min] Supprimer doublons core/views.py OU ajouter @login_required
2. [15min] Convertir patient_lookup en POST
3. [15min] Sérialisation minimale patient_lookup

### Jour 2: PERFORMANCE
4. [1h] Implémenter cache dashboard
5. [1h] Ajouter select_related/prefetch_related
6. [1h] Pagination patient_list

### Jour 3: BUGS + REFACTORING
7. [30min] Fix typos
8. [1h] DRY - centraliser services
9. [1h] Index DB

---

## ✅ CHECKLIST VALIDATION

- [ ] Aucun endpoint patient accessible sans @login_required
- [ ] patient_lookup utilise POST
- [ ] Toutes les vues utilisent select_related/prefetch_related
- [ ] Cache utilisé pour dashboard
- [ ] Pagination sur toutes les listes > 25 items
- [ ]Aucun count() séparé (utiliser aggregate)
- [ ] Temps de réponse < 200ms

---

*Document généré lors de l'audit technique du projet While Health*
*Django 6.0.2 | PostgreSQL | Redis*
