from django.db.models.signals import post_save # type: ignore
from django.dispatch import receiver # type:ignore
from core.models import User
from .models import Staff
from django.utils import timezone # type:ignore

@receiver(post_save, sender=Staff)
def create_user_for_staff(sender, instance, created, **kwargs):
    if created :
        if not instance.user:
            base_username = f"{instance.name.lower()}.{instance.first_name.lower()}.{instance.last_name.lower()}"
            username = base_username
            counter = 1

            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            password = f"{instance.first_name.upper()}{timezone.now().year}"
            user = User.objects.create_user(
                username=username, 
                password=password,
                first_name=instance.first_name,
                last_name=instance.last_name,
                email=instance.email, 
                is_staff=False,
                is_active=True,
            )
            instance.user = user
            instance.save()