from django.urls import path

from . import views

app_name = 'data'


urlpatterns = [
    path('', views.index, name='index'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
]
