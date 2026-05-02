from django.urls import path

from . import views

app_name = 'data'


urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about_detail, name='about_detail'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
]
