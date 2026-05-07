from django.urls import path #type: ignore 
from . import views

app_name = 'patients'

urlpatterns = [
    # Existing URLs
    path('appointment/', views.appointment, name='appointment'),
    path('patient-message/<int:pk>/', views.patient_message, name='patient_message'),
    
    # ✅ NEW: Patient phone access (no authentication required)
    path('verify-phone/', views.patient_phone_verification, name='patient_phone_verification'),
    path('my-appointments/', views.patient_appointments_list, name='patient_appointments_list'),
    path('appointment/<int:appointment_id>/edit/', views.patient_appointment_edit, name='patient_appointment_edit'),
    path('appointment/<int:appointment_id>/delete/', views.patient_appointment_delete, name='patient_appointment_delete'),
]
