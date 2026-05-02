from django import forms #type: ignore
from .models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [ 'time_service', 'date', 'time', 'accept']
        
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', "class": "form-control"}),
            'time': forms.TimeInput(attrs={'type': 'time', "class": "form-control"}),
            'accept': forms.CheckboxInput(attrs={'type':'checkbox', "class":"form-control"})
        }
        
        labels={
            'date':"Date du rendez-vous",
            'time': "L'heure du rendez-vous",
            'accept': "Validez le rendez-vous",
        }
        
        help_texts = {
            'date':"Date du rendez-vous",
            'time': "L'heure du rendez-vous",
            'accept': "Validez le rendez-vous",
        }