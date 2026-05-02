from django import forms  # type: ignore
from django.utils import timezone  # type: ignore

from appointment.forms import AppointmentForm
from appointment.models import Appointment
from staff.models import Staff  # type: ignore
from .models import Patients, TransferedPatient, VitalSign, MedicalHistory, Consultation, Prescription


class PatientsForm(forms.ModelForm):
    class Meta:
        model = Patients
        fields = '__all__'
        exclude = ('transfered', 'registered_at')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'type': 'email'}),
            'adress': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'tutor': forms.TextInput(attrs={'class': 'form-control'}),
            'tutor_contact': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel'}),
            'tutor_adress': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
        labels = {
            'name': 'Nom',
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'contact': 'Contact',
            'email': 'Email',
            'adress': 'Adresse',
            'sexe': 'Sexe',
            'tutor': 'Tuteur',
            'tutor_contact': 'Contact du tuteur',
            'tutor_adress': 'Adresse du tuteur',
        }

        help_texts = {
            'name': 'Nom du patient',
            'first_name': 'Prénom du patient',
            'last_name': 'Nom de famille du patient',
            'contact': 'Contact du patient',
            'email': 'Email du patient',
            'adress': 'Adresse du patient',
            'sexe': 'Sexe du patient',
            'tutor': 'Tuteur du patient',
            'tutor_contact': 'Contact du tuteur du patient',
            'tutor_adress': 'Adresse du tuteur du patient',
        }


class TransferedPatientForm(forms.ModelForm):
    class Meta:
        model = TransferedPatient
        fields = '__all__'
        
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'receiving_institution': forms.TextInput(attrs={'class': 'form-control'}),
        }

        labels = {
            'reason': 'Motif de transfert',
            'receiving_institution': 'Institution de réception',
        }

        help_texts = {
            'reason': 'Motif de transfert',
            'receiving_institution': 'Institution de réception',
        }


class VitalSignForm(forms.ModelForm):
    class Meta:
        model = VitalSign
        fields = '__all__'
        widgets = {
            'temperature': forms.NumberInput(attrs={'class': 'form-control'}),
            'heart_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'oxygen_saturation': forms.NumberInput(attrs={'class': 'form-control'}),
            'blood_pressure': forms.TextInput(attrs={'class': 'form-control'}),
            'pulse': forms.NumberInput(attrs={'class': 'form-control'}),
            'respiration_rate': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'temperature': 'Température',
            'heart_rate': 'Fréquence cardiaque',
            'oxygen_saturation': 'Saturation d\'oxygène',
            'blood_pressure': 'Pression artérielle',
            'pulse': 'Pouls',
            'respiration_rate': 'Fréquence respiratoire',
        }
        help_texts = {
            'temperature': 'Température',
            'heart_rate': 'Fréquence cardiaque',
            'oxygen_saturation': 'Saturation d\'oxygène',
            'blood_pressure': 'Pression artérielle',
            'pulse': 'Pouls',
            'respiration_rate': 'Fréquence respiratoire',
        }


class MedicalHistoryForm(forms.ModelForm):
    class Meta:
        model = MedicalHistory
        fields = '__all__'
        
        widgets = {
            'chronic_diseases': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'long_term_treatments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'lifestyle_habits': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'family_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        
        labels = {
            'chronic_diseases': 'Maladies chroniques',
            'allergies': 'Allergies',
            'long_term_treatments': 'Traitement long terme',
            'lifestyle_habits': 'Habitudes de vie',
            'family_history': 'Historique familial',
        }
        
        help_texts = {
            'chronic_diseases': 'Maladies chroniques',
            'allergies': 'Allergies',
            'long_term_treatments': 'Traitement long terme',
            'lifestyle_habits': 'Habitudes de vie',
            'family_history': 'Historique familial',
        }


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = '__all__'
        exclude = ['patient', 'doctor']
        
        widgets = {
            'reason_for_consultation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        
        labels = {
            'reason_for_consultation': 'Raison de la consultation',
            'diagnosis': 'Diagnostic',
        }
        
        help_texts = {
            'reason_for_consultation': 'Raison de la consultation',
            'diagnosis': 'Diagnostic',
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.doctor and self.request and self.request.user.is_authenticated:
            try:
                instance.doctor = self.request.user.staff_profile
            except Staff.DoesNotExist:
                pass
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = '__all__'
        
        widgets = {
            'medication_name': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'frequency': forms.TextInput(attrs={'class': 'form-control'}),
            'duration': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'medication_name': 'Nom du médicament',
            'dosage_value': 'Dosage',
            'frequency': 'Fréquence',
            'duration': 'Durée',
        }
        help_texts = {
            'medication_name': 'Nom du médicament',
            'dosage_value': 'Dosage en mg',
            'frequency': 'Fréquence',
            'duration': 'Durée',
        }


HystoryFormset = forms.inlineformset_factory(
    Patients,
    MedicalHistory,
    form=MedicalHistoryForm,
    extra=1,
    can_delete=False,
    max_num=1
)
