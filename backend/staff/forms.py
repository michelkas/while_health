from django import forms #type: ignore
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Staff, TimeService


class TimeServiceForm(forms.ModelForm):
    class Meta:
        model = TimeService
        fields = ['staff', 'service_day', 'open_time', 'close_time']
        widgets = {
            'staff': forms.Select(attrs={'class': 'form-control'}),
            'service_day': forms.Select(attrs={'class': 'form-control'}),
            'open_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'close_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
        labels = {
            'staff': 'Staff',
            'service_day': 'Jour de service',
            'open_time': 'Heure d\'ouverture',
            'close_time': 'Heure de fermeture',
        }
        help_texts = {
            'staff': 'Staff',
            'service_day': 'Jour de service',
            'open_time': 'Heure d\'ouverture',
            'close_time': 'Heure de fermeture',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._restrict_service_day_choices()

    def _restrict_service_day_choices(self):
        service_day_field = self.fields.get('service_day')
        if not service_day_field:
            return

        original_choices = list(service_day_field.choices)
        today_index = timezone.localdate().weekday()
        allowed_days = {day for day, _ in TimeService.DAY_OF_WEEK[today_index:]}

        if self.instance and self.instance.pk:
            service_day_field.help_text = 'Vous pouvez modifier ce planning existant.'
            return

        filtered_choices = [
            choice for choice in original_choices
            if choice[0] == '' or choice[0] in allowed_days
        ]
        service_day_field.choices = filtered_choices
        service_day_field.help_text = 'Seuls les jours à partir d’aujourd’hui sont autorisés pour une nouvelle planification.'

    def clean(self):
        cleaned_data = super().clean()
        service_day = cleaned_data.get('service_day')

        if not service_day or (self.instance and self.instance.pk):
            return cleaned_data

        today_index = timezone.localdate().weekday()
        allowed_days = {day for day, _ in TimeService.DAY_OF_WEEK[today_index:]}
        if service_day not in allowed_days:
            raise ValidationError({
                'service_day': 'Vous ne pouvez planifier qu’à partir d’aujourd’hui.'
            })

        return cleaned_data


class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['user', 'specialty', 'role']
        widgets = {
            'specialty': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'specialty': 'Spécialité',
            'role': 'Rôle',
        }
        help_texts = {
            'specialty': 'Spécialité',
            'role': 'Rôle',
        }


# ✅ STAFF APPOINTMENT MANAGEMENT - Forms for dashboard


from appointment.models import Appointment


class StaffAppointmentValidationForm(forms.ModelForm):
    """
    Form for staff to validate/confirm appointments.
    Can modify date, time, reason and set accept status.
    """
    class Meta:
        model = Appointment
        fields = ['date', 'time', 'raison', 'accept']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),
            'time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
            }),
            'raison': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Motif du rendez-vous',
            }),
            'accept': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'date': 'Date du rendez-vous',
            'time': 'Heure du rendez-vous',
            'raison': 'Motif du rendez-vous',
            'accept': 'Accepter et confirmer ce rendez-vous',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date_val = cleaned_data.get('date')
        time_val = cleaned_data.get('time')
        
        if date_val and time_val and self.instance:
            # Check if the new time slot is available
            existing = Appointment.objects.filter(
                staff=self.instance.staff,
                date=date_val,
                time=time_val,
            ).exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    "Ce créneau horaire n'est pas disponible. Veuillez choisir un autre."
                )
        
        return cleaned_data


class StaffAppointmentEditForm(forms.ModelForm):
    """
    Form for staff to edit appointment details.
    """
    class Meta:
        model = Appointment
        fields = ['date', 'time', 'raison']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),
            'time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
            }),
            'raison': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Motif du rendez-vous',
            }),
        }
        labels = {
            'date': 'Date du rendez-vous',
            'time': 'Heure du rendez-vous',
            'raison': 'Motif du rendez-vous',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date_val = cleaned_data.get('date')
        time_val = cleaned_data.get('time')
        
        if date_val and time_val and self.instance:
            existing = Appointment.objects.filter(
                staff=self.instance.staff,
                date=date_val,
                time=time_val,
            ).exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    "Ce créneau horaire n'est pas disponible."
                )
        
        return cleaned_data
