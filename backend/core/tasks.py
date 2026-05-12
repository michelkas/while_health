# ============================================
# While Health - Tâches Asynchrones Celery
# ============================================

import logging
from datetime import datetime, timedelta
from io import BytesIO

from celery import shared_task
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

# Conditional imports for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from weasyprint import HTML
    PDF_MODULES_AVAILABLE = True
except ImportError:
    PDF_MODULES_AVAILABLE = False

from config.settings import EMAIL_HOST_USER, EMAIL_DAILY_LIMIT
from patients.models import Patients, Consultation, Prescription
from staff.models import Staff

logger = logging.getLogger(__name__)

EMAIL_COUNT_CACHE_PREFIX = 'daily_email_count_'


def _get_email_limit_cache_key():
    today = timezone.now().date().strftime('%Y%m%d')
    return f"{EMAIL_COUNT_CACHE_PREFIX}{today}"


def _get_seconds_until_midnight():
    now = timezone.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((tomorrow - now).total_seconds())


def _get_daily_email_count():
    key = _get_email_limit_cache_key()
    count = cache.get(key)
    return int(count or 0)


def _increment_daily_email_count():
    key = _get_email_limit_cache_key()
    timeout = _get_seconds_until_midnight()
    added = cache.add(key, 1, timeout=timeout)
    if not added:
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=timeout)


def _can_send_email():
    return _get_daily_email_count() < EMAIL_DAILY_LIMIT


def _record_email_sent():
    _increment_daily_email_count()


@shared_task
def generate_patient_report_pdf(patient_id):
    """
    Génère un rapport PDF pour un patient (consultations, prescriptions)
    """
    if not PDF_MODULES_AVAILABLE:
        logger.warning("PDF modules not available, skipping PDF generation")
        return None

    try:
        patient = Patients.objects.select_related().get(pk=patient_id)

        # Récupérer données avec optimisation
        consultations = Consultation.objects.filter(
            patient=patient
        ).select_related('doctor__user').prefetch_related('prescriptions')

        context = {
            'patient': patient,
            'consultations': consultations,
            'generated_at': timezone.now(),
        }

        # Générer HTML puis PDF
        html_content = render_to_string('reports/patient_report.html', context)
        pdf_file = HTML(string=html_content).write_pdf()

        # Sauvegarder ou envoyer par email
        # ... logique de sauvegarde ...

        logger.info(f"PDF généré pour patient {patient}")
        return pdf_file

    except Exception as e:
        logger.error(f"Erreur génération PDF patient {patient_id}: {e}")
        raise


@shared_task
def send_appointment_reminder(appointment_id):
    """
    Envoie un rappel de rendez-vous par email/SMS
    """
    try:
        from appointment.models import Appointment
        appointment = Appointment.objects.select_related(
            'patient', 'staff__user'
        ).get(pk=appointment_id)

        if not _can_send_email():
            logger.warning(
                "Impossible d'envoyer le rappel RDV %s : limite journalière de %s emails atteinte.",
                appointment_id,
                EMAIL_DAILY_LIMIT,
            )
            return

        if appointment.patient.email:
            subject = f"Rappel RDV - {appointment.date}"
            message = render_to_string('emails/appointment_reminder.txt', {
                'appointment': appointment,
                'patient': appointment.patient,
                'doctor': appointment.staff.user.get_full_name(),
            })

            send_mail(
                subject=subject,
                message=message,
                from_email=EMAIL_HOST_USER,
                recipient_list=[appointment.patient.email],
                fail_silently=False,
            )
            _record_email_sent()

        logger.info(f"Rappel envoyé pour RDV {appointment_id}")

    except Exception as e:
        logger.error(f"Erreur envoi rappel RDV {appointment_id}: {e}")
        raise


@shared_task
def generate_monthly_statistics():
    """
    Génère les statistiques mensuelles (consultations, patients, etc.)
    """
    try:
        from django.db.models import Count, Q
        from datetime import datetime, timedelta

        today = timezone.now().date()
        first_day = today.replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Statistiques optimisées en une seule requête
        stats = Patients.objects.aggregate(
            new_patients=Count('id', filter=Q(registered_at__date__range=[first_day, last_day])),
            total_patients=Count('id'),
            transferred=Count('id', filter=Q(transfered=True)),
        )

        consultations_stats = Consultation.objects.filter(
            date_recorded__date__range=[first_day, last_day]
        ).aggregate(
            total=Count('id'),
            by_doctor=Count('doctor', distinct=True),
        )

        # Générer rapport
        context = {
            'stats': stats,
            'consultations': consultations_stats,
            'period': f"{first_day} - {last_day}",
        }

        # Sauvegarder ou envoyer
        logger.info(f"Statistiques mensuelles générées: {stats}")

        return stats

    except Exception as e:
        logger.error(f"Erreur génération stats mensuelles: {e}")
        raise


@shared_task
def bulk_import_patients(csv_data):
    """
    Import en masse des patients depuis CSV
    """
    try:
        from patients.forms import PatientsForm
        import csv
        from io import StringIO

        csv_reader = csv.DictReader(StringIO(csv_data))
        success_count = 0
        errors = []

        for row in csv_reader:
            form = PatientsForm(row)
            if form.is_valid():
                form.save()
                success_count += 1
            else:
                errors.append(f"Ligne {csv_reader.line_num}: {form.errors}")

        logger.info(f"Import terminé: {success_count} patients importés, {len(errors)} erreurs")

        return {
            'success_count': success_count,
            'errors': errors[:10],  # Limiter les erreurs affichées
        }

    except Exception as e:
        logger.error(f"Erreur import patients: {e}")
        raise


@shared_task
def send_appointment_confirmation_email(appointment_id):
    """
    Envoie un email de confirmation de rendez-vous au patient.
    Tâche asynchrone pour éviter le verrouillage de la base de données.
    """
    try:
        from appointment.models import Appointment
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings

        appointment = Appointment.objects.select_related(
            'patient', 'staff__user', 'staff__departement'
        ).get(pk=appointment_id)

        if not appointment.patient or not appointment.patient.email:
            logger.info(f"Pas d'email pour le patient du RDV {appointment_id}")
            return

        if not _can_send_email():
            logger.warning(
                "Impossible d'envoyer la confirmation RDV %s : limite journalière de %s emails atteinte.",
                appointment_id,
                EMAIL_DAILY_LIMIT,
            )
            return

        if not appointment.staff:
            logger.warning(f"Pas de staff assigné au RDV {appointment_id}")
            return

        # Préparer le contexte de l'email
        staff_title = "Dr." if appointment.staff.role in [Staff.Role.DOCTOR, Staff.Role.MEDECIN] else appointment.staff.get_role_display()
        patient_name = getattr(appointment.patient, 'full_name', f"{appointment.patient.first_name} {appointment.patient.last_name}")

        context = {
            'patient_name': patient_name,
            'staff_title': staff_title,
            'doctor_name': appointment.staff.user.get_full_name(),
            'doctor_specialty': (
                appointment.staff.get_specialty_display()
                if appointment.staff.specialty
                else appointment.staff.get_role_display()
            ),
            'appointment_date': appointment.date.strftime('%d/%m/%Y'),
            'appointment_time': appointment.time.strftime('%H:%M'),
            'department': appointment.staff.departement.name if appointment.staff.departement else 'N/A',
            'reason': appointment.raison or 'Consultation générale',
        }

        # Rendre les templates
        html_message = render_to_string('staff/email/appointment_confirmation.html', context)
        text_message = render_to_string('staff/email/appointment_confirmation.txt', context)

        # Créer et envoyer l'email
        email = EmailMultiAlternatives(
            subject="Confirmation de votre rendez-vous - While Health",
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[appointment.patient.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        _record_email_sent()

        logger.info(f"Email de confirmation envoyé pour RDV {appointment_id} à {appointment.patient.email}")

    except Exception as e:
        logger.error(f"Erreur envoi email confirmation RDV {appointment_id}: {e}")
        raise