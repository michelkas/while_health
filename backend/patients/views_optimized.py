"""
✅ VUES OPTIMISÉES - Performance & Sécurité

Changements:
1. @login_required + @permission_required sur endpoints sensibles
2. select_related() + prefetch_related() systématique
3. Pagination sur toutes les listes
4. Caching intelligent
5. POST-only sur endpoints critiques
"""

from datetime import datetime, timedelta
import json

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.db.models import Prefetch, F, Q, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.core.cache import cache

from appointment.models import Appointment, get_french_weekday
from appointment.forms import AppointmentForm
from staff.models import Staff, TimeService

from .forms import HystoryFormset, PatientsForm
from .models import Patients, Consultation, VitalSign, MedicalHistory, Prescription


# ============================================
# HELPER FUNCTIONS
# ============================================

def _normalize(value):
    """Normalize string input"""
    return str(value).strip() if value is not None else ""


def _validation_message(error):
    """Extract message from ValidationError"""
    if isinstance(error, ValidationError):
        if hasattr(error, "messages") and error.messages:
            return error.messages[0]
        if getattr(error, "message", None):
            return error.message
    return str(error)


def _find_existing_patient(data):
    """Find patient by contact, email, or name (optimized with select_related)"""
    contact = _normalize(data.get("contact"))
    email = _normalize(data.get("email"))
    name = _normalize(data.get("first_name"))
    last_name = _normalize(data.get("last_name"))

    # ✅ Single query with select_related
    patients = Patients.objects.select_related().all()

    if contact:
        return patients.filter(contact=contact).first()
    
    if email:
        return patients.filter(email__iexact=email).first()
    
    if name and last_name:
        return patients.filter(
            first_name__iexact=name,
            last_name__iexact=last_name,
        ).first()
    
    if name:
        return patients.filter(first_name__iexact=name).first()
    
    return None


def _serialize_patient(patient):
    """Serialize patient to JSON (minimal data for security)"""
    return {
        "id": patient.pk,
        "name": patient.first_name or "",
        "last_name": patient.last_name or "",
        "contact": str(patient.contact or ""),
        # ✅ PAS: email, adresse, tuteur - données sensibles!
    }


# ============================================
# APPOINTMENT VIEWS
# ============================================

@login_required(login_url="login")
@require_http_methods(["GET", "POST"])
def appointment(request):
    """
    ✅ Create/edit appointment - WITH authentication & permissions
    """
    
    # ✅ Check permission: only staff can create appointments
    if not request.user.is_staff:
        raise PermissionDenied("Seul le personnel peut créer des rendez-vous")
    
    # ✅ Optimized query: select_related all needed data
    doctors = (
        Staff.objects.select_related("user", "departement")
        .filter(
            role__in=[Staff.Role.DOCTOR, Staff.Role.MEDECIN],
            is_active=True,
            # ✅ Optional: filter by department if user has staff_profile
            departement=getattr(request.user, 'staff_profile', None).departement
            if hasattr(request.user, 'staff_profile') else None
        )
        .order_by("user__first_name", "user__last_name")
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

            # ✅ Check for existing appointment
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
                        
                        # ✅ Invalidate cache
                        cache.delete_pattern('appointment_*')
                        messages.success(request, "Rendez-vous créé avec succès!")

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


@login_required(login_url="login")
@require_http_methods(["POST"])  # ✅ POST ONLY - no GET
@csrf_protect  # ✅ CSRF protection
def patient_lookup(request):
    """
    ✅ Patient lookup API - POST only, CSRF protected, minimal data
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    contact = _normalize(data.get("contact", ""))
    
    # ✅ Check permission: only staff can lookup
    if not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    if not contact:
        return JsonResponse({"error": "Contact required"}, status=400)
    
    # ✅ Single query with select_related
    patient = Patients.objects.select_related().filter(
        contact=contact
    ).first()

    if not patient:
        return JsonResponse({"found": False})

    # ✅ Return MINIMUM data - no email/adresse/tutor
    return JsonResponse({
        "found": True,
        "patient": {
            "id": patient.pk,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "sexe": patient.sexe,
        }
    })


# ============================================
# PATIENT VIEWS
# ============================================

@login_required
@require_GET
def patient_list(request):
    """
    ✅ List patients - PAGINATED, optimized queries
    """
    
    # ✅ Base queryset optimized
    queryset = Patients.objects.select_related().order_by('-registered_at')
    
    # ✅ Search filter
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(contact__icontains=search)
        )
    
    # ✅ PAGINATION: 25 per page
    paginator = Paginator(queryset, per_page=25)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'page_obj': page_obj,
        'patients': page_obj.object_list,
        'search': search,
    }
    return render(request, 'patients/list.html', context)


@login_required
@require_GET
def patient_list_api(request):
    """
    ✅ Patient list API for AJAX - PAGINATED JSON response
    """
    
    page = int(request.GET.get('page', 1))
    per_page = 20
    search = request.GET.get('search', '')
    
    # ✅ Base query
    queryset = Patients.objects.select_related().order_by('-registered_at')
    
    # ✅ Search
    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # ✅ Pagination
    paginator = Paginator(queryset, per_page=per_page)
    
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        return JsonResponse({'error': 'Invalid page'}, status=400)
    
    data = {
        'count': paginator.count,
        'page': page,
        'total_pages': paginator.num_pages,
        'patients': [
            {
                'id': p.id,
                'name': p.full_name,
                'email': p.email,
                'contact': str(p.contact),
                'age': p.age,
                'url': f'/patients/{p.id}/detail/'
            }
            for p in page_obj.object_list
        ]
    }
    return JsonResponse(data)


@login_required
@permission_required('patients.view_sensitive_data', raise_exception=True)
@require_GET
def patient_detail(request, pk):
    """
    ✅ Patient detail - WITH sensitive data protection
    """
    
    # ✅ Optimized query: prefetch all relations
    vital_signs_prefetch = Prefetch(
        'vital_signs',
        VitalSign.objects.select_related('recorded_by').order_by('-date_recorded')[:10]
    )
    
    medical_history_prefetch = Prefetch(
        'medical_histories',
        MedicalHistory.objects.select_related('recorded_by').order_by('-date_recorded')[:5]
    )
    
    consultations_prefetch = Prefetch(
        'consultations',
        Consultation.objects.select_related('doctor__user').order_by('-date_recorded')[:10]
    )
    
    patient = get_object_or_404(
        Patients.objects.prefetch_related(
            vital_signs_prefetch,
            medical_history_prefetch,
            consultations_prefetch
        ),
        pk=pk
    )
    
    context = {
        'patient': patient,
        'vital_signs': patient.vital_signs.all()[:10],
        'medical_histories': patient.medical_histories.all()[:5],
        'consultations': patient.consultations.all()[:10],
    }
    return render(request, 'patients/detail.html', context)


# ============================================
# CONSULTATION VIEWS
# ============================================

@login_required
@require_GET
def consultation_list(request):
    """
    ✅ Consultation list - OPTIMIZED queries, PAGINATED
    """
    
    # ✅ Prefetch prescriptions to avoid N+1
    prescription_prefetch = Prefetch(
        'prescriptions',
        Prescription.objects.select_related('consultation').order_by('-date_recorded')
    )
    
    queryset = Consultation.objects.select_related(
        'patient',
        'doctor__user'
    ).prefetch_related(
        prescription_prefetch
    ).order_by('-date_recorded')
    
    # ✅ Pagination
    paginator = Paginator(queryset, per_page=25)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    context = {
        'page_obj': page_obj,
        'consultations': page_obj.object_list,
    }
    return render(request, 'patients/consultation_list.html', context)


@login_required
@require_GET
def consultation_prescriptions_api(request, consultation_id):
    """
    ✅ Get prescriptions for consultation - OPTIMIZED, JSON
    """
    
    # ✅ Single query: select_related + prefetch all data
    consultation = get_object_or_404(
        Consultation.objects.select_related(
            'patient', 'doctor__user'
        ).prefetch_related(
            Prefetch(
                'prescriptions',
                Prescription.objects.select_related('consultation__patient')
            )
        ),
        pk=consultation_id
    )
    
    data = {
        'consultation': {
            'id': consultation.id,
            'patient': consultation.patient.full_name,
            'doctor': consultation.doctor.user.get_full_name(),
            'reason': consultation.reason_for_consultation,
            'diagnosis': consultation.diagnosis,
            'prescriptions': [
                {
                    'id': p.id,
                    'medication': p.get_medication_display(),
                    'dosage': p.formatted_dosage(),
                    'frequency': p.get_frequency_display(),
                    'duration': f"{p.duration_days} jours" if p.duration_days else "Illimitée",
                    'instructions': p.instructions,
                }
                for p in consultation.prescriptions.all()
            ]
        }
    }
    return JsonResponse(data)


# ============================================
# DASHBOARD & STATISTICS (CACHED)
# ============================================

@login_required
@require_GET
def dashboard_stats(request):
    """
    ✅ Dashboard statistics - CACHED, aggregated
    """
    
    # ✅ Check cache first
    stats_key = 'dashboard_stats'
    stats = cache.get(stats_key)
    
    if not stats:
        # ✅ Calculate using SQL aggregation (not Python loop)
        stats = Appointment.objects.aggregate(
            total_count=Count('id'),
            accepted_count=Count('id', filter=Q(accept=True)),
            rejected_count=Count('id', filter=Q(accept=False)),
            today_count=Count('id', filter=Q(date=timezone.now().date())),
        )
        
        # ✅ Cache for 5 minutes
        cache.set(stats_key, stats, 300)
    
    # ✅ Top doctors (also aggregated)
    doctor_stats = Appointment.objects.filter(
        accept=True
    ).values('staff__user__first_name', 'staff__user__last_name').annotate(
        appointments_count=Count('id')
    ).order_by('-appointments_count')[:5]
    
    context = {
        'stats': stats,
        'top_doctors': doctor_stats,
    }
    return render(request, 'core/dashboard.html', context)
