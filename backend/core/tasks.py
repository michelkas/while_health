# ============================================
# While Health - Tâches Asynchrones Celery
# ============================================

import logging
from io import BytesIO

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from weasyprint import HTML

from config.settings import EMAIL_HOST_USER
from patients.models import Patients, Consultation, Prescription
from staff.models import Staff

logger = logging.getLogger(__name__)


@shared_task
def generate_patient_report_pdf(patient_id):
    """
    Génère un rapport PDF pour un patient (consultations, prescriptions)
    """
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