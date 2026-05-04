from django.urls import path  # type: ignore
from . import views

urlpatterns = [
    # path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("patient-lookup/", views.patient_lookup, name="patient_lookup"),
    path("available-slots/", views.get_available_slots, name="get_available_slots"),
#     path("dashboard/", views.dashboard, name="dashboard"),
#     path("dashboard/patients/", views.patient_list, name="dashboard_patients"),
#     path("dashboard/patients/new/", views.patient_create, name="dashboard_patient_create"),
#     path("dashboard/patients/<int:pk>/edit/", views.patient_update, name="dashboard_patient_update"),
#     path("dashboard/patients/<int:pk>/delete/", views.patient_delete, name="dashboard_patient_delete"),
]
