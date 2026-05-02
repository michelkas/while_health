from data.models import Contact, Service, About


def global_context(request):
    context= {
        "contact":Contact.objects.only('name', 'operation_days_time','phone', 'email', 'address', 'facebook', 'twitter', 'instagram', 'linkedin').first(),
        "services":Service.objects.only('title', 'departement', 'description', 'icon', 'short_description').all(),
        "about": About.objects.only('title', 'subtitle', 'goal', 'description').first()
        
    }
    return context