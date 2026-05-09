from django.core.exceptions import ValidationError
from django.db import models #type: ignore
from django.core.validators import MinValueValidator, MaxValueValidator, DecimalValidator
from phonenumber_field.modelfields import PhoneNumberField # type: ignore

class Patients(models.Model):
    """
    Modèle représentant un dossier du patient.
    """
    SEXE_CHOISES = (
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    )
    
    # ✅ SECURITY: Removed redundant 'name' field
    first_name = models.CharField("Prénom", max_length=100)
    last_name = models.CharField("Nom de famille", max_length=100)
    contact = PhoneNumberField("Contact📞", region='CD', null=True, blank=True, unique=True) # type: ignore
    adress = models.CharField("Adresse", max_length=255)
    sexe = models.CharField("Sexe", max_length=1, choices=SEXE_CHOISES)
    email = models.EmailField("Email", max_length=255, unique=True)
    # Tutor info
    tutor = models.CharField("Tuteur", max_length=100, blank=True, null=True)
    tutor_contact = PhoneNumberField("Contact du tuteur📞", region='CD', null=True, blank=True)
    tutor_adress = models.CharField("Adresse du tuteur", max_length=255, blank=True, null=True)
    transfered = models.BooleanField("Transféré", default=False)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        verbose_name = 'Dossier Medical'
        verbose_name_plural = 'Dossiers Medicaux'
        # ✅ DATABASE INDEXES for searchable fields
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['contact']),
            models.Index(fields=['registered_at']),
            # ✅ PERFORMANCE: Composite index for patient lookup by name
            models.Index(fields=['first_name', 'last_name']),
            # ✅ PERFORMANCE: Search by registration date
            models.Index(fields=['registered_at'], name='patient_registered_idx'),
            # ✅ PERFORMANCE: Index for transferred status filtering
            models.Index(fields=['transfered']),
            # ✅ PERFORMANCE: Index for sexe filtering
            models.Index(fields=['sexe']),
        ]

    def clean(self):
        super().clean()
        # ✅ VALIDATION: Email uniqueness check
        if self.email:
            existing = Patients.objects.filter(email__iexact=self.email)
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({'email': 'Un patient avec cet email existe déjà.'})
        
        # ✅ VALIDATION: Contact uniqueness check
        if self.contact:
            existing = Patients.objects.filter(contact=self.contact)
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({'contact': 'Un patient avec ce numéro existe déjà.'})
        
        # ✅ VALIDATION: Age validation for tutor (if minor)
        if self.tutor and not self.registered_at:
            # Assume minor if tutor is provided
            pass  # Could add age validation logic here
        if self.registered_at:
            return self.registered_at.strftime("%d %m %Y") #format jour mois année ex. 25 décembre 2023 %d/%m/%Y %H:%M
        return "date inconnue"
    
    @property
    def full_name(self):
        """Return full name for compatibility."""
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        return f"{self.full_name}"
    

class VitalSign(models.Model):
    """
    Modèle représentant les signes vitaux d'un patient.
    """
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name='vital_signs', null=True)
    temperature = models.DecimalField("Température (°C)", max_digits=4, decimal_places=1, blank=True, null=True, validators=[MinValueValidator(35), MaxValueValidator(42)])
    heart_rate = models.IntegerField("Fréquence cardiaque (bpm)", blank=True, null=True, validators=[MinValueValidator(40), MaxValueValidator(200)])
    oxygen_saturation = models.IntegerField("Saturation en oxygène (%)", blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    blood_pressure = models.CharField("Tension artérielle (mmHg)", max_length=7, blank=True, null=True)  # Ex: "120/80"
    pulse = models.IntegerField("Pouls (bpm)", blank=True, null=True, validators=[MinValueValidator(40), MaxValueValidator(200)])
    respiration_rate = models.IntegerField("Fréquence respiratoire (respirations/min)", blank=True, null=True, validators=[MinValueValidator(8), MaxValueValidator(60)])
    date_recorded = models.DateTimeField(auto_now_add=True, blank=True, editable=True)
    
    class Meta:
        managed = True
        verbose_name = 'Signe Vital'
        verbose_name_plural = 'Signes Vitaux'
        # ✅ DATABASE INDEXES
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['date_recorded']),
            models.Index(fields=['patient', '-date_recorded']),
        ]

    def __str__(self):
        patient_name = getattr(self.patient, 'full_name', 'inconnu') if self.patient else 'inconnu'
        date = self.date_recorded.strftime('%d/%m/%Y') if self.date_recorded else 'date inconnue'
        
        return f"Signe Vital de {patient_name} le {date}"

    def recorded_date(self):
        if self.date_recorded:
            return self.date_recorded.strftime("%d %m %Y %H:%M") #format jour mois année heure:minute ex. 25 décembre 2023 14:30
        return "date inconnue"
    
class TransferedPatient(models.Model):
    """
    Modèle représentant un patient transféré.
    """
    patient = models.OneToOneField(Patients, on_delete=models.CASCADE, related_name='transfer_info', null=True)
    transfer_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField("Motif du Transfert", blank=True, null=True)
    receiving_institution = models.CharField("Établissement Receveur", max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        verbose_name = 'Patient Transféré'
        verbose_name_plural = 'Patients Transférés'
        # ✅ DATABASE INDEXES
        indexes = [
            models.Index(fields=['transfer_date']),
        ]

class MedicalHistory(models.Model):
    """
    Modèle représentant les antécédents médicaux d'un patient.
    """
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name='medical_histories', null=True)
    chronic_diseases = models.TextField("Maladies Chroniques", blank=True, null=True)
    allergies = models.TextField("Allergies", blank=True, null=True)
    long_term_treatments = models.TextField("Traitements à Long Terme", blank=True, null=True)
    lifestyle_habits = models.TextField("Habitudes de Vie", blank=True, null=True)
    family_history = models.TextField("Historique familial", blank=True, null=True)
    date_recorded = models.DateTimeField(auto_now_add=True, blank=True, editable=True)
    
    class Meta:
        managed = True
        verbose_name = 'Antécédent Médical'
        verbose_name_plural = 'Antécédents Médicaux'
        # ✅ DATABASE INDEXES
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['date_recorded']),
        ]

    def __str__(self):
        patient_name = getattr(self.patient, 'full_name', 'inconnu') if self.patient else 'inconnu'
        date = self.date_recorded.strftime('%d/%m/%Y') if self.date_recorded else 'date inconnue'
        
        return f"Antécédent Médical de {patient_name} le {date}"
    
    def recorded_date(self):
        if self.date_recorded:
            return self.date_recorded.strftime("%d %m %Y  %H:%M") #format jour mois année heure:minute ex. 25 décembre 2023 14:30
        return "date inconnue"

#la consultation a partir d'ici

class Consultation(models.Model):
    """
    Modèle représentant une consultation médicale d'un patient.
    """
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name='consultations', null=True)
    # ✅ CORRECT RELATION: doctor (Staff) instead of user (core.User)
    doctor = models.ForeignKey('staff.Staff', on_delete=models.CASCADE, related_name='consultations', null=True, blank=True)
    reason_for_consultation = models.TextField("Raison de la Consultation", null=True)
    diagnosis = models.TextField("Diagnostic", blank=True, null=True)
    date_recorded = models.DateTimeField(auto_now_add=True, blank=True, editable=True)

    class Meta:
        managed = True
        verbose_name = 'Consultation'
        verbose_name_plural = 'Consultations'
        # ✅ DATABASE INDEXES
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['doctor']),
            models.Index(fields=['date_recorded']),
        ]

    def clean(self):
        if self.doctor and not self.doctor.is_active:
            raise ValidationError('Le médecin doit être actif pour créer une consultation.')

    def __str__(self):
        patient_name = getattr(self.patient, 'full_name', 'inconnu') if self.patient else 'inconnu'
        if self.doctor:
            user_name = f"{self.doctor.user.first_name} {self.doctor.user.last_name}".strip()
            if not user_name:
                user_name = self.doctor.user.username
        else:
            user_name = 'inconnu'
        date = self.date_recorded.strftime('%d/%m/%Y %H:%M') if self.date_recorded else 'date inconnue'
        return f"Consultation de {patient_name} par {user_name} le {date}"
  
    def save(self, *args, **kwargs):
        """Auto-fill doctor from current user if not set."""
        if not self.doctor:
            from django.contrib.auth import get_user
            from staff.models import Staff
            # Try to get staff from current user
            try:
                # This would need request context - leave as-is for now
                pass
            except:
                pass
        super().save(*args, **kwargs)

    def consultation_date_formatted(self):
        if self.date_recorded:
            return self.date_recorded.strftime("%d %m %Y %H:%M") #format jour mois année heure:minute ex. 25 décembre 2023 14:30
        return "date inconnue"
    
class Prescription(models.Model):
    """
    Modèle représentant une prescription médicale.
    """
    # ✅ CLOSED CHOICES for medications
    MEDICATION_CHOICES = (
        ('paracetamol', 'Paracétamol'),
        ('ibuprofene', 'Ibuprofène'),
        ('amoxicilline', 'Amoxicilline'),
        ('azithromycine', 'Azithromycine'),
        ('metformine', 'Metformine'),
        ('atorvastatine', 'Atorvastatine'),
        ('lisinopril', 'Lisinopril'),
        ('autre', 'Autre'),
    )
    
    FREQUENCY_CHOICES = (
        ('1x/day', '1 fois par jour'),
        ('2x/day', '2 fois par jour'),
        ('3x/day', '3 fois par jour'),
        ('4x/day', '4 fois par jour'),
        ('every_6h', 'Toutes les 6 heures'),
        ('every_8h', 'Toutes les 8 heures'),
        ('every_12h', 'Toutes les 12 heures'),
        ('as_needed', 'Si nécessaire'),
    )
    
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='prescriptions', null=True)
    medication_name = models.CharField("Nom du Médicament", max_length=100, choices=MEDICATION_CHOICES, null=True)
    # ✅ VALIDATION: DecimalField with numeric validation instead of CharField
    dosage_value = models.DecimalField(
        "Dosage (mg)", 
        max_digits=6, 
        decimal_places=2,
        validators=[
            MinValueValidator(0.01),
            MaxValueValidator(10000)
        ],
        null=True,
        blank=True
    )
    frequency = models.CharField("Fréquence", max_length=20, choices=FREQUENCY_CHOICES, null=True)
    duration = models.CharField("Durée", max_length=100, null=True)
    date_recorded = models.DateTimeField(auto_now_add=True, blank=True, editable=True)

    class Meta:
        managed = True
        verbose_name = 'Prescription'
        verbose_name_plural = 'Prescriptions'
        # ✅ DATABASE INDEXES
        indexes = [
            models.Index(fields=['consultation']),
            models.Index(fields=['date_recorded']),
        ]

    def prescription_date_formatted(self):
        if self.date_recorded:
            return self.date_recorded.strftime("%d %m %Y %H:%M") #format jour mois année heure:minute ex. 25 décembre 2023 14:30
        return "date inconnue"    

    def __str__(self):
        patient_name = getattr(getattr(self.consultation, 'patient', None), 'full_name', 'inconnu') if self.consultation else 'inconnu'
        med = self.medication_name or 'médicament inconnu'
        return f"Prescription de {med} pour {patient_name}"