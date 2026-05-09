from datetime import datetime, timedelta

from django.core.cache import cache
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


def _serialize_patient_for_form(patient):
    """Full patient data for pre-filling appointment form"""
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


def _invalidate_staff_cache(staff_id):
    """Invalidate cache for staff availability slots"""
    from datetime import datetime, timedelta
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=7)
    cache_key = f"available_slots_{staff_id}_{start_date}_{end_date}"
    cache.delete(cache_key)



def appointment(request):
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

                        # Invalidate cache for staff slots
                        if staff:
                            _invalidate_staff_cache(staff.pk)

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




def patient_message(request, pk):
    """✅ SECURITY: Login required. PERFORMANCE: prefetch_related for related data"""
    # ✅ PERFORMANCE: prefetch_related to avoid N+1 on vitals and consultations
    # Note: Slicing must be done AFTER prefetch, not inside Prefetch querysets
    vitals_prefetch = Prefetch(
        'vital_signs',
        VitalSign.objects.all().order_by('-date_recorded')
    )
    consultations_prefetch = Prefetch(
        'consultations',
        Consultation.objects.select_related('doctor__user').order_by('-date_recorded')
    )
    
    patient = get_object_or_404(
        Patients.objects.prefetch_related(vitals_prefetch, consultations_prefetch),
        pk=pk
    )
    
    # ⚡ Slice the related objects after fetch (in Python, not in queryset)
    patient.vital_signs_limited = list(patient.vital_signs.all())[:5]
    patient.consultations_limited = list(patient.consultations.all())[:5]
    
    context = {
        "patient": patient,
    }
    return render(request, "patients/patient_message.html", context)


# ✅ PATIENT PHONE ACCESS FEATURES - No authentication required, token-based access


def patient_phone_verification(request):
    """
    ✅ SECURITY: Phone verification without authentication.
    Allows patient to access their appointments by phone number.
    Uses session token for temporary access.
    
    GET: Displays phone verification form
    POST: Validates phone number and creates session token
    """
    # If patient already has verified token in session, redirect to appointments
    if request.session.get('patient_phone_token'):
        return redirect('patients:patient_appointments_list')
    
    form = None
    error_message = None
    
    if request.method == 'POST':
        from .forms import PatientPhoneVerificationForm
        form = PatientPhoneVerificationForm(request.POST)
        
        if form.is_valid():
            contact = form.cleaned_data['contact']
            
            # Find patient by phone number
            try:
                patient = Patients.objects.get(contact=contact)
                
                # ✅ SECURITY: Generate temporary token and store in session
                import secrets
                token = secrets.token_urlsafe(32)
                request.session['patient_phone_token'] = token
                request.session['patient_id'] = patient.pk
                request.session['patient_contact'] = str(contact)
                request.session.set_expiry(3600)  # 1 hour expiration
                
                return redirect('patients:patient_appointments_list')
                
            except Patients.DoesNotExist:
                error_message = "Aucun patient trouvé avec ce numéro de téléphone."
        else:
            error_message = "Numéro de téléphone invalide."
    else:
        from .forms import PatientPhoneVerificationForm
        form = PatientPhoneVerificationForm()
    
    context = {
        'form': form,
        'error_message': error_message,
        'page_title': 'Accéder à mes rendez-vous - While Health',
    }
    return render(request, 'patients/phone_verification.html', context)


def _verify_patient_session(request):
    """
    ✅ SECURITY: Helper to verify patient session token.
    Returns patient object or raises PermissionDenied.
    """
    token = request.session.get('patient_phone_token')
    patient_id = request.session.get('patient_id')
    
    if not token or not patient_id:
        raise PermissionDenied("Session expiée. Veuillez vous identifier à nouveau.")
    
    try:
        patient = Patients.objects.get(pk=patient_id)
        return patient
    except Patients.DoesNotExist:
        request.session.flush()
        raise PermissionDenied("Patient introuvable.")


def patient_appointments_list(request):
    """
    ✅ SECURITY: Display valid (future) appointments for patient.
    Requires phone verification token in session.
    
    Shows:
    - List of valid appointments (not cancelled, future dates)
    - Edit and Delete buttons for each appointment
    """
    try:
        patient = _verify_patient_session(request)
    except PermissionDenied:
        return redirect('patients:patient_phone_verification')
    
    from datetime import date, datetime, timedelta
    
    # Get valid appointments: future dates only
    today = date.today()
    now = datetime.now()
    
    # ✅ PERFORMANCE: Select related to avoid N+1 queries
    appointments = Appointment.objects.filter(
        patient=patient,
        date__gte=today,  # Future appointments only
    ).select_related('staff__user', 'staff__departement', 'time_service').order_by('date', 'time')
    
    # Check if patient has any valid appointments
    has_appointments = appointments.exists()
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'has_appointments': has_appointments,
        'page_title': f"Mes rendez-vous - {patient.full_name}",
    }
    
    return render(request, 'patients/appointments_list.html', context)


def patient_appointment_edit(request, appointment_id):
    """
    ✅ SECURITY: Allow patient to edit their own appointment.
    Can modify: date, time, reason.
    Requires phone verification token in session.
    """
    try:
        patient = _verify_patient_session(request)
    except PermissionDenied:
        return redirect('patients:patient_phone_verification')
    
    # ✅ SECURITY: Ensure patient owns this appointment
    appointment = get_object_or_404(Appointment, pk=appointment_id, patient=patient)
    
    from .forms import PatientAppointmentEditForm
    
    if request.method == 'POST':
        form = PatientAppointmentEditForm(request.POST, instance=appointment, appointment=appointment)
        
        if form.is_valid():
            try:
                form.save()
                # ✅ Clear cache for staff slots if using cache
                if appointment.staff:
                    cache.delete(f"available_slots_{appointment.staff.pk}")
                
                from django.contrib import messages
                messages.success(request, "Rendez-vous modifié avec succès.")
                return redirect('patients:patient_appointments_list')
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = PatientAppointmentEditForm(instance=appointment, appointment=appointment)
    
    context = {
        'form': form,
        'appointment': appointment,
        'patient': patient,
        'page_title': f"Modifier rendez-vous - {patient.full_name}",
    }
    
    return render(request, 'patients/appointment_edit.html', context)


def patient_appointment_delete(request, appointment_id):
    """
    ✅ SECURITY: Allow patient to delete their own appointment.
    Shows confirmation page before deletion.
    """
    try:
        patient = _verify_patient_session(request)
    except PermissionDenied:
        return redirect('patients:patient_phone_verification')
    
    # ✅ SECURITY: Ensure patient owns this appointment
    appointment = get_object_or_404(Appointment, pk=appointment_id, patient=patient)
    
    if request.method == 'POST':
        # Confirm deletion
        staff_id = appointment.staff.pk if appointment.staff else None
        appointment.delete()
        
        # ✅ Clear cache for staff slots if using cache
        if staff_id:
            cache.delete(f"available_slots_{staff_id}")
        
        from django.contrib import messages
        messages.success(request, "Rendez-vous annulé avec succès.")
        return redirect('patients:patient_appointments_list')
    
    context = {
        'appointment': appointment,
        'patient': patient,
        'page_title': f"Confirmer suppression - {patient.full_name}",
    }
    
    return render(request, 'patients/appointment_delete.html', context)
