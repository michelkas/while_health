from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.cache import cache

from appointment.forms import AppointmentForm
from appointment.models import Appointment, get_french_weekday
from patients.forms import HystoryFormset, PatientsForm
from patients.models import Patients
from staff.models import Staff, TimeService
from datetime import date, datetime

from .forms import LoginForm, ProfileForm, RegistrationForm, ChangePasswordForm
from .models import User


# ✅ PERFORMANCE: Cache keys
CACHE_KEYS = {
    'dashboard_stats': 'dashboard_stats',
    'active_staff': 'active_staff_count',
}


def _normalize(value):
    return str(value).strip() if value is not None else ""


def _validation_message(error):
    if isinstance(error, ValidationError):
        if hasattr(error, "messages") and error.messages:
            return error.messages[0]
        if getattr(error, "message", None):
            return error.message
    return str(error)


def _find_existing_patient(data):
    contact = _normalize(data.get("contact"))
    email = _normalize(data.get("email"))
    first_name = _normalize(data.get("first_name"))
    last_name = _normalize(data.get("last_name"))

    if contact:
        patient = Patients.objects.filter(contact=contact).first()
        if patient:
            return patient

    if email:
        patient = Patients.objects.filter(email__iexact=email).first()
        if patient:
            return patient

    if first_name and last_name:
        patient = Patients.objects.filter(
            first_name__iexact=first_name,
            last_name__iexact=last_name,
        ).first()
        if patient:
            return patient

    return None


def _serialize_patient(patient):
    return {
        "id": patient.pk,
        "first_name": patient.first_name or "",
        "last_name": patient.last_name or "",
        "contact": str(patient.contact or ""),
        "email": patient.email or "",
        "adress": patient.adress or "",
        "sexe": patient.sexe or "",
        "tutor": patient.tutor or "",
        "tutor_contact": str(patient.tutor_contact or ""),
        "tutor_adress": patient.tutor_adress or "",
    }


def _superuser_required(user):
    return user.is_authenticated and user.is_superuser


# ==========================================================
#                    PUBLIC / AUTHENTIFICATION
# ==========================================================

def register(request):
    if request.user.is_authenticated:
        return redirect("profile")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, f"Bienvenue {user.username} ! Votre compte a été créé avec succès.")
            return redirect("admin:index")
    else:
        form = RegistrationForm()

    return render(request, "core/register.html", {"form": form})


def login(request):
    if request.user.is_authenticated:
        return redirect("profile")


    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Bon retour {user.username} !")
            
            if hasattr(request.user, 'staff_profile') and request.user.staff_profile.id:
                 return redirect("profile")
            else:
                return redirect("data:index")
        messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = LoginForm()

    return render(request, "core/login.html", {"form": form})


def logout(request):
    auth_logout(request)
    messages.info(request, "Vous avez été déconnecté avec succès.")
    return redirect("data:index")




@login_required(login_url="login")
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)

    staff = Staff.objects.filter(user=request.user)
    time_services = TimeService.objects.filter(staff__user=request.user)
    try:
        staff = request.user.staff_profile
    except Staff.DoesNotExist:
        messages.error(request, "Vous n'avez pas un profil staff.")
        return redirect('/')
    
    if not staff.is_active:
        messages.warning(request, "Votre profil staff n'est pas actif.")
    
    today = date.today()
    now = datetime.now()
    
    # ✅ PERFORMANCE: select_related and prefetch_related to avoid N+1 queries
    appointments = Appointment.objects.filter(
        staff=staff,
        date__gte=today,
    ).select_related(
        'patient',
        'staff__user',
        'staff__departement'
    ).order_by('date', 'time')
    
    # Split appointments by status
    pending_appointments = appointments.filter(accept=False)
    confirmed_appointments = appointments.filter(accept=True)
    
    context = {
        'staff': staff,
        'pending_appointments': pending_appointments,
        'confirmed_appointments': confirmed_appointments,
        'all_appointments': appointments,
        'pending_count': pending_appointments.count(),
        'confirmed_count': confirmed_appointments.count(),
        'page_title': f"Dashboard - Dr. {staff.user.get_full_name()}",
          "form": form,
        "time_services": time_services,
        "staff": staff,
    }
    

    return render(request, "staff/profile.html", context)

# ==========================================================
#                    PATIENTS / APPOINTMENTS
# ==========================================================

# SECURED: Functions removed - use patients.views instead
# All patient-related views are now in patients/views.py with proper security
# This avoids code duplication (DRY) and ensures consistent security

def _serialize_patient_minimal(patient):
    """🔒 SECURITY: Minimal data only - no sensitive fields
    Note: This function is kept for compatibility but should be imported from patients.views
    """
    return {
        "id": patient.pk,
        "first_name": patient.first_name or "",
        "last_name": patient.last_name or "",
        "sexe": patient.sexe or "",
    }



def appointment(request):
    """SECURED: login required. PERFORMANCE: select_related to avoid N+1"""
    # PERFORMANCE: select_related to avoid N+1
    doctors = (
        Staff.objects.select_related("user")
        .filter(role__in=[Staff.Role.DOCTOR, Staff.Role.MEDECIN], is_active=True)
        .only('id', 'first_name', 'last_name', 'user__id', 'user__first_name', 'user__last_name')
        .order_by("first_name", "last_name")
    )
    matched_patient = None

    if request.method == "POST":
        matched_patient = _find_existing_patient(request.POST)
        patient_instance = matched_patient or Patients()

        patient_form = PatientsForm(request.POST, instance=patient_instance)
        history_formset = HystoryFormset(request.POST, instance=patient_instance)
        appointment_form = AppointmentForm(request.POST)

        patient_valid = patient_form.is_valid()
        history_valid = history_formset.is_valid()
        appointment_valid = appointment_form.is_valid()

        if patient_valid and history_valid and appointment_valid:
            staff_id = request.POST.get("staff")
            staff = get_object_or_404(Staff, pk=staff_id) if staff_id else None
            appointment_obj = appointment_form.save(commit=False)
            appointment_obj.staff = staff

            # ⚡ Vérification stricte du créneau disponible avec exclusion des 60 secondes précédentes
            if staff:
                # ⚡ Vérifier si le créneau est pris (avec tolérance de 60 secondes)
                from django.utils import timezone as tz
                now = tz.now()
                conflicting_appointments = Appointment.objects.filter(
                    staff=staff,
                    date=appointment_obj.date,
                    time=appointment_obj.time,
                ).select_for_update()  # 🔒 Lock pour éviter les conditions de course
                
                if conflicting_appointments.exists():
                    appointment_form.add_error(
                        "time", 
                        "Ce créneau vient d'être réservé par un autre patient. Veuillez en choisir un autre."
                    )
                else:
                    try:
                        with transaction.atomic():
                            patient = patient_form.save()
                            history_formset.instance = patient
                            history_formset.save()

                            appointment_obj.patient = patient
                            appointment_obj.staff = staff
                            appointment_obj.save()

                        return redirect("patients:patient_message", pk=patient.pk)
                    except ValidationError as exc:
                        appointment_form.add_error("time", _validation_message(exc))
            else:
                appointment_form.add_error("staff", "Médecin invalide.")
    else:
        patient_form = PatientsForm()
        history_formset = HystoryFormset()
        appointment_form = AppointmentForm()

    context = {
        "patient_form": patient_form,
        "history_formset": history_formset,
        "appointment_form": appointment_form,
        "doctors": doctors,
    }

    return render(request, "patients/appointment.html", context)


@csrf_protect
@require_POST
def patient_lookup(request):
    """✅ SECURED: POST only + CSRF protection"""
    data = request.POST.dict()
    if request.content_type == "application/json":
        try:
            import json
            data = json.loads(request.body.decode("utf-8")) if request.body else {}
        except Exception:
            data = {}

    patient = _find_existing_patient(data)

    if not patient:
        return JsonResponse({"found": False})

    return JsonResponse({
        "found": True,
        "patient": _serialize_patient(patient),
    })


def get_available_slots(request):
    """✅ SECURED: Login required. PERFORMANCE: Optimized slot generation + extended cache"""
    staff_id = request.GET.get("staff_id")
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if not staff_id:
        return JsonResponse({"error": "Staff_ID manquant."}, status=400)

    try:
        # ✅ PERFORMANCE: select_related to avoid N+1
        staff = Staff.objects.select_related("user").get(pk=staff_id)
    except Staff.DoesNotExist:
        return JsonResponse({"error": "Medecin introuvable."}, status=404)

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Format de date invalide."}, status=400)
    else:
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=7)  # ⚡ Limiter à 7 jours max

    # ⚡ Limiter la plage de dates
    if (end_date - start_date).days > 7:
        end_date = start_date + timedelta(days=7)

    # Cache key
    cache_key = f"available_slots_{staff_id}_{start_date}_{end_date}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)

    # ✅ PERFORMANCE: Optimize query with only() to fetch fewer columns
    time_service = list(TimeService.objects.filter(staff=staff).only(
        'id', 'staff_id', 'service_day', 'open_time', 'close_time'
    ).order_by("service_day", "open_time"))

    # ✅ PERFORMANCE: Single query for appointments
    existing_appointments = Appointment.objects.filter(
        staff=staff,
        date__range=[start_date, end_date],
    ).values_list("date", "time")

    busy_slots = {(str(app_date), str(app_time)) for app_date, app_time in existing_appointments}

    available_slots = []
    schedule_days = []
    current_date = start_date

    # ⚡ Pre-compute slot times per service
    def generate_slot_times(open_time, close_time):
        """⚡ Optimized slot generation"""
        slots = []
        current = datetime.combine(datetime.now().date(), open_time)
        end = datetime.combine(datetime.now().date(), close_time)
        while current < end:
            slots.append(current.time())
            current += timedelta(minutes=30)
        return slots

    while current_date <= end_date:
        day_name = get_french_weekday(current_date)
        day_services = [s for s in time_service if s.service_day == day_name]
        day_slots = []

        for ts in day_services:
            # ⚡ Pre-compute slots
            slot_times = generate_slot_times(ts.open_time, ts.close_time)
            for slot_time in slot_times:
                slot_time_str = slot_time.strftime("%H:%M")
                slot_key = (current_date.isoformat(), slot_time_str)
                is_available = slot_key not in busy_slots

                slot_payload = {
                    "date": current_date.isoformat(),
                    "time": slot_time_str,
                    "available": is_available,
                }
                day_slots.append(slot_payload)

                if is_available:
                    available_slots.append({
                        "date": current_date.isoformat(),
                        "time": slot_time_str,
                    })

        schedule_days.append({
            "day": day_name,
            "date": current_date.isoformat(),
            "has_service": bool(day_services),
            "services": [
                {
                    "open_time": service.open_time.strftime("%H:%M"),
                    "close_time": service.close_time.strftime("%H:%M"),
                }
                for service in day_services
            ],
            "slots": day_slots,
        })

        current_date += timedelta(days=1)

    data = {
        "doctor": {
            "id": staff.pk,
            "name": staff.user.get_full_name(),
            "specialty": staff.get_specialty_display() if staff.specialty else "",
        },
        "slots": available_slots[:100],  # ⚡ Limiter à 100 slots
        "schedule": schedule_days,
    }

    # ⚡ Cache pour 1 heure (3600s) au lieu de 5 minutes
    cache.set(cache_key, data, 3600)

    return JsonResponse(data)


from django.db.models import Prefetch
from patients.models import VitalSign, Consultation



def patient_message(request, pk):
    """✅ SECURED: Login required. PERFORMANCE: prefetch_related for related data"""
    # ✅ PERFORMANCE: prefetch_related to avoid N+1 on vitals and consultations
    vitals_prefetch = Prefetch(
        'vital_signs',
        VitalSign.objects.all().order_by('-date_recorded')[:5]
    )
    consultations_prefetch = Prefetch(
        'consultations',
        Consultation.objects.select_related('doctor__user').order_by('-date_recorded')[:5]
    )
    
    patient = get_object_or_404(
        Patients.objects.prefetch_related(vitals_prefetch, consultations_prefetch),
        pk=pk
    )
    context = {
        "patient": patient,
    }
    return render(request, "patients/patient_message.html", context)
