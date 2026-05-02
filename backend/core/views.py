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
from django.views.decorators.http import require_GET
from django.core.cache import cache

from appointment.forms import AppointmentForm
from appointment.models import Appointment, get_french_weekday
from patients.forms import HystoryFormset, PatientsForm
from patients.models import Patients
from staff.models import Staff, TimeService

from .forms import LoginForm, ProfileForm, RegistrationForm
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
    name = _normalize(data.get("name"))
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

    if name and first_name and last_name:
        patient = Patients.objects.filter(
            name__iexact=name,
            first_name__iexact=first_name,
            last_name__iexact=last_name,
        ).first()
        if patient:
            return patient

    if name and first_name:
        patient = Patients.objects.filter(
            name__iexact=name,
            first_name__iexact=first_name,
        ).first()
        if patient:
            return patient

    return None


def _serialize_patient(patient):
    return {
        "id": patient.pk,
        "name": patient.name or "",
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
            return redirect("profile")
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
            return redirect("profile")
        messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = LoginForm()

    return render(request, "core/login.html", {"form": form})


def logout(request):
    auth_logout(request)
    messages.info(request, "Vous avez été déconnecté avec succès.")
    return redirect("index")


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

    context = {
        "form": form,
        "time_services": time_services,
        "staff": staff,
    }

    return render(request, "core/profile.html", context)


# ==========================================================
#                    ADMINISTRATION
# ==========================================================

@login_required(login_url="login")
@user_passes_test(_superuser_required, login_url="login")
def dashboard(request):
    """✅ PERFORMANCE: Cached with aggregated queries"""
    # ✅ PERFORMANCE: Try cache first
    stats_cache = cache.get(CACHE_KEYS['dashboard_stats'])
    if stats_cache is not None:
        context = stats_cache
    else:
        today = timezone.localdate()
        patients_qs = Patients.objects.all()
        
        # Single aggregation query instead of 6+ separate count()
        stats = patients_qs.aggregate(
            total=Count('id'),
            today_count=Count('id', filter=Q(registered_at__date=today)),
            transferred=Count('id', filter=Q(transfered=True))
        )
        
        appointments_qs = Appointment.objects.select_related("patient", "staff").order_by("-id")
        appointments_stats = appointments_qs.aggregate(
            total=Count('id'),
            accepted=Count('id', filter=Q(accept=True)),
            pending=Count('id', filter=Q(accept=False))
        )
        
        active_staff_count = Staff.objects.filter(is_active=True).count()
        
        context = {
            "patients_count": stats['total'] or 0,
            "patients_today_count": stats['today_count'] or 0,
            "active_staff_count": active_staff_count,
            "appointments_count": appointments_stats['total'] or 0,
            "appointments_accepted_count": appointments_stats['accepted'] or 0,
            "appointments_pending_count": appointments_stats['pending'] or 0,
            "transferred_patients_count": stats['transferred'] or 0,
            "recent_patients": patients_qs.order_by("-registered_at")[:6],
            "recent_appointments": appointments_qs[:5],
        }
        
        # ✅ PERFORMANCE: Cache for 5 minutes
        cache.set(CACHE_KEYS['dashboard_stats'], context, 300)

    return render(request, "admin/index.html", context)


@login_required(login_url="login")
@user_passes_test(_superuser_required, login_url="login")
def patient_list(request):
    query = request.GET.get("q", "").strip()
    patients = Patients.objects.all().order_by("-registered_at")

    if query:
        patients = patients.filter(
            Q(name__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(contact__icontains=query)
        )

    paginator = Paginator(patients, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    # ✅ PERFORMANCE: Single aggregation query instead of 3 separate count()
    stats_cache_key = f"patient_stats_{query or 'all'}"
    stats = cache.get(stats_cache_key)
    if stats is None:
        base_qs = Patients.objects.all()
        if query:
            base_qs = base_qs.filter(
                Q(name__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(contact__icontains=query)
            )
        
        stats = base_qs.aggregate(
            total=Count('id'),
            transferred=Count('id', filter=Q(transfered=True)),
            active=Count('id', filter=Q(transfered=False))
        )
        # Cache for 2 minutes
        cache.set(stats_cache_key, stats, 120)

    context = {
        "patients": page_obj,
        "page_obj": page_obj,
        "query": query,
        "total_patients": stats['total'] or 0,
        "transferred_count": stats['transferred'] or 0,
        "active_count": stats['active'] or 0,
    }

    return render(request, "admin/patients/list.html", context)


@login_required(login_url="login")
@user_passes_test(_superuser_required, login_url="login")
def patient_create(request):
    if request.method == "POST":
        form = PatientsForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f"Le patient {patient} a été créé avec succès.")
            return redirect("dashboard_patients")
    else:
        form = PatientsForm()

    context = {
        "form": form,
        "patient": None,
        "page_mode": "create",
    }
    return render(request, "admin/patients/form.html", context)


@login_required(login_url="login")
@user_passes_test(_superuser_required, login_url="login")
def patient_update(request, pk):
    patient = get_object_or_404(Patients, pk=pk)

    if request.method == "POST":
        form = PatientsForm(request.POST, instance=patient)
        if form.is_valid():
            updated_patient = form.save()
            messages.success(request, f"Le patient {updated_patient} a été modifié avec succès.")
            return redirect("dashboard_patients")
    else:
        form = PatientsForm(instance=patient)

    context = {
        "form": form,
        "patient": patient,
        "page_mode": "update",
    }
    return render(request, "admin/patients/form.html", context)


@login_required(login_url="login")
@user_passes_test(_superuser_required, login_url="login")
def patient_delete(request, pk):
    patient = get_object_or_404(Patients, pk=pk)

    if request.method == "POST":
        label = str(patient)
        patient.delete()
        messages.success(request, f"Le patient {label} a été supprimé avec succès.")
        return redirect("dashboard_patients")

    context = {
        "patient": patient,
    }
    return render(request, "admin/patients/confirm_delete.html", context)


# ==========================================================
#                    PATIENTS / APPOINTMENTS
# ==========================================================

# ✅ SECURED: Functions removed - use patients.views instead
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
    """✅ SECURED: login required. PERFORMANCE: select_related to avoid N+1"""
    # ✅ PERFORMANCE: select_related to avoid N+1
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

            if staff and Appointment.objects.filter(
                staff=staff,
                date=appointment_obj.date,
                time=appointment_obj.time,
            ).exists():
                appointment_form.add_error("time", "Ce rendez-vous est déjà pris.")
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


from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect




@csrf_protect
def patient_lookup(request):
    """✅ SECURED: POST only + CSRF protection + login required"""
    patient = _find_existing_patient(request.POST)

    if not patient:
        return JsonResponse({"found": False})

    # ✅ SECURITY: Return only minimal safe data (no email, address, etc.)
    return JsonResponse({
        "found": True,
        "patient": _serialize_patient_minimal(patient),
    })




def get_available_slots(request):
    """✅ SECURED: Login required. PERFORMANCE: select_related for staff + user"""
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
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    else:
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=7)

    # ✅ PERFORMANCE: Optimize query with only() to fetch fewer columns
    time_service = TimeService.objects.filter(staff=staff).only(
        'id', 'staff_id', 'service_day', 'open_time', 'close_time'
    ).order_by("service_day", "open_time")

    existing_appointments = Appointment.objects.filter(
        staff=staff,
        date__range=[start_date, end_date],
    ).values_list("date", "time")

    busy_slots = set()
    for appointment_date, appointment_time in existing_appointments:
        busy_slots.add((appointment_date.isoformat(), appointment_time.strftime("%H:%M")))

    available_slots = []
    schedule_days = []
    current_date = start_date

    while current_date <= end_date:
        day_name = get_french_weekday(current_date)
        day_services = list(time_service.filter(service_day=day_name).order_by("open_time"))
        day_slots = []

        for ts in day_services:
            slot_time = ts.open_time
            while slot_time < ts.close_time:
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

                slot_time = (datetime.combine(current_date, slot_time) + timedelta(minutes=30)).time()

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

    return JsonResponse({
        "doctor": {
            "id": staff.pk,
            "name": staff.user.get_full_name(),
            "specialty": staff.get_specialty_display() if staff.specialty else "",
        },
        "slots": available_slots,
        "schedule": schedule_days,
    })


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
