"""
✅ MODÈLES PATIENTS OPTIMISÉS

Changements:
1. Suppression champ redondant 'name' (gardé first_name + last_name)
2. Ajout date_of_birth pour historique complet
3. Validation stricte sur unicité email/contact
4. Indexes sur recherche fréquente
5. Full_clean() forcé dans save()
6. Consultation -> Doctor (Staff) au lieu de User
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import F, Q


class Patients(models.Model):
    """Patient medical record"""
    
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('O', 'Autre'),
    ]
    
    # ✅ CORE INFO - Simplified from 3 fields to 2
    first_name = models.CharField("Prénom", max_length=100)
    last_name = models.CharField("Nom de famille", max_length=100)
    date_of_birth = models.DateField("Date de naissance", null=True, blank=True)
    
    # CONTACT & PERSONAL
    sexe = models.CharField("Sexe", max_length=1, choices=SEXE_CHOICES)
    contact = PhoneNumberField("Contact", region='CD', unique=True, db_index=True)
    email = models.EmailField("Email", unique=True, db_index=True)
    adress = models.CharField("Adresse", max_length=255)
    
    # TUTOR INFO
    tutor_name = models.CharField("Nom du tuteur", max_length=200, blank=True)
    tutor_contact = PhoneNumberField("Contact du tuteur", region='CD', null=True, blank=True)
    tutor_adress = models.CharField("Adresse du tuteur", max_length=255, blank=True)
    
    # STATUS
    transfered = models.BooleanField("Transféré", default=False, db_index=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = True
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        # ✅ DATABASE INDEXES pour performance
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['contact']),
            models.Index(fields=['email']),
            models.Index(fields=['date_of_birth']),
            models.Index(fields=['-registered_at']),
            models.Index(fields=['transfered']),
        ]
        permissions = [
            ("view_sensitive_data", "Can view patient sensitive data"),
            ("create_appointment", "Can create appointments"),
            ("manage_prescriptions", "Can manage prescriptions"),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        """Propriété pour accès unifié du nom complet"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate patient age from date_of_birth"""
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def clean(self):
        """✅ VALIDATION MÉTIER STRICTE"""
        # Vérifier unicité email (case-insensitive)
        if self.email:
            existing = Patients.objects.filter(
                email__iexact=self.email
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(f"Email '{self.email}' déjà enregistré")
        
        # Vérifier unicité téléphone
        if self.contact:
            existing = Patients.objects.filter(
                contact=self.contact
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(f"Téléphone '{self.contact}' déjà enregistré")
        
        # Valider date de naissance
        if self.date_of_birth:
            today = timezone.now().date()
            if self.date_of_birth > today:
                raise ValidationError("Date de naissance ne peut pas être dans le futur")
            
            age = today.year - self.date_of_birth.year
            if age > 150 or age < 0:
                raise ValidationError("Date de naissance invalide")
    
    def save(self, *args, **kwargs):
        """✅ FORCER VALIDATION AVANT SAVE"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def registered_date(self):
        """Format date for display"""
        if self.registered_at:
            return self.registered_at.strftime("%d/%m/%Y %H:%M")
        return "date inconnue"


class VitalSign(models.Model):
    """Signes vitaux du patient"""
    
    patient = models.ForeignKey(
        Patients,
        on_delete=models.CASCADE,
        related_name='vital_signs',
        null=True,
        db_index=True
    )
    
    # ✅ VITALS NUMÉRIQUES AVEC VALIDATION
    temperature = models.DecimalField(
        "Température (°C)",
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        validators=[MinValueValidator(35.0), MaxValueValidator(42.0)]
    )
    heart_rate = models.IntegerField(
        "Fréquence cardiaque (bpm)",
        blank=True,
        null=True,
        validators=[MinValueValidator(30), MaxValueValidator(200)]
    )
    oxygen_saturation = models.IntegerField(
        "Saturation en oxygène (%)",
        blank=True,
        null=True,
        validators=[MinValueValidator(70), MaxValueValidator(100)]
    )
    blood_pressure = models.CharField(
        "Tension artérielle (mmHg)",
        max_length=7,
        blank=True,
        null=True,
        help_text="Format: 120/80"
    )
    pulse = models.IntegerField(
        "Pouls (bpm)",
        blank=True,
        null=True,
        validators=[MinValueValidator(30), MaxValueValidator(200)]
    )
    respiration_rate = models.IntegerField(
        "Fréquence respiratoire (/min)",
        blank=True,
        null=True,
        validators=[MinValueValidator(8), MaxValueValidator(60)]
    )
    
    date_recorded = models.DateTimeField(auto_now_add=True, editable=True)
    recorded_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='vital_signs_recorded'
    )
    
    class Meta:
        managed = True
        verbose_name = 'Signe Vital'
        verbose_name_plural = 'Signes Vitaux'
        indexes = [
            models.Index(fields=['patient', '-date_recorded']),
        ]
        ordering = ['-date_recorded']
    
    def __str__(self):
        patient_name = getattr(self.patient, 'full_name', 'inconnu') if self.patient else 'inconnu'
        date = self.date_recorded.strftime('%d/%m/%Y') if self.date_recorded else 'date inconnue'
        return f"Signes Vitaux de {patient_name} le {date}"
    
    def recorded_date(self):
        if self.date_recorded:
            return self.date_recorded.strftime("%d/%m/%Y %H:%M")
        return "date inconnue"


class MedicalHistory(models.Model):
    """Antécédents médicaux du patient"""
    
    patient = models.ForeignKey(
        Patients,
        on_delete=models.CASCADE,
        related_name='medical_histories',
        null=True,
        db_index=True
    )
    
    chronic_diseases = models.TextField("Maladies Chroniques", blank=True, null=True)
    allergies = models.TextField("Allergies", blank=True, null=True)
    long_term_treatments = models.TextField("Traitements à Long Terme", blank=True, null=True)
    lifestyle_habits = models.TextField("Habitudes de Vie", blank=True, null=True)
    family_history = models.TextField("Historique familial", blank=True, null=True)
    
    date_recorded = models.DateTimeField(auto_now_add=True, editable=True)
    recorded_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='medical_histories_recorded'
    )
    
    class Meta:
        managed = True
        verbose_name = 'Antécédent Médical'
        verbose_name_plural = 'Antécédents Médicaux'
        indexes = [
            models.Index(fields=['patient', '-date_recorded']),
        ]
        ordering = ['-date_recorded']
    
    def __str__(self):
        patient_name = getattr(self.patient, 'full_name', 'inconnu') if self.patient else 'inconnu'
        date = self.date_recorded.strftime('%d/%m/%Y') if self.date_recorded else 'date inconnue'
        return f"Antécédents de {patient_name} le {date}"
    
    def recorded_date(self):
        if self.date_recorded:
            return self.date_recorded.strftime("%d/%m/%Y %H:%M")
        return "date inconnue"


class TransferedPatient(models.Model):
    """Patient transféré"""
    
    patient = models.OneToOneField(
        Patients,
        on_delete=models.CASCADE,
        related_name='transfer_info'
    )
    transfer_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField("Motif du Transfert", blank=True, null=True)
    receiving_institution = models.CharField(
        "Établissement Receveur",
        max_length=255,
        blank=True,
        null=True
    )
    
    class Meta:
        managed = True
        verbose_name = 'Patient Transféré'
        verbose_name_plural = 'Patients Transférés'
    
    def __str__(self):
        patient_name = getattr(self.patient, 'full_name', 'inconnu') if self.patient else 'inconnu'
        return f"Transfert de {patient_name}"


class Consultation(models.Model):
    """Consultation médicale"""
    
    patient = models.ForeignKey(
        Patients,
        on_delete=models.CASCADE,
        related_name='consultations',
        db_index=True
    )
    
    # ✅ DOCTOR au lieu de User (plus sûr)
    doctor = models.ForeignKey(
        'staff.Staff',
        on_delete=models.PROTECT,  # Pas de suppression
        related_name='consultations',
        limit_choices_to=Q(
            is_active=True,
            role__in=['MEDECIN', 'DOCTOR', 'NURSE']
        )
    )
    
    reason_for_consultation = models.TextField("Raison de la Consultation", null=True)
    diagnosis = models.TextField("Diagnostic", blank=True, null=True)
    treatment_plan = models.TextField("Plan de traitement", blank=True, null=True)
    notes = models.TextField("Notes", blank=True, null=True)
    
    date_recorded = models.DateTimeField(auto_now_add=True, editable=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = True
        verbose_name = 'Consultation'
        verbose_name_plural = 'Consultations'
        indexes = [
            models.Index(fields=['patient', '-date_recorded']),
            models.Index(fields=['doctor', '-date_recorded']),
        ]
        ordering = ['-date_recorded']
    
    def __str__(self):
        patient_name = getattr(self.patient, 'full_name', 'inconnu') if self.patient else 'inconnu'
        doctor_name = self.doctor.user.get_full_name() if self.doctor else 'inconnu'
        date = self.date_recorded.strftime('%d/%m/%Y') if self.date_recorded else 'date inconnue'
        return f"Consultation de {patient_name} par {doctor_name} le {date}"
    
    def clean(self):
        """✅ VALIDATION MÉTIER"""
        if self.doctor and not self.doctor.is_active:
            raise ValidationError("Le docteur n'est pas actif")
        
        if self.doctor and self.doctor.role not in ['MEDECIN', 'DOCTOR', 'NURSE']:
            raise ValidationError("Seul le personnel médical peut créer une consultation")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def consultation_date_formatted(self):
        if self.date_recorded:
            return self.date_recorded.strftime("%d/%m/%Y %H:%M")
        return "date inconnue"


class Prescription(models.Model):
    """Prescription médicale - avec validation stricte"""
    
    # ✅ CHOIX FERMÉS pour médicaments
    MEDICATION_CHOICES = [
        ('PARACETAMOL', 'Paracétamol (Doliprane)'),
        ('IBUPROFEN', 'Ibuprofène (Advil)'),
        ('AMOXICILLIN', 'Amoxicilline'),
        ('CIPROFLOXACIN', 'Ciprofloxacine'),
        ('INSULIN_RAPID', 'Insuline Rapide'),
        ('METFORMIN', 'Metformine'),
        ('ATORVASTATIN', 'Atorvastatine'),
        ('ASPIRIN', 'Aspirine'),
        ('LISINOPRIL', 'Lisinopril'),
        ('OMEPRAZOLE', 'Oméprazole'),
        ('ATORVASTATIN', 'Atorvastatine'),
        ('OTHER', 'Autre (préciser dans notes)'),
    ]
    
    # ✅ UNITÉS FERMÉES
    DOSAGE_UNITS = [
        ('MG', 'mg'),
        ('MCG', 'μg'),
        ('ML', 'mL'),
        ('IU', 'IU'),
        ('G', 'g'),
    ]
    
    # ✅ FRÉQUENCES PRÉDÉFINIES
    FREQUENCIES = [
        ('TWICE_DAILY', '2 fois par jour'),
        ('THRICE_DAILY', '3 fois par jour'),
        ('FOUR_DAILY', '4 fois par jour'),
        ('TWICE_WEEKLY', '2 fois par semaine'),
        ('ONCE_WEEKLY', '1 fois par semaine'),
        ('EVERY_12H', 'Toutes les 12h'),
        ('EVERY_8H', 'Toutes les 8h'),
        ('EVERY_6H', 'Toutes les 6h'),
        ('EVERY_4H', 'Toutes les 4h'),
        ('ON_DEMAND', 'À la demande'),
    ]
    
    # ✅ DURÉES PRÉDÉFINIES
    DURATIONS = [
        (1, '1 jour'),
        (3, '3 jours'),
        (5, '5 jours'),
        (7, '7 jours'),
        (10, '10 jours'),
        (14, '14 jours'),
        (21, '21 jours'),
        (30, '30 jours'),
        (60, '60 jours'),
        (90, '90 jours'),
        (180, '180 jours'),
        (365, '1 an'),
        (None, 'Illimitée'),
    ]
    
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        db_index=True
    )
    
    # ✅ MÉDICATION FERMÉE
    medication = models.CharField(
        "Médicament",
        max_length=50,
        choices=MEDICATION_CHOICES
    )
    
    # ✅ DOSAGE NUMÉRIQUE
    dosage_value = models.DecimalField(
        "Dosage (valeur)",
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(10000)]
    )
    
    dosage_unit = models.CharField("Unité", max_length=10, choices=DOSAGE_UNITS)
    
    frequency = models.CharField("Fréquence", max_length=50, choices=FREQUENCIES)
    
    # ✅ DURÉE FERMÉE
    duration_days = models.IntegerField(
        "Durée (jours)",
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(365)]
    )
    
    instructions = models.TextField(
        "Instructions spéciales",
        blank=True,
        null=True,
        help_text="Ex: 'Avec repas', 'Éviter alcool'"
    )
    
    date_recorded = models.DateTimeField(auto_now_add=True, editable=False)
    
    class Meta:
        managed = True
        verbose_name = 'Prescription'
        verbose_name_plural = 'Prescriptions'
        indexes = [
            models.Index(fields=['consultation', '-date_recorded']),
        ]
        ordering = ['-date_recorded']
    
    def clean(self):
        """✅ VALIDATION MÉTIER STRICTE"""
        # Vérifier cohérence fréquence/durée
        if self.frequency == 'ON_DEMAND' and self.duration_days:
            raise ValidationError("Durée inutile pour 'à la demande'")
        
        # Vérifier dosage raisonnable
        if self.dosage_value and self.medication:
            common_max_doses = {
                'PARACETAMOL': 1000,  # mg max per dose
                'IBUPROFEN': 800,
                'ASPIRIN': 500,
                'INSULIN_RAPID': 100,  # IU
            }
            
            max_dose = common_max_doses.get(self.medication)
            if max_dose and self.dosage_value > max_dose:
                raise ValidationError(
                    f"Dosage de {self.dosage_value} {self.dosage_unit} semble trop élevé "
                    f"pour {self.get_medication_display()}"
                )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return (f"{self.get_medication_display()} {self.dosage_value}"
                f"{self.get_dosage_unit_display()} x{self.get_frequency_display()}")
    
    def formatted_dosage(self):
        """Format sûr pour affichage"""
        return f"{self.dosage_value} {self.get_dosage_unit_display()}"
    
    def prescription_date_formatted(self):
        if self.date_recorded:
            return self.date_recorded.strftime("%d/%m/%Y %H:%M")
        return "date inconnue"
