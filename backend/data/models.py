from django.db import models #type: ignore
from staff.models import Departement

class Hero(models.Model):
    title = models.CharField(max_length=100, verbose_name='titre')
    subtitle = models.CharField(max_length=100, verbose_name='subtitle')
    description = models.TextField(verbose_name='description')
    image = models.ImageField(upload_to='hero/', verbose_name='image')
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'Hero'
        verbose_name_plural = 'Heros'
        
    # def save(self, *args, **kwargs):
    #     if not self.pk and Hero.objects.exists():
    #         raise Exception("une information existe déjà")
    #     return super().save(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

class About(models.Model):
    title = models.CharField(max_length=100, verbose_name='titre')
    subtitle = models.CharField(max_length=100, verbose_name='subtitle')
    year = models.DateField(verbose_name='Année de  creation')
    goal = models.TextField(verbose_name='Objectif')
    location = models.CharField(max_length=100, verbose_name='location')
    description = models.TextField(verbose_name='description', blank=True, null=True)
    compassionate_care = models.TextField(verbose_name='soin compassionnel', blank=True, null=True)
    care_quality = models.TextField(verbose_name='qualité de soin', blank=True, null=True)
    image = models.ImageField(upload_to='about/', verbose_name='image')
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'A propos'
        verbose_name_plural = 'A propos'

class Service(models.Model):
    title = models.CharField(max_length=100, verbose_name='titre')
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, verbose_name='departement', blank=True, null=True)
    description = models.TextField(verbose_name='description')
    icon = models.CharField(max_length=100, verbose_name='icone')
    short_description = models.TextField(verbose_name='description courte')
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    
    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
    
    def __str__(self):
        return self.title
    
    def get_short_description(self):
        return [
            line.strip() for line in self.short_description.split(',')
        ]

class EmergencyInfo(models.Model):
    title = models.CharField(max_length=100, verbose_name='titre')
    phone = models.CharField(max_length=100, verbose_name='phone')
    address = models.CharField(max_length=100, verbose_name='adresse')
    operation_time = models.TextField(verbose_name='heures et jours de travail')
    created_at = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'urgence info'
        verbose_name_plural = 'urgence info'
    
    def __str__(self):
        return self.title

class Emergency(models.Model):
    title = models.CharField(max_length=100, verbose_name='titre')
    description = models.TextField(verbose_name='description')
    phone = models.CharField(max_length=100, verbose_name='phone')
    created_at = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'urgence'
        verbose_name_plural = 'urgence'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

class Contact(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nom Hopital')
    operation_days_time = models.CharField(max_length=150,verbose_name="jours et heures de service" )
    phone = models.CharField(max_length=100, verbose_name='phone')
    email = models.CharField(max_length=100, verbose_name='email')
    address = models.CharField(max_length=100, verbose_name='adresse')
    facebook = models.URLField(verbose_name="Lien facebook", null=True, blank=True)
    twitter = models.URLField(verbose_name="Lien x(twitter)", null=True, blank=True)
    instagram = models.URLField(verbose_name="Lien instagram", null=True, blank=True)
    linkedin = models.URLField(verbose_name="lien linkedin", null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'contact'
        verbose_name_plural = 'contact'
    
    def __str__(self):
        return self.phone
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)