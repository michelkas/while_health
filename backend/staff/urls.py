from django.urls import path

from . import views

app_name = 'staff'


urlpatterns = [
    path('departement/<int:departement_id>/', views.departement_detail, name='departement_detail'),
    path('staff/<int:staff_id>/', views.staff_profile_detail, name='staff_profile_detail'),
]
