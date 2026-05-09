from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from .models import Hero, About, Service, Emergency, EmergencyInfo
from staff.models import Departement, Staff
from appointment.models import Appointment
from django.db.models import Q
from django.utils import timezone
import random

def index(request):
    now = timezone.localtime()
    today = now.date()
    current_time = now.time()

    doctors = list(
        Staff.objects.select_related('user', 'departement')
        .filter(Q(is_active=True) & Q(is_verified=True))
    )

    current_appointments = Appointment.objects.filter(
        staff__in=doctors,
        date=today,
        accept=True
    ).select_related('staff')

    busy_doctor_ids = set()
    for appointment in current_appointments:
        appointment_start = appointment.time
        appointment_end = (
            timezone.datetime.combine(today, appointment_start) + timedelta(minutes=30)
        ).time()

        if appointment_start <= current_time < appointment_end:
            busy_doctor_ids.add(appointment.staff_id)

    for doctor in doctors:
        is_busy = doctor.id in busy_doctor_ids
        doctor.status_label = (
            doctor.departement.name
            if is_busy and doctor.departement
            else 'Occupé' if is_busy else 'LIBRE'
        )
        doctor.status_badge_class = 'badge-busy' if is_busy else 'badge-available'

    icon_emergence = random.choice(["bi bi-hospital", "bi bi-headset","bi bi-heart-pulse", "bi bi-shield-plus","bi bi-activity",]) 
    context = {
        "hero":Hero.objects.only('title', 'subtitle', 'description', 'image').first(),
        "about":About.objects.only('title', 'subtitle', 'year', 'goal', 'location', 'description', 'image', 'compassionate_care', 'care_quality').first(),
        "services":Service.objects.only('title', 'departement', 'description', 'icon', 'short_description').all(),
        "departements3":Departement.objects.only('name', 'description')[:3],
        # ✅ PERFORMANCE: Paginate departments (limit to 10 for homepage)
        "departements":Departement.objects.all()[:10],
        "emergency":Emergency.objects.only('title', 'description', 'phone').first(),
        "emergency_info": EmergencyInfo.objects.only('title', 'phone', 'address', 'operation_time'), 
        'doctors': doctors,
        'icon_emergence': icon_emergence,
    }
    return render(request, 'index.html',context)


def about_detail(request):
    """
    Vue de détail pour la page À propos (About).
    Affiche toutes les informations sur l'hôpital/clinique.
    """
    about = About.objects.first()
    context = {
        "about": about,
        "page_title": "À propos - " + (about.title if about else "While Health"),
    }
    return render(request, 'data/about_detail.html', context)


def service_detail(request, service_id):
    """
    Vue de détail pour un service médical spécifique.
    Affiche les informations complètes d'un service.
    """
    service = get_object_or_404(Service, pk=service_id)
    related_services = Service.objects.filter(departement=service.departement).exclude(pk=service_id)[:4]
    staff_in_service = Staff.objects.filter(departement=service.departement, is_active=True, is_verified=True)[:4]
    
    context = {
        "service": service,
        "related_services": related_services,
        "staff_in_service": staff_in_service,
        "page_title": f"{service.title} - While Health",
    }
    return render(request, 'data/service_detail.html', context)
