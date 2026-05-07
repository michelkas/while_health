from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib import messages
from django.db.models import Prefetch
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import date, datetime

from .models import Departement, Staff
from appointment.models import Appointment
from patients.models import Patients
from data.models import Service


def departement_detail(request, departement_id):
    """
    Vue de détail pour un département.
    Affiche toutes les informations sur un département ainsi que les services et membres du personnel associés.
    """
    departement = get_object_or_404(Departement, pk=departement_id)
    services = Service.objects.filter(departement=departement)
    staff_members = Staff.objects.filter(departement=departement, is_active=True, is_verified=True)
    
    context = {
        "departement": departement,
        "services": services,
        "staff_members": staff_members,
        "page_title": f"{departement.name} - While Health",
    }
    return render(request, 'staff/departement_detail.html', context)


def staff_profile_detail(request, staff_id):
    """
    Vue de détail pour le profil d'un membre du personnel.
    Affiche toutes les informations sur un membre du personnel médical ou administratif.
    Automatically displays schedule for appointment booking (public - no login required).
    """
    from django.urls import reverse
    
    staff = get_object_or_404(Staff, pk=staff_id)
    
    # Récupérer les services liés au département du staff
    related_services = []
    if staff.departement:
        related_services = Service.objects.filter(departement=staff.departement).exclude(
            title__icontains=staff.specialty or ""
        )[:4]
    
    context = {
        "staff": staff,
        "related_services": related_services,
        "page_title": f"Dr. {staff.user.get_full_name()} - While Health",
        "available_slots_url": reverse("patients:get_available_slots"),
    }
    return render(request, 'staff/staff_profile_detail.html', context)


# ✅ STAFF DASHBOARD - Authenticated staff only


@login_required
def staff_dashboard(request):
    """
    ✅ SECURITY: Staff dashboard - authenticated users only.
    
    Displays:
    - Staff member's schedule (upcoming appointments)
    - Pending confirmations
    - List of appointments to manage
    """
    
    # ✅ SECURITY: Ensure user has staff profile
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
    }
    
    return render(request, 'staff/dashboard.html', context)


@login_required
def staff_appointment_validate(request, appointment_id):
    """
    ✅ SECURITY: Staff validates/confirms appointment.
    Can modify date, time, reason and set accept=True.
    Sends email to patient when confirmed.
    
    Only staff member assigned to appointment can access.
    """
    
    try:
        staff = request.user.staff_profile
    except Staff.DoesNotExist:
        raise PermissionDenied("Vous n'avez pas un profil staff.")
    
    # ✅ SECURITY: Only assigned staff can modify
    appointment = get_object_or_404(
        Appointment,
        pk=appointment_id,
        staff=staff
    )
    
    from staff.forms import StaffAppointmentValidationForm
    
    if request.method == 'POST':
        form = StaffAppointmentValidationForm(request.POST, instance=appointment)
        
        if form.is_valid():
            try:
                old_accept = appointment.accept
                appointment = form.save()
                
                # ✅ Send confirmation email if accepting
                if appointment.accept and not old_accept:
                    _send_appointment_confirmation_email(appointment)
                    messages.success(request, "Rendez-vous confirmé et email envoyé au patient.")
                else:
                    messages.success(request, "Rendez-vous mis à jour.")
                
                return redirect('staff:staff_dashboard')
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = StaffAppointmentValidationForm(instance=appointment)
    
    context = {
        'form': form,
        'appointment': appointment,
        'staff': staff,
        'page_title': f"Valider Rendez-vous",
    }
    
    return render(request, 'staff/appointment_validate.html', context)


@login_required
def staff_appointment_edit(request, appointment_id):
    """
    ✅ SECURITY: Staff edits appointment details.
    Only assigned staff can modify.
    """
    
    try:
        staff = request.user.staff_profile
    except Staff.DoesNotExist:
        raise PermissionDenied("Vous n'avez pas un profil staff.")
    
    # ✅ SECURITY: Only assigned staff can modify
    appointment = get_object_or_404(
        Appointment,
        pk=appointment_id,
        staff=staff
    )
    
    from staff.forms import StaffAppointmentEditForm
    
    if request.method == 'POST':
        form = StaffAppointmentEditForm(request.POST, instance=appointment)
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Rendez-vous modifié avec succès.")
                return redirect('staff:staff_dashboard')
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = StaffAppointmentEditForm(instance=appointment)
    
    context = {
        'form': form,
        'appointment': appointment,
        'staff': staff,
        'page_title': f"Modifier Rendez-vous",
    }
    
    return render(request, 'staff/appointment_edit.html', context)


@login_required
def staff_appointment_delete(request, appointment_id):
    """
    ✅ SECURITY: Staff deletes appointment.
    Shows confirmation page before deletion.
    Only assigned staff can delete.
    """
    
    try:
        staff = request.user.staff_profile
    except Staff.DoesNotExist:
        raise PermissionDenied("Vous n'avez pas un profil staff.")
    
    # ✅ SECURITY: Only assigned staff can delete
    appointment = get_object_or_404(
        Appointment,
        pk=appointment_id,
        staff=staff
    )
    
    if request.method == 'POST':
        appointment.delete()
        messages.success(request, "Rendez-vous supprimé avec succès.")
        return redirect('staff:staff_dashboard')
    
    context = {
        'appointment': appointment,
        'staff': staff,
        'page_title': f"Confirmer Suppression",
    }
    
    return render(request, 'staff/appointment_delete.html', context)


# ✅ EMAIL UTILITIES


def _send_appointment_confirmation_email(appointment):
    """
    ✅ SECURITY: Send confirmation email to patient.
    
    Email includes:
    - Doctor name
    - Appointment date and time
    - Department/Service
    """
    
    if not appointment.patient or not appointment.patient.email:
        return False
    
    if not appointment.staff:
        return False
    
    try:
        # Prepare email context
        context = {
            'patient_name': appointment.patient.full_name,
            'doctor_name': appointment.staff.user.get_full_name(),
            'doctor_specialty': appointment.staff.specialty or 'Médecin',
            'appointment_date': appointment.date.strftime('%d/%m/%Y'),
            'appointment_time': appointment.time.strftime('%H:%M'),
            'department': appointment.staff.departement.name if appointment.staff.departement else 'N/A',
            'reason': appointment.raison or 'Consultation générale',
        }
        
        # Render email templates
        html_message = render_to_string('staff/email/appointment_confirmation.html', context)
        text_message = render_to_string('staff/email/appointment_confirmation.txt', context)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=f"Confirmation de votre rendez-vous - While Health",
            body=text_message,
            from_email='noreply@whilehealth.cd',
            to=[appointment.patient.email],
        )
        
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        
        return True
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending appointment confirmation email: {str(e)}")
        return False

