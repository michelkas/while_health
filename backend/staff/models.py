

from django.core.exceptions import ValidationError #type: ignore
from django.db import models #type: ignore
from django.utils import timezone #type: ignore
from django.utils.text import slugify #type: ignore
import uuid
from datetime import datetime

class Departement(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nom")
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='departements/', blank=True, null=True, verbose_name="Image")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_at = models.DateField(auto_now_add=True)
    

    class Meta:
        verbose_name = 'Departement'
        verbose_name_plural = 'Departements'

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{uuid.uuid4().hex[:6]}")
        super().save(*args, **kwargs)


class Staff(models.Model):
    """
    Modèle représentant un membre du personnel médical ou administratif.
    """
    class Role(models.TextChoices):
        DOCTOR = "DOCTOR", "Docteur",
        NURSE = "NURSE", "Infirmier",
        MEDECIN = "MEDECIN", "Medecin",
        ADMIN = "ADMIN", "Administrateur",
        LAB_TECH = "LAB_TECH", "Technicien de laboratoire",
        PHARMACIST = "PHARMACIST","Pharmacien",
        SECRETARY = "SECRETARY", "Secrtaire",
        
    class Specialty(models.TextChoices):
        CHIRURGIE = "CHIRURGIE", "Chirurgie",
        ANESTHESISTE = "ANESTHESISTE", "Anesthsiste",
        RADIOLOGUE = "RADIOLOGUE", "Radiologue",
        PEDIATRE = "PEDIATRE", "Pédiatre",
        GYNAECOLOGUE = "GYNAECOLOGUE", "Gynecologue",
        DENTISTE = "DENTISTE", "Dentiste",
        OPHTALMOLOGUE = "OPHTALMOLOGUE", "Ophtalmologue",
        ORTHOPEDISTE = "ORTHOPEDISTE", "Orthopediste",
        PATHOLOGUE = "PATHOLOGUE", "Pathologue",
        PSYCHIATRE = "PSYCHIATRE", "Psychiatre",
        THERAPEUTE = "THERAPEUTE", "Therapeute",
        



    user = models.OneToOneField('core.User', on_delete=models.CASCADE, related_name='staff_profile')
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nom")
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nom de famille")
    first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Prénom")
    specialty = models.CharField(max_length=100, choices=Specialty.choices, blank=True, null=True, verbose_name="Spécialité")
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Departement")
    slug = models.SlugField(unique=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEDECIN, verbose_name="Role") 
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    experience_years = models.PositiveIntegerField(default=0)
    twitter = models.URLField(max_length=255, blank=True, null=True)
    facebook = models.URLField(max_length=255, blank=True, null=True)
    instagram = models.URLField(max_length=255, blank=True, null=True)
    linkedin = models.URLField(max_length=255, blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)
    

    class Meta:
        verbose_name = 'Membre du personnel'
        verbose_name_plural = 'Membres du personnel'
        # ✅ PERFORMANCE: Database indexes
        indexes = [
            models.Index(fields=['is_active', 'is_verified']),
            models.Index(fields=['role']),
            models.Index(fields=['departement']),
            models.Index(fields=['specialty']),
            # ✅ PERFORMANCE: Composite index for active staff lookup
            models.Index(fields=['is_active', 'is_verified', 'role'], name='staff_active_role_idx'),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    def get_experiencie_years(self):
        if self.created_at.year != datetime.now().year:
            yrs = datetime.now().year - self.created_at.year 
            exp_yrs = self.experience_years + yrs
            return exp_yrs
        return self.experience_years
    
    
          

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.user.get_full_name()}-{uuid.uuid4().hex[:6]}")
        super().save(*args, **kwargs)
class TimeService(models.Model):
    """
    Modèle representant le temps de service du travailleur
    """
    DAY_OF_WEEK = (
        ('Lundi', 'Lundi'),
        ('Mardi', 'Mardi'),
        ('Mercredi', 'Mercredi'),
        ('Jeudi', 'Jeudi'),
        ('Vendredi', 'Vendredi'),
        ('Samedi', 'Samedi'),
        ('Dimanche', 'Dimanche'),
    )

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='time_service')
    service_day = models.CharField(verbose_name='Jours de service', choices=DAY_OF_WEEK, max_length=20)
    open_time = models.TimeField(verbose_name="Heure d'ouverture")
    close_time = models.TimeField(verbose_name="Heure de cloture")

    class Meta:
        verbose_name = "Temps de service"
        verbose_name_plural = "Temps de service"
        unique_together = ('staff', 'service_day')

    def clean(self):
        super().clean()

        if self.pk:
            return

        today_index = timezone.localdate().weekday()
        allowed_days = {day for day, _ in self.DAY_OF_WEEK[today_index + 1:]}

        if self.service_day and self.service_day not in allowed_days:
            raise ValidationError({
                'service_day': 'Vous ne pouvez planifier qu’un jour à venir.'
            })

    def __str__(self):
        return f"{self.staff.user.get_full_name()}  {self.service_day} : {self.open_time.strftime('%H:%M')} - {self.close_time.strftime('%H:%M')}"
