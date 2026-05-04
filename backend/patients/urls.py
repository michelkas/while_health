from django.urls import path #type: ignore 
from . import views

app_name = 'patients'

urlpatterns = [
    path('appointment/', views.appointment, name='appointment'),
    
    path('patient-message/<int:pk>/', views.patient_message, name='patient_message'),
]
