# 🚀 GUIDE D'IMPLÉMENTATION - Audit While Health

## Phase 1: Setup Environnement (2h)

### Étape 1.1: Installer les dépendances

```bash
# Créer venv (si pas déjà fait)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Installer packages
pip install --upgrade pip
pip install -r requirements.txt

# PostgreSQL driver
pip install psycopg2-binary
pip install dj-database-url
pip install python-decouple
pip install django-redis
```

### Étape 1.2: Créer fichier .env

```bash
# Copier template
cp .env.example .env

# Générer SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Éditer .env avec:
nano .env
```

```env
DEBUG=False
SECRET_KEY=<votre-clé-générée>
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3  # Pour développement
# DATABASE_URL=postgresql://user:pass@localhost/while_health  # Pour production
REDIS_URL=redis://127.0.0.1:6379/1
```

### Étape 1.3: Setup Redis (pour cache)

```bash
# macOS
brew install redis
redis-server

# Linux
sudo apt-get install redis-server
sudo systemctl start redis-server

# Docker (option)
docker run -d -p 6379:6379 redis:latest
```

### Étape 1.4: Mettre à jour settings.py

```bash
# Sauvegarder ancien settings
cp config/settings.py config/settings_backup.py

# Copier nouveau settings
cp config/settings_secure.py config/settings.py

# Test configuration
python manage.py check --deploy
```

---

## Phase 2: Migration Base de Données (3h)

### Étape 2.1: Migrer vers PostgreSQL (optionnel mais recommandé)

```bash
# Créer DB PostgreSQL
sudo -u postgres createdb while_health
sudo -u postgres psql -c "ALTER DATABASE while_health OWNER TO $(whoami);"

# Dumper données SQLite
python manage.py dumpdata > data_backup.json

# Changer DATABASE_URL en .env
# DATABASE_URL=postgresql://user:password@localhost:5432/while_health

# Installer driver PostgreSQL
pip install psycopg2-binary

# Migrer
python manage.py migrate

# Charger données
python manage.py loaddata data_backup.json
```

### Étape 2.2: Créer migration pour modèles optimisés

```bash
# Backup modèles actuels
cp patients/models.py patients/models_old.py

# Copier modèles optimisés
cp patients/models_optimized.py patients/models.py

# Créer migration
python manage.py makemigrations

# Vérifier migration
python manage.py sqlmigrate patients 0003  # Numéro peut varier

# Appliquer
python manage.py migrate
```

### Étape 2.3: Vérifier intégrité données

```bash
# Shell Django
python manage.py shell

>>> from patients.models import Patients
>>> Patients.objects.count()  # Vérifier count
>>> p = Patients.objects.first()
>>> p.full_name  # Tester propriété new
>>> p.age  # Tester âge calculé

# Quitter
exit()
```

---

## Phase 3: Sécurité (4h)

### Étape 3.1: Mettre à jour les vues

```bash
# Copier vues optimisées
cp patients/views_optimized.py patients/views_new.py

# ATTENTION: Merger manuellement avec views existantes 
# pour ne pas perdre la logique personnalisée
```

**À faire manuellement:** 
1. Ouvrir `patients/views.py` et `patients/views_new.py` côte-à-côte
2. Fusionner les changements clés (authentication, pagination)
3. Tester chaque vue

### Étape 3.2: Ajouter authentification sur endpoints

**AVANT (dangereux):**
```python
def appointment(request):  # N'importe qui peut accéder!
    pass
```

**APRÈS:**
```python
@login_required(login_url="login")
def appointment(request):  # Seuls utilisateurs connectés
    if not request.user.is_staff:
        raise PermissionDenied("Staff only")
    pass
```

**Appliquer sur les vues critiques:**
- `appointment()` - ✅ @login_required + staff check
- `patient_lookup()` - ✅ @login_required + staff check  
- `patient_list()` - ✅ @login_required
- `consultation_list()` - ✅ @login_required

### Étape 3.3: Tester authentification

```bash
python manage.py runserver

# 1. Essayer accéder /appointment sans login
# → Should redirect to login

# 2. Login comme patient (non-staff)
# → Should raise PermissionDenied

# 3. Login comme docteur (staff)
# → Should show appointment form ✅
```

### Étape 3.4: Vérifier permissions

```bash
python manage.py shell

>>> from django.contrib.auth.models import Permission
>>> from patients.models import Patients

# Créer permission
Permission.objects.create(
    codename='view_sensitive_data',
    name='Can view patient sensitive data',
    content_type_id=...,  # Patients content_type
)

# Assigner à groupe "Doctors"
from django.contrib.auth.models import Group
doctors = Group.objects.create(name='Doctors')
# Ajouter permission...
```

---

## Phase 4: Performance (5h)

### Étape 4.1: Optimiser requêtes N+1

**Avant (problématique):**
```python
def appointment_list(request):
    appointments = Appointment.objects.all()  # ← N+1!
    for a in appointments:
        print(a.patient.name)  # 1 query par appointment
```

**Après (correct):**
```python
def appointment_list(request):
    appointments = Appointment.objects.select_related(
        'patient', 'staff', 'staff__user'
    )
    for a in appointments:
        print(a.patient.name)  # Zéro query supplémentaire
```

**Checklist à appliquer:**

- [ ] `appointment/admin.py`: Ajouter `list_select_related` 
- [ ] `patients/admin.py`: Ajouter `get_queryset()` avec select_related
- [ ] `patients/views.py`: Ajouter select_related sur consultation list
- [ ] `appointment/views.py`: Ajouter select_related sur appointments list

### Étape 4.2: Setup Cache Redis

```python
# config/settings.py - Vérifier cache config:
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
        }
    }
}
```

```bash
# Tester cache
python manage.py shell

>>> from django.core.cache import cache
>>> cache.set('test_key', 'test_value', 60)
>>> cache.get('test_key')
'test_value'
```

### Étape 4.3: Ajouter cache aux vues

**Dans `core/views.py` ajouter:**
```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache 5 minutes
def dashboard(request):
    # Calculs lourds
    stats = Appointment.objects.aggregate(...)
    return render(request, 'dashboard.html', {'stats': stats})
```

### Étape 4.4: Mesurer avec Django Debug Toolbar

```bash
# Installer
pip install django-debug-toolbar

# Ajouter à settings.py:
INSTALLED_APPS = [
    'debug_toolbar',
    # ...
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # ...
]

INTERNAL_IPS = ['127.0.0.1']

# Ajouter à config/urls.py:
from django.conf import settings
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
```

```bash
# Tester
python manage.py runserver
# Ouvrir http://localhost:8000/patients/list/
# Cliquer "DjDT" en bas-right → voir "SQL" tab
# → Vérifier nombre queries < 5 pour liste patients
```

**Objectif:** Chaque page < 5 queries, < 200ms temps réponse

---

## Phase 5: Validation & Testing (4h)

### Étape 5.1: Tester authentification

```bash
# Créer superuser si inexistant
python manage.py createsuperuser

# Créer user staff (docteur)
python manage.py shell
>>> from core.models import User
>>> from staff.models import Staff, Departement
>>> dept = Departement.objects.first()
>>> user = User.objects.create_user(
...     username='dr_smith',
...     email='smith@hospital.com',
...     password='SecurePass123!',
...     is_staff=True,
...     first_name='John',
...     last_name='Smith'
... )
>>> staff = Staff.objects.create(
...     user=user,
...     departement=dept,
...     role='MEDECIN',
...     is_active=True
... )
```

```bash
# Test login form
python manage.py runserver
# http://localhost:8000/login
# Login avec dr_smith:SecurePass123!
# Essayer créer rendez-vous → Devrait marcher
```

### Étape 5.2: Tester permissions

```bash
# Login comme user NON-STAFF
python manage.py shell
>>> user2 = User.objects.create_user(
...     username='patient1',
...     password='PatientPass123!'
... )

# Test: Patient tries to create appointment
# Should get PermissionDenied ✅

# Test: Patient tries to view sensitive data
# Should get PermissionDenied ✅
```

### Étape 5.3: Tester validations

```bash
python manage.py shell

# Test 1: Prescription avec dosage excessif
>>> from patients.models import Prescription, Consultation
>>> p = Prescription()
>>> p.medication = 'PARACETAMOL'
>>> p.dosage_value = 5000  # Max 1000!
>>> p.dosage_unit = 'MG'
>>> p.frequency = 'TWICE_DAILY'
>>> try:
...     p.full_clean()  # Should raise ValidationError
... except ValidationError as e:
...     print("✅ Validation fonctionne:", e)

# Test 2: Patient avec email existant
>>> from patients.models import Patients
>>> p1 = Patients.objects.create(
...     first_name='John',
...     last_name='Doe',
...     email='john@example.com',
...     contact='+243912345678',
...     sexe='M',
...     adress='123 Main St'
... )
>>> p2 = Patients()
>>> p2.first_name = 'Jane'
>>> p2.last_name = 'Smith'
>>> p2.email = 'john@example.com'  # Duplicate!
>>> p2.contact = '+243987654321'
>>> p2.sexe = 'F'
>>> p2.adress = '456 Oak St'
>>> try:
...     p2.full_clean()
... except ValidationError as e:
...     print("✅ Duplicate detection:", e)
```

### Étape 5.4: Tester pagination

```bash
# Créer 100 patients de test
python manage.py shell
>>> from patients.models import Patients
>>> from faker import Faker
>>> faker = Faker('fr_FR')

>>> for i in range(100):
...     Patients.objects.create(
...         first_name=faker.first_name(),
...         last_name=faker.last_name(),
...         email=f'patient{i}@hospital.com',
...         contact=faker.phone_number(),
...         sexe=['M', 'F'][i % 2],
...         adress=faker.address()
...     )
```

```bash
# Tester pagination
python manage.py runserver
# http://localhost:8000/patients/list/
# → Should show 25 patients per page
# → Click "Next" → Should go to page 2
# → Should handle pagination smoothly ✅
```

### Étape 5.5: Tester cache

```bash
# Charger dashboard avec Django Debug Toolbar
python manage.py runserver
# http://localhost:8000/dashboard
# First load: [time] 50 queries ← Cache miss
# Refresh: [time] 5 queries ← Cache hit ✅
```

---

## Phase 6: Deployment (2h)

### Étape 6.1: Checklist final

```bash
python manage.py check --deploy
```

Devrait retourner:
- ✅ 0 System checks
- ✅ 0 Warnings
- ✅ All green

### Étape 6.2: Collecter static files

```bash
python manage.py collectstatic --noinput --clear
```

### Étape 6.3: Créer superuser production

```bash
# Sur serveur production:
python manage.py createsuperuser
```

### Étape 6.4: Setup gunicorn + nginx

```bash
# Installation
pip install gunicorn

# Tester gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Production avec systemd
# Créer /etc/systemd/system/while-health.service
# Voir template dans docs/
```

---

## Rollback si problème

### Si migration données échoue:

```bash
# Restaurer backup
python manage.py loaddata data_backup.json

# Restaurer settings
cp config/settings_backup.py config/settings.py
```

### Si vues cassées:

```bash
# Restaurer vues
cp patients/views_old.py patients/views.py
```

### Si cache cause problème:

```bash
# Flush tout cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()

# Ou désactiver dans settings.py:
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

---

## Checklist d'implémentation

### Phase 1: Setup
- [ ] Installer dépendances (pip install -r requirements.txt)
- [ ] Créer .env avec SECRET_KEY
- [ ] Setup Redis local
- [ ] Test: `python manage.py check` → OK

### Phase 2: BD
- [ ] Backup données: `python manage.py dumpdata > backup.json`
- [ ] Migrer modèles optimisés
- [ ] Tester intégrité: `Patient.objects.count() > 0`

### Phase 3: Sécurité
- [ ] Authentification: @login_required sur toutes vues sensibles
- [ ] Permissions: @permission_required sur données médicales
- [ ] Test: Patient non-staff ne peut pas créer RDV
- [ ] Test: Endpoints retournent données minimales

### Phase 4: Performance
- [ ] Optimiser N+1: select_related + prefetch_related
- [ ] Cache Redis setup
- [ ] Django Debug Toolbar: <5 queries par page
- [ ] Load test: 100 patients chargent en <200ms

### Phase 5: Testing
- [ ] Auth tests: Login/logout fonctionne
- [ ] Permission tests: Staff can, patient cannot
- [ ] Validation tests: Prescriptions validées
- [ ] Pagination tests: Liste patients pagine à 25

### Phase 6: Deploy
- [ ] `python manage.py check --deploy` → 0 warnings
- [ ] Collectstatic fonctionne
- [ ] Gunicorn + nginx configurés
- [ ] HTTPS enabled
- [ ] Logs setup

---

## Support & Debugging

### Erreur: "No module named 'django_redis'"
```bash
pip install django-redis
```

### Erreur: "DATABASES is not configured"
- Vérifier .env existe et est chargé
- Vérifier settings.py utilise config()

### Query trop lente?
1. Ouvrir Django Debug Toolbar
2. Voir tab "SQL"
3. Identifier query lente
4. Ajouter select_related / prefetch_related

### Cache pas à jour?
```bash
# Flush cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

---

**Duration totale:** 20h  
**Difficulté:** Moyenne  
**Priority:** CRITIQUE (sécurité & performance)

Pour toute question: relire l'audit complet dans `AUDIT_COMPLET.md`
