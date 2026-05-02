from django.urls import path #type: ignore 
from . import views

app_name = 'patients'

urlpatterns = [
    path('appointment/', views.appointment, name='appointment'),
    path('patient-lookup/', views.patient_lookup, name='patient_lookup'),
    path('get-available-slots/', views.get_available_slots, name='get_available_slots'),
    path('patient-message/<int:pk>/', views.patient_message, name='patient_message'),
]
