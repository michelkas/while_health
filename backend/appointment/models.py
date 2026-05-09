from django.core.exceptions import ValidationError  # type: ignore
from django.db import models  # type: ignore

from patients.models import Patients
from staff.models import Staff, TimeService

FRENCH_WEEKDAYS = (
    "Lundi",
    "Mardi",
    "Mercredi",
    "Jeudi",
    "Vendredi",
    "Samedi",
    "Dimanche",
)


def get_french_weekday(date_value):
    if not date_value:
        return None
    weekday_index = date_value.weekday()
    if 0 <= weekday_index < len(FRENCH_WEEKDAYS):
        return FRENCH_WEEKDAYS[weekday_index]
    return None


class Appointment(models.Model):
    """
    Modèle representant un rendez-vous
    """

    patient = models.ForeignKey(
        Patients,
        on_delete=models.CASCADE,
        related_name="appointments",
        null=True,
        blank=True,
    )
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="appointments",
        null=True,
        blank=True,
    )
    time_service = models.ForeignKey(
        TimeService,
        on_delete=models.CASCADE,
        related_name="appointments",
        null=True,
        blank=True,
    )
    date = models.DateField()
    time = models.TimeField()
    raison = models.TextField(
        verbose_name="Motif du rendez-vous",
        blank=True,
        null=True,
        help_text="Raison ou motif de la consultation"
    )
    accept = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        # ✅ PERFORMANCE: Database indexes for appointment queries
        indexes = [
            models.Index(fields=['staff', 'date', 'time']),
            models.Index(fields=['patient', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['staff', 'accept']),
            models.Index(fields=['created_at']),
            # ✅ PERFORMANCE: Composite index for time slot conflicts
            models.Index(fields=['staff', 'date', 'time'], name='appointment_slot_idx'),
        ]

    def __str__(self):
        return f"{self.patient.first_name}"
    def clean(self):
        if self.time_service and self.staff and self.time_service.staff != self.staff:
            raise ValidationError("Le personnel ne correspond pas au temps de service")

        if self.time_service and self.date and self.time:
            day_name = get_french_weekday(self.date)
            if day_name and day_name != self.time_service.service_day:
                raise ValidationError("Le jour ne correspond pas au planning du personnel")

            if not (self.time_service.open_time <= self.time <= self.time_service.close_time):
                raise ValidationError("Heure hors Plage")

        if self.staff and self.date and self.time:
            existing_appointments = Appointment.objects.filter(
                staff=self.staff,
                date=self.date,
                time=self.time,
            )
            if self.pk:
                existing_appointments = existing_appointments.exclude(pk=self.pk)

            if existing_appointments.exists():
                raise ValidationError("Ce rendez-vous est deja pris")

    def save(self, *args, **kwargs):
        if not self.time_service:
            if not (self.staff and self.date and self.time):
                raise ValidationError(
                    "Le médecin, la date et l'heure sont requis pour déterminer le temps de service"
                )

            date_name = get_french_weekday(self.date)
            if not date_name:
                raise ValidationError("Date de rendez-vous invalide")

            try:
                self.time_service = TimeService.objects.get(
                    staff=self.staff,
                    service_day=date_name,
                    open_time__lte=self.time,
                    close_time__gte=self.time,
                )
            except TimeService.DoesNotExist:
                raise ValidationError("Aucun temps de service disponible pour ce jour et Heure")

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        patient_name = self.patient.full_name if self.patient else "patient inconnu"
        doctor_name = (
            self.staff.user.get_full_name()
            if self.staff and self.staff.user
            else "médecin inconnu"
        )
        return f"{patient_name} {doctor_name} - {self.date} - {self.time}"
