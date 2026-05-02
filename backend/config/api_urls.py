"""
Configuration des URLs de l'API REST.
Définit tous les endpoints de l'API versionnée.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# JWT Authentication
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# ViewSets de l'API
from patients.viewsets import PatientViewSet
from medecins.viewsets import SpecialiteViewSet, MedecinViewSet
from rendezvous.viewsets import RendezVousViewSet
from dossiers.viewsets import ConsultationViewSet, TraitementViewSet
from facturation.viewsets import FactureViewSet
from core.viewsets import UserViewSet

# Initialisation du routeur
router = DefaultRouter()

# Enregistrement des ViewSets
router.register(r'users', UserViewSet, basename='user')
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'specialites', SpecialiteViewSet, basename='specialite')
router.register(r'medecins', MedecinViewSet, basename='medecin')
router.register(r'rendezvous', RendezVousViewSet, basename='rendezvous')
router.register(r'consultations', ConsultationViewSet, basename='consultation')
router.register(r'traitements', TraitementViewSet, basename='traitement')
router.register(r'factures', FactureViewSet, basename='facture')

urlpatterns = [
    # ===========================================
    # AUTHENTIFICATION JWT
    # ===========================================
    # Obtenir un token (access + refresh)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Rafraîchir un token expiré
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Vérifier la validité d'un token
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # ===========================================
    # ENDPOINTS CRUD (via ViewSets)
    # ===========================================
    # Tous les endpoints CRUD sont générés automatiquement par le routeur
    # Exemples :
    #   GET    /api/patients/        -> Liste des patients
    #   POST   /api/patients/        -> Créer un patient
    #   GET    /api/patients/1/      -> Détail du patient 1
    #   PUT    /api/patients/1/      -> Modifier le patient 1
    #   PATCH  /api/patients/1/      -> Modifier partiellement
    #   DELETE /api/patients/1/      -> Supprimer le patient 1
    path('', include(router.urls)),
]