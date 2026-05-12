import logging
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from kombu.exceptions import OperationalError
from .models import Appointment
from core.tasks import send_appointment_confirmation_email  # Use Celery task instead of direct function

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Appointment)
def track_original_accept_value(sender, instance, **kwargs):
    """
    Track the original value of 'accept' field before saving.
    """
    if instance.pk:
        try:
            original = Appointment.objects.get(pk=instance.pk)
            instance._original_accept = original.accept
        except Appointment.DoesNotExist:
            instance._original_accept = False
    else:
        instance._original_accept = False


@receiver(post_save, sender=Appointment)
def send_appointment_confirmation_email_on_accept(sender, instance, created, **kwargs):
    """
    Signal to send confirmation email when appointment is accepted by admin.
    Only sends email when 'accept' field changes from False to True.
    Uses Celery task to avoid database locking issues.
    """
    if created:
        # Don't send email for new appointments
        return

    # Check if 'accept' was changed from False to True
    if hasattr(instance, '_original_accept') and not instance._original_accept and instance.accept:
        try:
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                send_appointment_confirmation_email.apply(args=(instance.pk,))
            else:
                send_appointment_confirmation_email.delay(instance.pk)
        except (OperationalError, ConnectionError) as exc:
            logger.warning(
                "Celery broker unavailable, sending appointment confirmation synchronously: %s",
                exc,
            )
            send_appointment_confirmation_email.apply(args=(instance.pk,))