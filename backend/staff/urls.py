from django.urls import path

from . import views

app_name = 'staff'


urlpatterns = [
    # Public views
    path('departement/<int:departement_id>/', views.departement_detail, name='departement_detail'),
    path('staff/<int:staff_id>/', views.staff_profile_detail, name='staff_profile_detail'),
    
    # ✅ Staff profile (remplace l'ancien dashboard sur /staff/profile/)
    path('profile/', views.staff_profile_detail, name='profile'),

    path('appointment/<int:appointment_id>/validate/', views.staff_appointment_validate, name='staff_appointment_validate'),
    path('appointment/<int:appointment_id>/edit/', views.staff_appointment_edit, name='staff_appointment_edit'),
    path('appointment/<int:appointment_id>/delete/', views.staff_appointment_delete, name='staff_appointment_delete'),
]
