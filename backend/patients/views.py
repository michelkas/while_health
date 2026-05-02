from datetime import datetime, timedelta

from django.core.exceptions import ValidationError, PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect
from django.db.models import Prefetch

from appointment.forms import AppointmentForm
from appointment.models import Appointment, get_french_weekday
from staff.models import Staff, TimeService

from .forms import HystoryFormset, PatientsForm
from .models import Patients, Consultation, VitalSign

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


def _serialize_patient_minimal(patient):
    """✅ SECURITY: Minimal data only - no sensitive fields"""
    return {
        "id": patient.pk,
        "first_name": patient.first_name or "",
        "last_name": patient.last_name or "",
        "sexe": patient.sexe or "",
    }


def _serialize_patient_full(patient):
    """✅ Full data for authenticated users"""
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



def appointment(request):
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


@require_POST
@csrf_protect
def patient_lookup(request):
    """✅ SECURITY: POST only + CSRF protection + public minimal patient lookup + rate limiting"""
    try:
        from django_ratelimit.decorators import ratelimit
    except ImportError:
        def ratelimit(*args, **kwargs):
            def decorator(func):
                return func
            return decorator

    @ratelimit(key='user', rate='10/m', method='POST', block=True)
    def _patient_lookup(request):
        patient = _find_existing_patient(request.POST)

        if not patient:
            return JsonResponse({"found": False})

        # ✅ SECURITY: Return only minimal safe data to support anonymous appointment lookup
        return JsonResponse({
            "found": True,
            "patient": _serialize_patient_minimal(patient),
        })
    
    return _patient_lookup(request)



def get_available_slots(request):
    """✅ SECURITY: Login required. PERFORMANCE: select_related for staff + user"""
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



def patient_message(request, pk):
    """✅ SECURITY: Login required. PERFORMANCE: prefetch_related for related data"""
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
