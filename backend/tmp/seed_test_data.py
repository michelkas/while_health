from pathlib import Path
from datetime import date, datetime, timedelta

import os
import sys
import django

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.utils import timezone
from core.models import User
from data.models import Hero, About, Service, Emergency, EmergencyInfo, Contact
from staff.models import Departement, Staff, TimeService
from patients.models import Patients, MedicalHistory, VitalSign
from appointment.models import Appointment, get_french_weekday


MEDIA_DIR = BASE_DIR / "media"


def ensure_svg(path: Path, label: str, bg: str, fg: str = "#ffffff"):
    path.parent.mkdir(parents=True, exist_ok=True)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800">
  <rect width="1200" height="800" fill="{bg}"/>
  <circle cx="220" cy="180" r="120" fill="rgba(255,255,255,0.18)"/>
  <circle cx="980" cy="620" r="180" fill="rgba(255,255,255,0.12)"/>
  <text x="60" y="420" fill="{fg}" font-size="64" font-family="Arial, sans-serif" font-weight="700">{label}</text>
</svg>"""
    path.write_text(svg, encoding="utf-8")


def ensure_avatar(path: Path, initials: str, bg: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
  <rect width="400" height="400" rx="36" fill="{bg}"/>
  <circle cx="200" cy="150" r="72" fill="rgba(255,255,255,0.92)"/>
  <path d="M90 338c18-62 68-98 110-98s92 36 110 98" fill="rgba(255,255,255,0.92)"/>
  <text x="200" y="380" text-anchor="middle" fill="#ffffff" font-size="36" font-family="Arial, sans-serif" font-weight="700">{initials}</text>
</svg>"""
    path.write_text(svg, encoding="utf-8")


def phone_cd(index: int) -> str:
    return f"+243970000{index:03d}"


now = timezone.localtime()
today = now.date()
service_day_label = get_french_weekday(today)

current_slot_minute = 30 if now.minute >= 30 else 0
current_slot_dt = datetime.combine(
    today,
    now.replace(minute=current_slot_minute, second=0, microsecond=0).time(),
)

start_of_day_dt = datetime.combine(today, datetime.min.time())
end_of_day_dt = datetime.combine(today, datetime.max.time().replace(microsecond=0))

past_slot_dt = current_slot_dt - timedelta(minutes=60)
future_slot_dt = current_slot_dt + timedelta(minutes=60)

if past_slot_dt < start_of_day_dt:
    past_slot_dt = current_slot_dt - timedelta(minutes=30)
if past_slot_dt < start_of_day_dt:
    past_slot_dt = current_slot_dt

if future_slot_dt > end_of_day_dt:
    future_slot_dt = current_slot_dt + timedelta(minutes=30)
if future_slot_dt > end_of_day_dt:
    future_slot_dt = current_slot_dt

current_slot_start = current_slot_dt.time()
past_slot = past_slot_dt.time()
future_slot = future_slot_dt.time()

ensure_svg(MEDIA_DIR / "hero" / "hero-test.svg", "MediTrust Hero", "#0d6efd")
ensure_svg(MEDIA_DIR / "about" / "about-test.svg", "A Propos", "#14b8a6")
ensure_svg(MEDIA_DIR / "departements" / "cardiologie.svg", "Cardiologie", "#ef4444")
ensure_svg(MEDIA_DIR / "departements" / "pediatrie.svg", "Pediatrie", "#22c55e")
ensure_svg(MEDIA_DIR / "departements" / "chirurgie.svg", "Chirurgie", "#f59e0b")
ensure_svg(MEDIA_DIR / "departements" / "radiologie.svg", "Radiologie", "#8b5cf6")
ensure_avatar(MEDIA_DIR / "avatar" / "doctor-alain.svg", "AM", "#2563eb")
ensure_avatar(MEDIA_DIR / "avatar" / "doctor-brenda.svg", "BK", "#7c3aed")
ensure_avatar(MEDIA_DIR / "avatar" / "doctor-charles.svg", "CL", "#059669")
ensure_avatar(MEDIA_DIR / "avatar" / "doctor-diane.svg", "DN", "#dc2626")
ensure_avatar(MEDIA_DIR / "avatar" / "admin.svg", "AD", "#0f766e")

Hero.objects.update_or_create(
    pk=1,
    defaults={
        "title": "Centre medical de confiance",
        "subtitle": "Des soins modernes et une equipe disponible pour vos consultations",
        "description": "Etablissement de test pour valider l'affichage de la page d'accueil, la disponibilite des medecins et le parcours de prise de rendez-vous.",
        "image": "hero/hero-test.svg",
    },
)

About.objects.update_or_create(
    pk=1,
    defaults={
        "title": "A propos de MediTrust",
        "subtitle": "Une equipe pluridisciplinaire au service des patients",
        "year": date(2015, 1, 1),
        "goal": "Offrir un parcours de soins rapide, humain et fiable.",
        "location": "Lubumbashi",
        "description": "Structure de demonstration pour les tests fonctionnels et visuels du projet Django.",
        "compassionate_care": "Prise en charge bienveillante, attentive et continue des patients et de leurs familles.",
        "care_quality": "Suivi medical rigoureux, coordination entre services et recherche de qualite.",
        "image": "about/about-test.svg",
    },
)

Emergency.objects.update_or_create(
    pk=1,
    defaults={
        "title": "Urgence 24h/24",
        "description": "Notre service d'urgence prend en charge les situations critiques a tout moment.",
        "phone": "+243 970 000 111",
    },
)

Contact.objects.update_or_create(
    pk=1,
    defaults={
        "name": "MediTrust",
        "operation_days_time": "Lundi - Samedi | 07:00 - 19:00",
        "phone": "+243 970 000 222",
        "email": "contact@meditrust.test",
        "address": "Avenue de la Sante, Lubumbashi",
        "facebook": "https://facebook.com/meditrust.test",
        "twitter": "https://x.com/meditrust_test",
        "instagram": "https://instagram.com/meditrust.test",
        "linkedin": "https://linkedin.com/company/meditrust-test",
    },
)

for item in [
    {
        "title": "Salle d'urgence",
        "phone": "+243 970 000 333",
        "address": "Bloc urgence, rez-de-chaussee",
        "operation_time": "24h/24 - 7j/7",
    },
    {
        "title": "Urgent Care",
        "phone": "+243 970 000 334",
        "address": "Batiment B, niveau 1",
        "operation_time": "Tous les jours | 07:00 - 22:00",
    },
    {
        "title": "Helpline infirmiere",
        "phone": "+243 970 000 335",
        "address": "Assistance telephonique",
        "operation_time": "24h/24 - 7j/7",
    },
]:
    EmergencyInfo.objects.update_or_create(title=item["title"], defaults=item)

departments_data = [
    ("Cardiologie", "Service de prise en charge cardiovasculaire et suivi clinique.", "departements/cardiologie.svg"),
    ("Pediatrie", "Soins des nourrissons, enfants et adolescents.", "departements/pediatrie.svg"),
    ("Chirurgie", "Interventions programmees et urgences chirurgicales.", "departements/chirurgie.svg"),
    ("Radiologie", "Imagerie medicale et examens diagnostiques specialises.", "departements/radiologie.svg"),
]

departments = {}
for name, description, image in departments_data:
    dept, _ = Departement.objects.update_or_create(
        name=name,
        defaults={"description": description, "image": image},
    )
    departments[name] = dept

Service.objects.all().delete()
services_data = [
    ("Consultation cardiologique", "Cardiologie", "heart-pulse", "ECG, echographie, suivi tensionnel, bilan cardiaque"),
    ("Suivi pediatrique", "Pediatrie", "emoji-smile", "Vaccination, croissance, nutrition, consultations nourrissons"),
    ("Chirurgie generale", "Chirurgie", "scissors", "Bloc operatoire, preparation, suivi post-operatoire, hospitalisation"),
    ("Imagerie diagnostique", "Radiologie", "activity", "Radiographie, echo, interpretation, compte rendu"),
    ("Medecine preventive", "Cardiologie", "shield-check", "Depistage, conseils, evaluation, orientation"),
]
for title, dept_name, icon, short_desc in services_data:
    Service.objects.create(
        title=title,
        departement=departments[dept_name],
        description=f"{title} - service cree pour les tests applicatifs.",
        icon=icon,
        short_description=short_desc,
    )

admin_user, _ = User.objects.update_or_create(
    username="admin_test",
    defaults={
        "first_name": "Admin",
        "last_name": "Test",
        "email": "admin.test@meditrust.test",
        "is_staff": True,
        "is_superuser": True,
        "avatar": "avatar/admin.svg",
    },
)
admin_user.set_password("admin12345")
admin_user.save()

doctors_data = [
    {
        "username": "doc_alain",
        "first_name": "Alain",
        "last_name": "Mukeba",
        "email": "alain.mukeba@meditrust.test",
        "avatar": "avatar/doctor-alain.svg",
        "department": "Cardiologie",
        "specialty": "RADIOLOGUE",
        "experience": 7,
        "slot_type": "current",
    },
    {
        "username": "doc_brenda",
        "first_name": "Brenda",
        "last_name": "Kabeya",
        "email": "brenda.kabeya@meditrust.test",
        "avatar": "avatar/doctor-brenda.svg",
        "department": "Pediatrie",
        "specialty": "PEDIATRE",
        "experience": 5,
        "slot_type": "future",
    },
    {
        "username": "doc_charles",
        "first_name": "Charles",
        "last_name": "Lukusa",
        "email": "charles.lukusa@meditrust.test",
        "avatar": "avatar/doctor-charles.svg",
        "department": "Chirurgie",
        "specialty": "CHIRURGIE",
        "experience": 11,
        "slot_type": "past",
    },
    {
        "username": "doc_diane",
        "first_name": "Diane",
        "last_name": "Numbi",
        "email": "diane.numbi@meditrust.test",
        "avatar": "avatar/doctor-diane.svg",
        "department": "Radiologie",
        "specialty": "RADIOLOGUE",
        "experience": 4,
        "slot_type": None,
    },
]

created_staff = []
for idx, doctor in enumerate(doctors_data, start=1):
    user, _ = User.objects.update_or_create(
        username=doctor["username"],
        defaults={
            "first_name": doctor["first_name"],
            "last_name": doctor["last_name"],
            "email": doctor["email"],
            "avatar": doctor["avatar"],
            "is_staff": True,
        },
    )
    user.set_password("doctor12345")
    user.save()

    staff, _ = Staff.objects.update_or_create(
        user=user,
        defaults={
            "name": doctor["last_name"],
            "last_name": doctor["last_name"],
            "first_name": doctor["first_name"],
            "specialty": doctor["specialty"],
            "departement": departments[doctor["department"]],
            "role": "MEDECIN",
            "is_active": True,
            "is_verified": True,
            "experience_years": doctor["experience"],
        },
    )
    created_staff.append((staff, doctor["slot_type"]))

    TimeService.objects.update_or_create(
        staff=staff,
        service_day=service_day_label,
        defaults={"open_time": "00:00", "close_time": "23:59"},
    )

patients_data = [
    ("Mireille", "Ilunga", "F"),
    ("Jordan", "Tshibangu", "M"),
    ("Ruth", "Kalala", "F"),
    ("Patrick", "Kanku", "M"),
    ( "Grace", "Mutombo", "F"),
    ( "Cedric", "Katowa", "M"),
]

created_patients = []
for idx, (first_name, last_name, sexe) in enumerate(patients_data, start=1):
    patient, _ = Patients.objects.update_or_create(
        email=f"patient{idx}@meditrust.test",
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "contact": phone_cd(100 + idx),
            "adress": f"Quartier Test {idx}, Lubumbashi",
            "sexe": sexe,
            "tutor": f"Tuteur {idx}",
            "tutor_contact": phone_cd(200 + idx),
            "tutor_adress": f"Avenue Parent {idx}, Lubumbashi",
            "transfered": idx % 3 == 0,
        },
    )
    created_patients.append(patient)

    MedicalHistory.objects.update_or_create(
        patient=patient,
        defaults={
            "chronic_diseases": "Hypertension legere" if idx % 2 == 0 else "Aucune maladie chronique connue",
            "allergies": "Penicilline" if idx % 3 == 0 else "Aucune allergie connue",
            "long_term_treatments": "Supplement vitaminique",
            "lifestyle_habits": "Activite physique moderee, alimentation surveillee",
            "family_history": "Antecedents cardiovasculaires dans la famille" if idx % 2 == 0 else "RAS",
        },
    )

    VitalSign.objects.update_or_create(
        patient=patient,
        defaults={
            "temperature": "36.8",
            "heart_rate": 78 + idx,
            "oxygen_saturation": 97,
            "blood_pressure": "120/80",
            "pulse": 76 + idx,
            "respiration_rate": 18,
        },
    )

for patient in created_patients:
    Appointment.objects.filter(patient=patient).delete()

for index, (staff, slot_type) in enumerate(created_staff):
    if slot_type is None:
        continue

    ts = TimeService.objects.get(staff=staff, service_day=service_day_label)
    patient = created_patients[index]

    if slot_type == "current":
        appt_time = current_slot_start
        accepted = True
    elif slot_type == "future":
        appt_time = future_slot
        accepted = True
    else:
        appt_time = past_slot
        accepted = True

    Appointment.objects.create(
        patient=patient,
        staff=staff,
        time_service=ts,
        date=today,
        time=appt_time,
        accept=accepted,
    )

summary = {
    "Hero": Hero.objects.count(),
    "About": About.objects.count(),
    "Service": Service.objects.count(),
    "Emergency": Emergency.objects.count(),
    "EmergencyInfo": EmergencyInfo.objects.count(),
    "Contact": Contact.objects.count(),
    "Departement": Departement.objects.count(),
    "User": User.objects.count(),
    "Staff": Staff.objects.count(),
    "TimeService": TimeService.objects.count(),
    "Patients": Patients.objects.count(),
    "MedicalHistory": MedicalHistory.objects.count(),
    "VitalSign": VitalSign.objects.count(),
    "Appointment": Appointment.objects.count(),
}

print("SEED_OK")
print(summary)
print("ADMIN_LOGIN= admin_test / admin12345")
print("DOCTOR_LOGIN= doc_alain / doctor12345")
print("DOCTOR_LOGIN= doc_brenda / doctor12345")
print("DOCTOR_LOGIN= doc_charles / doctor12345")
print("DOCTOR_LOGIN= doc_diane / doctor12345")
print(f"CURRENT_SLOT= {current_slot_start.strftime('%H:%M')}")
print(f"SERVICE_DAY= {service_day_label}")
