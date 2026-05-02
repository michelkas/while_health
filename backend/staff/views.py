from django.shortcuts import render, get_object_or_404
from .models import Departement, Staff
from data.models import Service


def departement_detail(request, departement_id):
    """
    Vue de détail pour un département.
    Affiche toutes les informations sur un département ainsi que les services et membres du personnel associés.
    """
    departement = get_object_or_404(Departement, pk=departement_id)
    services = Service.objects.filter(departement=departement)
    staff_members = Staff.objects.filter(departement=departement, is_active=True, is_verified=True)
    
    context = {
        "departement": departement,
        "services": services,
        "staff_members": staff_members,
        "page_title": f"{departement.name} - While Health",
    }
    return render(request, 'staff/departement_detail.html', context)


def staff_profile_detail(request, staff_id):
    """
    Vue de détail pour le profil d'un membre du personnel.
    Affiche toutes les informations sur un membre du personnel médical ou administratif.
    """
    staff = get_object_or_404(Staff, pk=staff_id)
    
    # Récupérer les services liés au département du staff
    related_services = []
    if staff.departement:
        related_services = Service.objects.filter(departement=staff.departement).exclude(
            title__icontains=staff.specialty or ""
        )[:4]
    
    context = {
        "staff": staff,
        "related_services": related_services,
        "page_title": f"Dr. {staff.user.get_full_name()} - While Health",
    }
    return render(request, 'staff/staff_profile_detail.html', context)

