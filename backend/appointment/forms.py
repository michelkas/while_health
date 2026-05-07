from django import forms #type: ignore
from .models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['time_service', 'date', 'time', 'raison', 'accept']
        
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', "class": "form-control"}),
            'time': forms.TimeInput(attrs={'type': 'time', "class": "form-control"}),
            'raison': forms.Textarea(attrs={'rows': 3, "class": "form-control", "placeholder": "Décrivez le motif de votre visite"}),
            'accept': forms.CheckboxInput(attrs={'type':'checkbox', "class":"form-check-input"})
        }
        
        labels={
            'date':"Date du rendez-vous",
            'time': "L'heure du rendez-vous",
            'raison': "Motif du rendez-vous",
            'accept': "Validez le rendez-vous",
        }
        
        help_texts = {
            'date':"Date du rendez-vous",
            'time': "L'heure du rendez-vous",
            'raison': "Décrivez brièvement le motif de votre visite",
            'accept': "Validez le rendez-vous",
        }