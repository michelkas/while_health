"""
Configuration des URLs principales du projet de gestion hospitalière.
Inclut les URLs de l'interface web, de l'API REST et de la documentation.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

# Documentation API (drf-spectacular)


urlpatterns = [
    # ===========================================
    # ADMIN DJANGO
    # ===========================================
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('patients.urls')),
    path('', include('data.urls')),
    path('', include('staff.urls')),
   
]

# ===========================================
# FICHIERS STATIQUES ET MÉDIAS
# ===========================================
# En production, le serveur (nginx/apache) doit servir /media depuis MEDIA_ROOT.
# En local/dev, Django peut aussi le servir.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)



