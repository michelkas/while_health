from tabnanny import verbose

from django.db import models #type: ignore
from django.contrib.auth.models import AbstractUser #type: ignore
from phonenumber_field.modelfields import PhoneNumberField #type: ignore
from django.urls import reverse #type: ignore

class User(AbstractUser):
    phone = PhoneNumberField(blank=True, null=True, region='CD')
    avatar = models.ImageField(upload_to='avatar/', blank=True, null=True)
    bio = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateur'
    

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_absolute_url(self):
        return reverse('profile')
    
    def __str__(self):
        return self.get_full_name()
    

